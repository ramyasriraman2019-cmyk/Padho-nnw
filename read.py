import json

import plotly.graph_objects as go
import streamlit as st

from padho import asr, badges as bd, config, listen, scoring, three, tts, ui
from padho.passages import passages_for

teacher = ui.require_teacher()
store = ui.store()
LV = config.LEVELS

ui.page_header("🎤 Read & Assess", "Choose the child, choose the passage, press record. Results appear in seconds.")


def gauge(wcpm, target):
    top = max(target * 1.6, wcpm * 1.2, 30)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(wcpm, 1),
        number={"font": {"size": 46, "color": "#2C3E50"}, "suffix": " wpm"},
        gauge={"axis": {"range": [0, top]}, "bar": {"color": "#7B4397", "thickness": 0.72}, "bgcolor": "white",
               "borderwidth": 0,
               "steps": [{"range": [0, target * 0.6], "color": "#FADBD8"},
                         {"range": [target * 0.6, target], "color": "#FCF3CF"},
                         {"range": [target, top], "color": "#D5F5E3"}],
               "threshold": {"line": {"color": "#E74C3C", "width": 4}, "thickness": 0.85, "value": target}}))
    fig.update_layout(height=230, margin=dict(l=18, r=18, t=10, b=6), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def passage_html(disp, status):
    cls = {"ok": "w-ok", "bad": "w-bad", "skip": "w-skip", "wait": "w-wait"}
    words = " ".join(f'<span class="{cls[s]}">{t}</span>' for t, s in zip(disp, status))
    return f'<div class="passage-box">{words}</div>'


# ------------------------------------------------------------------ 1. who + what
stud = ui.pick_student("read_student", allow_guest=True, label="Who is reading?")

lang_codes = list(config.LANGS)
default_lang = stud["language"] if stud else "hi"
default_lvl = stud["level"] if stud else 1

c1, c2, c3 = st.columns([2, 2, 3])
lang = c1.selectbox("Language", lang_codes, index=lang_codes.index(default_lang),
                    format_func=lambda c: config.LANGS[c]["label"], key=f"lang_{stud['id'] if stud else 'g'}")
level = c2.selectbox("Level", list(LV), index=default_lvl - 1,
                     format_func=lambda k: f"Level {k} · {LV[k]['name']} {LV[k]['emoji']}",
                     key=f"lvl_{stud['id'] if stud else 'g'}_{default_lvl}")
bench = LV[level]
c3.markdown(f"**Target for this level:** {bench['wpm']} words/min at {bench['acc']}% accuracy  \n"
            f"<span class='small-note'>{bench['desc']}</span>", unsafe_allow_html=True)

if stud:
    atts = store.attempts(stud["id"])
    got = bd.met_count(atts, stud["level"])
    if stud["level"] < config.MAX_LEVEL:
        st.progress(min(got / config.MET_TO_PROMOTE, 1.0),
                    text=f"{stud['name']}: {got} of {config.MET_TO_PROMOTE} target readings toward Level {stud['level'] + 1}")

options = passages_for(lang, level)
pick = 0
if len(options) > 1:
    pick = st.radio("Passage", range(len(options)), horizontal=True, format_func=lambda i: f"Passage {i + 1}")

left, right = st.columns([6, 5], gap="large")
with left:
    st.markdown("#### 1️⃣  The passage")
    passage_text = st.text_area("Teachers can edit or paste any passage", value=options[pick], height=150,
                                key=f"passage_{lang}_{level}_{pick}")
    disp_tokens, ref_norm = scoring.tokenise(passage_text)
    st.caption(f"{len(ref_norm)} words · {config.LANGS[lang]['label']}")
    # ---- let the app read the passage first (read-along) ---------------------------
    listen_on = st.toggle("🔊 Let the app read this passage aloud first", key=f"listen_{lang}_{level}_{pick}",
                          help="Each word lights up as it is spoken. The child listens, then reads it aloud.")
    if listen_on:
        voices = (["Bhashini voice", "Device voice"] if asr.has_keys() else ["Device voice"])
        v1, v2 = st.columns([3, 2])
        voice = v1.radio("Voice", voices, horizontal=True, key="voice_mode")
        gender = v2.radio("Bhashini voice", ["female", "male"], horizontal=True, key="voice_gender",
                          disabled=voice != "Bhashini voice")
        audio_b64 = ""
        if voice == "Bhashini voice":
            try:
                with st.spinner("Preparing the Bhashini voice…"):
                    audio_b64 = tts.speak(passage_text, lang, gender)
            except Exception as exc:
                st.warning("The Bhashini voice is not available for this language right now, so the device voice "
                           "is used instead.")
                st.caption(str(exc)[:240])
        ui.show_html(listen.listen_html(disp_tokens, passage_text, audio_b64, config.LANGS[lang]["sr"]),
                     listen.frame_height(passage_text))
        st.caption("Highlighting is approximate. After listening, the child reads the passage aloud into the microphone.")

    comp = st.select_slider(
        "Optional: after reading, ask 3 oral questions about the passage. How many did the child answer?",
        options=[-1, 0, 1, 2, 3], value=-1,
        format_func=lambda v: "Not asked" if v < 0 else f"{v} of 3", key=f"comp_{lang}_{level}_{pick}")

with right:
    st.markdown("#### 2️⃣  Record the child reading aloud")
    audio = st.audio_input("Press the microphone, let the child read, then press stop")
    st.caption("Quiet room, phone or laptop mic about 30 cm away. The child reads the whole passage without stopping.")
    strict_label = st.radio(
        "Marking strictness", list(config.STRICTNESS), horizontal=True,
        help="Strict: a word must match exactly, so a changed sound (sooriyan → sariyan) is marked as misread. "
             "Standard and Lenient forgive small differences, which also forgives some real mispronunciations.")
    ok_ratio = config.STRICTNESS[strict_label]
    allow_backup = st.toggle("Backup recogniser if Bhashini fails", value=False,
                             help="Off by default: the backup sends the recording to Google, not to the Government's Bhashini.")

analyse = st.button("✨ Check the reading", type="primary", **ui.stretch(), disabled=audio is None)

# ---------------------------------------------------------------------- 2. analyse
if analyse and audio is not None and ref_norm:
    st.session_state.pop("read_result", None)
    try:
        with st.spinner("Listening to the recording…"):
            samples = asr.decode_audio(audio.getvalue())
        if len(samples) / 16000 < 1.0:
            st.warning("That recording is too short. Record at least a few seconds.")
            st.stop()
        reading = scoring.trim_silence(samples)
        duration = len(reading) / 16000.0

        with st.spinner("Sending to Bhashini…"):
            transcript, engine = asr.transcribe(samples, lang, config.LANGS[lang]["sr"], allow_backup)
        if not transcript:
            st.error("Nothing was recognised. Check the microphone and try again in a quieter place.")
            st.stop()

        _, hyp_norm = scoring.tokenise(transcript)
        res = scoring.score_reading(ref_norm, hyp_norm, ok_ratio)
        wcpm, accuracy, coverage = scoring.compute_metrics(res, len(ref_norm), duration)
        met = int(wcpm >= bench["wpm"] and accuracy >= bench["acc"] and coverage >= config.MIN_COVERAGE_FOR_TARGET)
        v_cls, v_head, v_sub = scoring.verdict_for(wcpm, accuracy, bench["wpm"], bench["acc"])

        bad_words = list(dict.fromkeys(d for d, s in zip(disp_tokens, res["status"]) if s == "bad"))
        skip_words = list(dict.fromkeys(d for d, s in zip(disp_tokens, res["status"]) if s == "skip"))

        new_badges, level_up = [], None
        if stud:
            store.add_attempt(student_id=stud["id"], language=lang, level=level, wcpm=round(wcpm, 1),
                              accuracy=round(accuracy, 1), coverage=round(coverage, 1), correct=res["correct"],
                              misread=res["misread"], skipped=res["skipped"], extra=res["extra"],
                              duration=round(duration, 1), comprehension=comp, met=met,
                              bad_words=json.dumps(bad_words, ensure_ascii=False),
                              skip_words=json.dumps(skip_words, ensure_ascii=False))
            all_att = store.attempts(stud["id"])
            new_level = bd.promotion(stud["level"], all_att)
            if new_level != stud["level"]:
                store.update_student(stud["id"], level=new_level)
                level_up = (stud["level"], new_level)
            earned = {b["badge_key"] for b in store.badges(stud["id"])}
            new_badges = bd.evaluate(new_level, all_att, earned)
            for k in new_badges:
                store.award(stud["id"], k)

        st.session_state.read_result = dict(
            who=stud["name"] if stud else "Guest", saved=bool(stud), disp=disp_tokens, status=res["status"],
            wcpm=wcpm, accuracy=accuracy, coverage=coverage, res=res, duration=duration, met=met,
            verdict=(v_cls, v_head, v_sub), bad=bad_words, skip=skip_words, transcript=transcript,
            engine=engine, heard=len(hyp_norm), new_badges=new_badges, level_up=level_up, target=bench["wpm"],
            raw_seconds=len(samples) / 16000.0)
    except Exception as exc:
        st.error("Could not complete the assessment.")
        st.code(str(exc), language=None)
        st.markdown(
            "**How to read this error**\n"
            "- `HTTP 401` or `403`: the user ID or API key is wrong. Copy both again from the ULCA dashboard.\n"
            "- `HTTP 400`: the account has no access to this pipeline, or no model for this language. Use the "
            "connection test on the **Admin** page.\n"
            "- `could not make out any speech`: the recording was too quiet or too short.")

# ---------------------------------------------------------------------- 3. result
R = st.session_state.get("read_result")
if R:
    st.markdown("#### 3️⃣  Result")
    v_cls, v_head, v_sub = R["verdict"]
    st.markdown(f'<div class="verdict {v_cls}"><h2>{R["who"]}: {v_head}</h2><p>{v_sub}</p></div>', unsafe_allow_html=True)

    celebrate = None
    if R["level_up"]:
        a, b = R["level_up"]
        celebrate = (f"🎉 Level up! {LV[b]['emoji']} {LV[b]['name']}", f"{R['who']} climbed from Level {a} to Level {b}")
    elif R["new_badges"]:
        k = R["new_badges"][0]
        celebrate = (f"🏅 New badge: {bd.BADGES[k]['emoji']} {bd.BADGES[k]['name']}", f"Well done, {R['who']}!")
    elif v_cls == "v-gold":
        celebrate = ("🏆 Target reached!", f"Wonderful reading, {R['who']}!")
    if celebrate:
        ui.show_html(three.confetti_html(*celebrate), 190)

    c1, c2 = st.columns([5, 4], gap="large")
    with c1:
        st.markdown(passage_html(R["disp"], R["status"]), unsafe_allow_html=True)
        st.markdown('<div class="legend" style="margin-top:10px"><span style="color:#21A05A">● read correctly</span>'
                    '<span style="color:#E23D33">● misread</span><span style="color:#B4BCB8">● skipped</span>'
                    '<span style="color:#9AA29E">● not reached</span></div>', unsafe_allow_html=True)
    with c2:
        st.plotly_chart(gauge(R["wcpm"], R["target"]), **ui.stretch())
        tiles = [("t-green", R["res"]["correct"], "words correct"), ("t-red", R["res"]["misread"], "misread"),
                 ("t-grey", R["res"]["skipped"], "skipped"), ("t-blue", f"{R['accuracy']:.0f}%", "accuracy"),
                 ("t-purple", f"{R['duration']:.1f}s", "reading time"), ("t-orange", f"{R['coverage']:.0f}%", "of passage read")]
        for row in (tiles[:3], tiles[3:]):
            for col, (cls, val, cap) in zip(st.columns(3), row):
                col.markdown(ui.tile(cls, val, cap), unsafe_allow_html=True)
        st.caption("Reading time ignores silence before the child starts and after they finish.")

    if R["new_badges"]:
        st.markdown("#### 🏅 New badges")
        st.markdown('<div class="bgrid">' + "".join(
            f'<div class="bcard on new"><div class="em">{bd.BADGES[k]["emoji"]}</div><b>{bd.BADGES[k]["name"]}</b>'
            f'<span>{bd.BADGES[k]["how"]}</span></div>' for k in R["new_badges"]) + "</div>", unsafe_allow_html=True)

    st.markdown("#### 📝 Words to practise")
    if R["bad"] or R["skip"]:
        chips = "".join(f'<span class="chip chip-bad">{w}</span>' for w in R["bad"])
        chips += "".join(f'<span class="chip chip-skip">{w}</span>' for w in R["skip"])
        st.markdown(chips, unsafe_allow_html=True)
        st.caption("Red = said differently · grey = jumped over. Practise these five times each.")
    else:
        st.success("Every word attempted was read correctly. Nothing to practise here.")

    if R["saved"]:
        st.success(f"Saved to {R['who']}'s history.")
        st.page_link("views/profile.py", label="Open profile", icon="🧒")
    else:
        st.info("Guest reading: not saved. Register the child to keep their history and earn badges.")

    with st.expander("🔍 What the recogniser heard (check it was fair)"):
        st.info(R["transcript"])
        st.caption(f"Engine: {R['engine']} · {R['heard']} words heard · {R['res']['extra']} extra words")
        st.caption("Speech recognition sometimes 'corrects' a mispronounced word to the right one. If the child clearly "
                   "said a word wrongly but it shows green, trust your own ears and note it for practice.")
