"""
Read-along player. Shows the passage and lights up each word while it is spoken.

Two sources of voice:
  * audio_b64 given  -> plays the Bhashini voice; word highlighting is timed across the audio
  * audio_b64 empty  -> uses the device's own voice (browser speech synthesis); uses real word
                        events when the voice sends them, otherwise an estimated timer

Highlighting is approximate. The child still reads from the colour-coded passage after this.
"""

import json
import math
from html import escape

_JS = """
(function(){
const P=__PARAMS__;
const spans=[].slice.call(document.querySelectorAll('.w'));
const playBtn=document.getElementById('play'),slowBtn=document.getElementById('slow'),msg=document.getElementById('msg');
let slow=false,timer=null;
const wts=P.words.map(w=>w.length+1),tot=wts.reduce((a,b)=>a+b,0);
function hl(i){spans.forEach((s,k)=>{s.classList.toggle('on',k===i);s.classList.toggle('done',k<i);});}
function allDone(){spans.forEach(s=>{s.classList.remove('on');s.classList.add('done');});}
function clearAll(){spans.forEach(s=>s.classList.remove('on','done'));}
function idxAtFrac(f){let c=0;for(let i=0;i<wts.length;i++){c+=wts[i];if(f*tot<=c)return i;}return wts.length-1;}
slowBtn.onclick=()=>{slow=!slow;slowBtn.classList.toggle('act',slow);slowBtn.textContent=slow?'🐢 Slow: on':'🐢 Slow';};

if(P.audio){
  const a=new Audio('data:audio/wav;base64,'+P.audio);
  playBtn.onclick=()=>{clearAll();a.playbackRate=slow?0.8:1;a.currentTime=0;a.play();};
  a.ontimeupdate=()=>{if(a.duration)hl(idxAtFrac(a.currentTime/a.duration));};
  a.onended=allDone;
  msg.textContent='Bhashini voice';
}else{
  const synth=window.speechSynthesis;
  if(!synth){playBtn.disabled=true;msg.textContent='This browser cannot speak. Try Chrome.';return;}
  const starts=[];let pos=0;
  P.words.forEach(w=>{const i=P.text.indexOf(w,pos);starts.push(i<0?pos:i);pos=(i<0?pos:i)+w.length;});
  function wordAt(ch){let k=0;for(let i=0;i<starts.length;i++){if(starts[i]<=ch)k=i;}return k;}
  function voiceFor(l){const vs=synth.getVoices();const n=l.replace('_','-');
    return vs.find(v=>v.lang.replace('_','-')===n)||vs.find(v=>v.lang.toLowerCase().indexOf(n.split('-')[0].toLowerCase())===0);}
  playBtn.onclick=()=>{
    synth.cancel();clearInterval(timer);clearAll();
    const u=new SpeechSynthesisUtterance(P.text);u.lang=P.lang;
    const v=voiceFor(P.lang);
    if(v){u.voice=v;msg.textContent='Device voice: '+v.name;}
    else{msg.textContent='No voice for this language on this device. Use the Bhashini voice instead.';}
    u.rate=slow?0.7:0.95;
    let gotBoundary=false,t0=0;
    u.onstart=()=>{t0=Date.now();
      setTimeout(()=>{if(gotBoundary)return;
        const cps=13*u.rate;
        timer=setInterval(()=>{const ch=((Date.now()-t0)/1000)*cps;hl(wordAt(Math.min(ch,P.text.length-1)));},120);},1200);};
    u.onboundary=e=>{if(e.name&&e.name!=='word')return;gotBoundary=true;hl(wordAt(e.charIndex));};
    u.onend=()=>{clearInterval(timer);allDone();};
    u.onerror=()=>{clearInterval(timer);};
    synth.speak(u);
  };
}
})();
"""


def listen_html(words, text, audio_b64, lang_sr):
    span = " ".join(f'<span class="w">{escape(w)}</span>' for w in words)
    params = json.dumps({"words": words, "text": text, "audio": audio_b64 or "", "lang": lang_sr},
                        ensure_ascii=False).replace("</", "<\\/")
    js = _JS.replace("__PARAMS__", params)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700&display=swap');
html,body{{margin:0;font-family:'Baloo 2','Noto Sans Devanagari','Noto Sans Tamil','Noto Sans Telugu','Noto Sans Bengali','Noto Sans Gujarati',sans-serif;background:transparent}}
.box{{background:#FFFDF5;border:2px dashed #F0A227;border-radius:18px;padding:18px 22px;font-size:1.5rem;line-height:2.1;color:#6B7570}}
.w{{padding:1px 5px;border-radius:8px;transition:all .12s}}
.w.on{{background:#FFD54A;color:#3B1C57;transform:scale(1.08);display:inline-block;box-shadow:0 2px 8px rgba(0,0,0,.18)}}
.w.done{{color:#7B4397}}
.bar{{display:flex;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap}}
button{{font-family:inherit;font-weight:700;font-size:1.05rem;border:0;border-radius:999px;padding:9px 22px;cursor:pointer;color:#fff;
  background:linear-gradient(120deg,#F7971E,#FF5F6D);box-shadow:0 4px 12px rgba(255,95,109,.35)}}
button#slow{{background:#EFE6F7;color:#5B2F7A;box-shadow:none}} button#slow.act{{background:#7B4397;color:#fff}}
button:disabled{{opacity:.5;cursor:not-allowed}}
#msg{{font-size:.85rem;color:#6B6F73;font-weight:600;font-family:system-ui,sans-serif}}
</style></head><body>
<div class="box">{span}</div>
<div class="bar"><button id="play">🔊 Listen</button><button id="slow">🐢 Slow</button><span id="msg"></span></div>
<script>{js}</script></body></html>"""


def frame_height(text: str) -> int:
    return 150 + 36 * math.ceil(len(text) / 48)
