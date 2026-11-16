import json
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from padho import badges as bd, config, mentor, three, ui

store = ui.store()
LV = config.LEVELS

ui.page_header("🧒 Student profile", "Photo, level, badges, graphs and the full reading history.")
stud = ui.pick_student("profile_student")
sid = stud["id"]
atts = store.attempts(sid)
earned = {b["badge_key"]: b["earned_at"] for b in store.badges(sid)}
lvl = stud["level"]
lv = LV[lvl]
days = [bd.local_date(a["ts"]) for a in atts]
streak = bd.current_streak(days)

sec = f" · Section {stud['section']}" if stud.get("section") else ""
roll = f" · Roll {stud['roll']}" if stud.get("roll") else ""
st.markdown(
    f'<div class="pcard"><img src="{ui.photo_uri(stud)}" alt=""><div>'
    f'<h2>{stud["name"]}</h2><p>{stud["class_name"]}{sec}{roll} · {config.LANGS[stud["language"]]["label"]}</p>'
    f'<span class="chip chip-lvl">{lv["emoji"]} Level {lvl} · {lv["name"]}</span>'
    f'<span class="chip chip-lvl">🏅 {len(earned)} of {len(bd.BADGES)} badges</span></div></div>',
    unsafe_allow_html=True)

n = len(atts)
wc = [a["wcpm"] for a in atts]
tiles = [("t-purple", n, "readings"), ("t-green", f"{max(wc):.0f}" if wc else "—", "best words/min"),
         ("t-blue", f"{sum(a['accuracy'] for a in atts) / n:.0f}%" if n else "—", "average accuracy"),
         ("t-orange", f"{streak} 🔥", "day streak"), ("t-red", len(earned), "badges earned")]
for col, t in zip(st.columns(5), tiles):
    col.markdown(ui.tile(*t), unsafe_allow_html=True)
st.write("")

# ------------------------------------------------------------- 3D journey + latest badge
got = bd.met_count(atts, lvl)
frac = min(got / config.MET_TO_PROMOTE, 1.0)
if lvl < config.MAX_LEVEL:
    cap = f"{lv['emoji']} Level {lvl} · {lv['name']}  —  {got}/{config.MET_TO_PROMOTE} target readings to reach {LV[lvl + 1]['emoji']} Level {lvl + 1}"
else:
    cap = f"{lv['emoji']} Level {lvl} · {lv['name']}  —  top of the mountain! 🎉"
j, m = st.columns([3, 1], gap="medium")
with j:
    ui.show_html(three.journey_html(stud["name"], lvl, frac, ui.photo_b64(stud), cap, LV), 420)
with m:
    if earned:
        latest = max(earned, key=lambda k: earned[k])
        ui.show_html(three.medal_html(bd.BADGES[latest]["emoji"], bd.BADGES[latest]["color"]), 330)
        st.markdown(f"<p style='text-align:center;font-weight:700;margin-top:-6px'>Latest badge<br>"
                    f"{bd.BADGES[latest]['name']}</p>", unsafe_allow_html=True)
    else:
        st.info("No badges yet. The first one comes after the first reading!")
        st.page_link("views/read.py", label="Start a reading", icon="🎤")

# ---------------------------------------------------------------- personalised mentor
st.markdown(ui.mentor_html(mentor.build(stud, atts, set(earned))), unsafe_allow_html=True)

# ----------------------------------------------------------------------- graphs
if atts:
    xs = list(range(1, n + 1))
    g1, g2 = st.columns(2, gap="large")
    with g1:
        st.markdown("#### 📈 Words per minute")
        f = go.Figure()
        f.add_scatter(x=xs, y=wc, mode="lines+markers", line=dict(color="#7B4397", width=3), marker=dict(size=9),
                      name="words/min")
        f.add_hline(y=lv["wpm"], line_dash="dash", line_color="#E74C3C", annotation_text=f"Level {lvl} target")
        f.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="reading number",
                        yaxis_title="correct words per minute", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(f, **ui.stretch())
    with g2:
        st.markdown("#### 🎯 Accuracy")
        f = go.Figure()
        f.add_scatter(x=xs, y=[a["accuracy"] for a in atts], mode="lines+markers", line=dict(color="#11998E", width=3),
                      marker=dict(size=9), name="accuracy")
        f.add_hline(y=lv["acc"], line_dash="dash", line_color="#E74C3C", annotation_text=f"Level {lvl} target")
        f.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), xaxis_title="reading number",
                        yaxis_title="accuracy %", yaxis_range=[0, 105], paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(f, **ui.stretch())

    miss = Counter()
    for a in atts[-8:]:
        miss.update(json.loads(a["bad_words"] or "[]") + json.loads(a["skip_words"] or "[]"))
    st.markdown("#### 📝 Words that need practice (last 8 readings)")
    if miss:
        st.markdown("".join(f'<span class="chip chip-bad">{w}</span>' for w, _ in miss.most_common(16)),
                    unsafe_allow_html=True)
    else:
        st.success("No difficult words recently. Excellent!")
else:
    st.info("No readings yet. Graphs will appear after the first reading.")

# ----------------------------------------------------------------------- badges
st.markdown("#### 🏅 Badges")
st.markdown('<div class="bgrid">' + "".join(
    f'<div class="bcard {"on" if k in earned else "off"}"><div class="em">{b["emoji"]}</div><b>{b["name"]}</b>'
    f'<span>{b["how"]}</span></div>' for k, b in bd.BADGES.items()) + "</div>", unsafe_allow_html=True)
st.page_link("views/badges_page.py", label="What are motivation badges?", icon="🏅")

# ---------------------------------------------------------------------- history
if atts:
    st.markdown("#### 📚 Reading history")
    df = pd.DataFrame([{
        "Date": bd.parse_ts(a["ts"]).strftime("%d %b %Y %H:%M"), "Level": a["level"],
        "Language": a["language"], "Words/min": round(a["wcpm"], 1), "Accuracy %": round(a["accuracy"], 1),
        "Passage read %": round(a["coverage"], 1), "Correct": a["correct"], "Misread": a["misread"],
        "Skipped": a["skipped"], "Questions": "—" if a["comprehension"] < 0 else f"{a['comprehension']}/3",
        "Target met": "✔" if a["met"] else "",
    } for a in reversed(atts)])
    st.dataframe(df, **ui.stretch(), hide_index=True)
    st.download_button("⬇️ Download history (CSV)", df.to_csv(index=False), f"{stud['name']}_history.csv", "text/csv")

st.page_link("views/report_page.py", label="Open printable progress report", icon="📄")

# ------------------------------------------------------------------ edit / delete
teacher_ok = (not config.TEACHER_PIN) or st.session_state.get("teacher_ok")
if teacher_ok:
    with st.expander("✏️ Edit this student (teachers)"):
        e1, e2 = st.columns(2)
        new_name = e1.text_input("Name", stud["name"])
        new_class = e2.selectbox("Class", config.CLASSES, index=config.CLASSES.index(stud["class_name"])
                                 if stud["class_name"] in config.CLASSES else 3)
        e3, e4, e5 = st.columns(3)
        new_sec = e3.text_input("Section", stud["section"] or "")
        new_roll = e4.text_input("Roll", stud["roll"] or "")
        new_level = e5.selectbox("Level", list(LV), index=lvl - 1,
                                 format_func=lambda k: f"Level {k} · {LV[k]['name']}")
        new_photo = st.file_uploader("Replace photo", type=["jpg", "jpeg", "png"], key="editphoto")
        cam = st.camera_input("…or take a new photo", key="editcam")
        if st.button("Save changes", type="primary"):
            patch = dict(name=new_name.strip() or stud["name"], class_name=new_class, section=new_sec.strip(),
                         roll=new_roll.strip(), level=new_level)
            raw = (new_photo.getvalue() if new_photo else None) or (cam.getvalue() if cam else None)
            if raw:
                patch["photo"] = ui.process_photo(raw)
            store.update_student(sid, **patch)
            ui.forget_photo(sid)
            st.success("Saved.")
            st.rerun()
        st.divider()
        sure = st.checkbox(f"I understand this permanently deletes {stud['name']} and all their readings")
        if st.button("🗑️ Delete student", disabled=not sure):
            store.delete_student(sid)
            ui.forget_photo(sid)
            st.session_state.active_student = None
            st.rerun()
