"""
Three.js scenes, embedded with st.components.v1.html.

Every scene degrades gracefully: if the three.js CDN cannot load (no internet),
the gradient background and text still show.
"""

import json

CDN = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"

_BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&display=swap');
html,body{margin:0;height:100%;overflow:hidden;font-family:'Baloo 2',system-ui,sans-serif;}
#c{position:absolute;inset:0;}
canvas{display:block;}
"""

_TEX = """
function tex(txt,size,color,font){
  const c=document.createElement('canvas');c.width=c.height=256;const g=c.getContext('2d');
  g.font='700 '+size+'px '+(font||'"Baloo 2","Noto Sans Devanagari","Noto Sans Tamil","Noto Sans Telugu","Noto Sans Bengali","Noto Sans Gujarati",sans-serif');
  g.textAlign='center';g.textBaseline='middle';
  g.shadowColor='rgba(0,0,0,.35)';g.shadowBlur=14;g.fillStyle=color;g.fillText(txt,128,134);
  return new THREE.CanvasTexture(c);
}
"""


def _page(css, body, js, params=None):
    js = js.replace("__PARAMS__", json.dumps(params or {}, ensure_ascii=False))
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{_BASE_CSS}{css}</style></head>'
            f'<body>{body}<script src="{CDN}"></script><script>{_TEX}{js}</script></body></html>')


# --------------------------------------------------------------------------- HERO
_HERO_JS = """
(function(){
if(!window.THREE){return;}
const el=document.getElementById('c');let W=el.clientWidth,H=el.clientHeight;
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(48,W/H,0.1,100);cam.position.set(0,0,10);
const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setSize(W,H);
el.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff,0.85));
const dl=new THREE.DirectionalLight(0xffffff,0.9);dl.position.set(3,5,6);scene.add(dl);

const cols=['#ffffff','#FFE9A8','#FFD1DC','#E4D4FF'];
const items=[['अ',150],['आ',150],['அ',150],['ஆ',150],['అ',150],['ఆ',150],['অ',150],['আ',150],
 ['અ',150],['આ',150],['A',150],['B',150],['क',150],['पढ़',105],['படி',105],['చదువు',80],
 ['পড়ো',100],['વાંચો',80],['Read',95],['ka',120]];
const sprites=[];
items.forEach((it,i)=>{
  const m=new THREE.SpriteMaterial({map:tex(it[0],it[1],cols[i%cols.length]),transparent:true,opacity:.95});
  const s=new THREE.Sprite(m);const sc=1.6+Math.random()*1.3;s.scale.set(sc,sc,1);
  s.userData={a:Math.random()*Math.PI*2,r:1.2+Math.random()*3.6,y:(Math.random()-.5)*5,sp:.07+Math.random()*.16,ph:Math.random()*6};
  scene.add(s);sprites.push(s);
});

const book=new THREE.Group();
const cover=new THREE.Mesh(new THREE.BoxGeometry(4.6,.12,3.2),new THREE.MeshStandardMaterial({color:0x4a2a7a}));
cover.position.y=-.1;book.add(cover);
function page(sign){
  const p=new THREE.Mesh(new THREE.BoxGeometry(2.2,.07,3),new THREE.MeshStandardMaterial({color:0xfff8e8}));
  p.position.set(sign*1.12,.1,0);p.rotation.z=-sign*0.18;return p;}
book.add(page(-1));book.add(page(1));
book.rotation.x=.6;book.position.set(8,-.3,2.5);scene.add(book);

const N=420,pos=new Float32Array(N*3);
for(let i=0;i<N;i++){pos[i*3]=(Math.random()-.5)*34;pos[i*3+1]=(Math.random()-.5)*16;pos[i*3+2]=(Math.random()-.5)*14-4;}
const sg=new THREE.BufferGeometry();sg.setAttribute('position',new THREE.BufferAttribute(pos,3));
const stars=new THREE.Points(sg,new THREE.PointsMaterial({color:0xffffff,size:.07,transparent:true,opacity:.8}));
scene.add(stars);

const clock=new THREE.Clock();let mx=0,my=0;
window.addEventListener('pointermove',e=>{const r=el.getBoundingClientRect();
  mx=((e.clientX-r.left)/r.width-.5);my=((e.clientY-r.top)/r.height-.5);});
function loop(){
  const t=clock.getElapsedTime();
  sprites.forEach(s=>{const d=s.userData,a=d.a+t*d.sp;
    s.position.set(8.2+Math.cos(a)*d.r,d.y+Math.sin(t*.8+d.ph)*.35,Math.sin(a)*d.r*.6-1);});
  book.rotation.y=Math.sin(t*.5)*.5;book.position.y=-.3+Math.sin(t*1.1)*.18;
  stars.rotation.y=t*.02;
  cam.position.x+=((mx*2)-cam.position.x)*.04;cam.position.y+=((-my*1.2)-cam.position.y)*.04;
  cam.lookAt(3,0,0);renderer.render(scene,cam);requestAnimationFrame(loop);}
loop();
window.addEventListener('resize',()=>{W=el.clientWidth;H=el.clientHeight;renderer.setSize(W,H);
  cam.aspect=W/H;cam.updateProjectionMatrix();});
})();
"""


def hero_html(school: str) -> str:
    css = """
    body{background:linear-gradient(120deg,#F7971E 0%,#FF5F6D 45%,#7B4397 100%);border-radius:22px;}
    .txt{position:absolute;left:34px;top:50%;transform:translateY(-50%);color:#fff;z-index:2;max-width:56%;
      pointer-events:none;text-shadow:0 2px 14px rgba(0,0,0,.25);}
    .txt h1{margin:0;font-size:clamp(2.2rem,5.2vw,4rem);font-weight:800;letter-spacing:-1px;line-height:1.05;}
    .txt .sc{font-size:clamp(.95rem,1.8vw,1.25rem);font-weight:600;margin:8px 0 14px 0;opacity:.96;}
    .tag{display:inline-block;background:rgba(255,255,255,.24);padding:4px 14px;border-radius:999px;
      font-size:.82rem;font-weight:700;margin:4px 8px 0 0;}
    """
    body = (f'<div id="c"></div><div class="txt"><h1>Padho!<br><span style="font-size:.52em;font-weight:700">'
            f'पढ़ो · படி · చదువు · পড়ো</span></h1><div class="sc">AI reading fluency meter · {school}</div>'
            f'<span class="tag">🎙️ Bhashini ASR</span><span class="tag">🇮🇳 NIPUN Bharat Standard</span>'
            f'<span class="tag">📊 Performance Monitoring</span><span class="tag">🧑‍🏫 Personalised Mentor AI</span></div>')
    return _page(css, body, _HERO_JS)


# ------------------------------------------------------------------------ JOURNEY
_JOURNEY_JS = """
(function(){
const P=__PARAMS__;
if(!window.THREE){document.getElementById('fb').style.display='block';return;}
const el=document.getElementById('c');let W=el.clientWidth,H=el.clientHeight;
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(42,W/H,0.1,100);cam.position.set(0,3.2,15);cam.lookAt(0,1.3,0);
const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setSize(W,H);
el.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff,0.75));
const dl=new THREE.DirectionalLight(0xffffff,0.95);dl.position.set(5,8,6);scene.add(dl);

const world=new THREE.Group();scene.add(world);
const mount=new THREE.Mesh(new THREE.ConeGeometry(3.4,6,10,1),
  new THREE.MeshStandardMaterial({color:0x4cae78,flatShading:true}));
mount.position.y=1.2;world.add(mount);
const snow=new THREE.Mesh(new THREE.ConeGeometry(.75,1.25,10),new THREE.MeshStandardMaterial({color:0xffffff,flatShading:true}));
snow.position.y=3.72;world.add(snow);
const ground=new THREE.Mesh(new THREE.CylinderGeometry(4.6,4.9,.3,40),new THREE.MeshStandardMaterial({color:0xf2d28b}));
ground.position.y=-1.95;world.add(ground);

function pos(t){const a=t*Math.PI*2*2.2+0.6,r=3.4*(1-t)+0.28;
  return new THREE.Vector3(Math.cos(a)*r,-1.8+t*6,Math.sin(a)*r);}
function st(i){return 0.04+(i-1)/4*0.9;}

const pts=[];for(let t=0;t<=1.0001;t+=0.01)pts.push(pos(t));
world.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),240,.05,6),
  new THREE.MeshBasicMaterial({color:0xfff1a8})));

for(let i=1;i<=5;i++){
  const p=pos(st(i)),reached=i<=P.level,col=new THREE.Color(reached?P.colors[i-1]:'#9aa5a0');
  const g=new THREE.Group();g.position.copy(p);
  const pole=new THREE.Mesh(new THREE.CylinderGeometry(.03,.03,.9,8),new THREE.MeshStandardMaterial({color:0x5a4a3a}));
  pole.position.y=.45;g.add(pole);
  const flag=new THREE.Mesh(new THREE.PlaneGeometry(.62,.4),new THREE.MeshStandardMaterial({color:col,side:THREE.DoubleSide}));
  flag.position.set(.32,.72,0);g.add(flag);
  const lab=new THREE.Sprite(new THREE.SpriteMaterial({map:tex(P.emojis[i-1],150,'#ffffff','"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif'),transparent:true,opacity:reached?1:.45}));
  lab.scale.set(.75,.75,1);lab.position.set(0,1.3,0);g.add(lab);
  world.add(g);
}

// avatar: student photo (or initial) in a gold ring
const ac=document.createElement('canvas');ac.width=ac.height=256;const ag=ac.getContext('2d');
const atex=new THREE.CanvasTexture(ac);
function drawAvatar(img){
  ag.clearRect(0,0,256,256);
  ag.save();ag.beginPath();ag.arc(128,128,112,0,7);ag.clip();
  if(img){ag.drawImage(img,0,0,256,256);}
  else{ag.fillStyle='#7B4397';ag.fillRect(0,0,256,256);ag.fillStyle='#fff';ag.font='700 140px sans-serif';
    ag.textAlign='center';ag.textBaseline='middle';ag.fillText((P.name||'?').charAt(0).toUpperCase(),128,138);}
  ag.restore();ag.lineWidth=14;ag.strokeStyle='#F2C94C';ag.beginPath();ag.arc(128,128,112,0,7);ag.stroke();
  atex.needsUpdate=true;}
drawAvatar(null);
if(P.photo){const im=new Image();im.onload=()=>drawAvatar(im);im.src='data:image/jpeg;base64,'+P.photo;}
const av=new THREE.Sprite(new THREE.SpriteMaterial({map:atex,transparent:true}));av.scale.set(1.35,1.35,1);world.add(av);

// clouds
const clouds=[];
for(let i=0;i<5;i++){const c=new THREE.Group();
  for(let k=0;k<4;k++){const s=new THREE.Mesh(new THREE.SphereGeometry(.35+Math.random()*.25,10,8),
    new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:.85}));s.position.set(k*.4,Math.random()*.15,0);c.add(s);}
  c.position.set(-7+Math.random()*14,3+Math.random()*2.5,-3-Math.random()*3);scene.add(c);clouds.push(c);}

const tgt=(P.level<5)?st(P.level)+(st(P.level+1)-st(P.level))*Math.min(P.frac,1)*0.9:st(5);
let drag=false,lx=0,rot=0;
el.addEventListener('pointerdown',e=>{drag=true;lx=e.clientX;});
window.addEventListener('pointerup',()=>drag=false);
window.addEventListener('pointermove',e=>{if(drag){rot+=(e.clientX-lx)*.01;lx=e.clientX;}});
const clock=new THREE.Clock();
function ease(x){return 1-Math.pow(1-x,3);}
function loop(){
  const t=clock.getElapsedTime();
  const k=ease(Math.min(t/2.8,1));
  const p=pos(tgt*k);
  av.position.set(p.x,p.y+1.05+Math.sin(t*2.4)*.07,p.z);
  if(!drag)rot+=0.0035;
  world.rotation.y=rot;
  clouds.forEach((c,i)=>{c.position.x+=.003*(i+1);if(c.position.x>8)c.position.x=-8;});
  renderer.render(scene,cam);requestAnimationFrame(loop);}
loop();
window.addEventListener('resize',()=>{W=el.clientWidth;H=el.clientHeight;renderer.setSize(W,H);
  cam.aspect=W/H;cam.updateProjectionMatrix();});
})();
"""


def journey_html(name: str, level: int, frac: float, photo_b64: str, caption: str, levels: dict) -> str:
    css = """
    body{background:linear-gradient(180deg,#8EC5FC 0%,#E0C3FC 100%);border-radius:22px;}
    .cap{position:absolute;left:16px;bottom:12px;right:16px;z-index:2;color:#3B1C57;font-weight:700;
      background:rgba(255,255,255,.78);padding:8px 16px;border-radius:14px;font-size:.98rem;pointer-events:none;}
    .hint{position:absolute;right:16px;top:10px;z-index:2;color:#3B1C57;font-size:.78rem;font-weight:700;opacity:.75;}
    #fb{display:none;position:absolute;top:45%;width:100%;text-align:center;color:#3B1C57;font-weight:700;}
    """
    params = {"name": name, "level": level, "frac": frac, "photo": photo_b64,
              "colors": [levels[i]["color"] for i in sorted(levels)],
              "emojis": [levels[i]["emoji"] for i in sorted(levels)]}
    body = (f'<div id="c"></div><div class="hint">drag to rotate 🏔️</div><div id="fb">3D view needs an internet '
            f'connection</div><div class="cap">{caption}</div>')
    return _page(css, body, _JOURNEY_JS, params)


# ---------------------------------------------------------------------- CONFETTI
_CONFETTI_JS = """
(function(){
const P=__PARAMS__;
if(!window.THREE){return;}
const el=document.getElementById('c');let W=el.clientWidth,H=el.clientHeight;
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(50,W/H,0.1,100);cam.position.z=10;
const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setSize(W,H);
el.appendChild(renderer.domElement);
const cols=[0xF2C94C,0xEB3349,0x2193B0,0x38EF7D,0x8E2DE2,0xF2994A,0xFF5F6D];
const bits=[];
for(let i=0;i<170;i++){
  const m=new THREE.Mesh(new THREE.PlaneGeometry(.2,.3),new THREE.MeshBasicMaterial({color:cols[i%cols.length],side:THREE.DoubleSide,transparent:true}));
  m.position.set((Math.random()-.5)*14,5+Math.random()*7,(Math.random()-.5)*4);
  m.userData={vy:-(1.6+Math.random()*2.6),vx:(Math.random()-.5)*.8,rx:Math.random()*5,ry:Math.random()*5,d:Math.random()*1.2};
  scene.add(m);bits.push(m);}
const clock=new THREE.Clock();let alive=true;
function loop(){
  if(!alive)return;
  const t=clock.getElapsedTime(),dt=Math.min(clock.getDelta(),.05)||0.016;
  bits.forEach(m=>{const u=m.userData;if(t<u.d)return;
    m.position.y+=u.vy*0.016;m.position.x+=u.vx*0.016+Math.sin(t*3+u.rx)*.004;
    m.rotation.x+=u.rx*.02;m.rotation.y+=u.ry*.02;
    m.material.opacity=Math.max(0,Math.min(1,(8-t)/1.5));});
  renderer.render(scene,cam);
  if(t>8.5){alive=false;el.style.display='none';return;}
  requestAnimationFrame(loop);}
loop();
})();
"""


def confetti_html(title: str, sub: str = "") -> str:
    css = """
    body{background:transparent;}
    .msg{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
      z-index:2;text-align:center;pointer-events:none;}
    .msg h1{margin:0;font-size:clamp(1.6rem,4vw,2.6rem);color:#3B1C57;animation:pop .8s ease both;
      text-shadow:0 2px 0 #fff,0 0 18px #fff;}
    .msg p{margin:4px 0 0 0;font-weight:700;color:#5B2F7A;font-size:1.05rem;text-shadow:0 0 10px #fff;}
    @keyframes pop{0%{transform:scale(.3);opacity:0}70%{transform:scale(1.12)}100%{transform:scale(1);opacity:1}}
    """
    body = f'<div id="c"></div><div class="msg"><h1>{title}</h1><p>{sub}</p></div>'
    return _page(css, body, _CONFETTI_JS, {})


# ------------------------------------------------------------------------ MEDAL
_MEDAL_JS = """
(function(){
const P=__PARAMS__;
if(!window.THREE){document.getElementById('fb').style.display='block';return;}
const el=document.getElementById('c');let W=el.clientWidth,H=el.clientHeight;
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(40,W/H,0.1,100);cam.position.set(0,0,8.2);
const renderer=new THREE.WebGLRenderer({alpha:true,antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setSize(W,H);
el.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff,1.1));
const l1=new THREE.DirectionalLight(0xffffff,1.1);l1.position.set(4,5,7);scene.add(l1);
const l2=new THREE.PointLight(0xffe9a8,1.0,30);l2.position.set(-5,-2,5);scene.add(l2);

const medal=new THREE.Group();
const disc=new THREE.Mesh(new THREE.CylinderGeometry(1.5,1.5,.24,64),
  new THREE.MeshStandardMaterial({color:new THREE.Color(P.color),metalness:.35,roughness:.4}));
disc.rotation.x=Math.PI/2;medal.add(disc);
const ring=new THREE.Mesh(new THREE.TorusGeometry(1.5,.08,16,72),
  new THREE.MeshStandardMaterial({color:0xF2C94C,metalness:.9,roughness:.2}));medal.add(ring);
const etex=tex(P.emoji,150,'#ffffff','"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif');
const face=new THREE.Mesh(new THREE.CircleGeometry(1.15,48),new THREE.MeshBasicMaterial({map:etex,transparent:true}));
face.position.z=.13;medal.add(face);
const back=face.clone();back.position.z=-.13;back.rotation.y=Math.PI;medal.add(back);
const rib=new THREE.MeshStandardMaterial({color:0xEB3349,side:THREE.DoubleSide});
[-1,1].forEach(s=>{const r=new THREE.Mesh(new THREE.PlaneGeometry(.55,1.5),rib);
  r.position.set(s*.38,1.95,0);r.rotation.z=s*.28;medal.add(r);});
scene.add(medal);
const clock=new THREE.Clock();
function loop(){const t=clock.getElapsedTime();
  medal.rotation.y=t*.9;medal.position.y=Math.sin(t*1.6)*.12-.2;
  renderer.render(scene,cam);requestAnimationFrame(loop);}
loop();
})();
"""


def medal_html(emoji: str, color: str = "#F2994A") -> str:
    css = "body{background:transparent;} #fb{display:none;position:absolute;top:42%;width:100%;text-align:center;font-size:4rem;}"
    body = f'<div id="c"></div><div id="fb">{emoji}</div>'
    return _page(css, body, _MEDAL_JS, {"emoji": emoji, "color": color})
