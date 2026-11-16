from datetime import datetime, timedelta

import streamlit as st

from padho import config, three, ui
from padho.badges import parse_ts

store = ui.store()
ui.show_html(three.hero_html(config.SCHOOL_NAME), 400)

students = store.students()
attempts = store.attempts()
badges = store.badges()
week_ago = datetime.now(config.IST) - timedelta(days=7)
this_week = sum(1 for a in attempts if parse_ts(a["ts"]) >= week_ago)

st.write("")
c = st.columns(4)
for col, (cls, val, cap) in zip(c, [
    ("t-purple", len(students), "students registered"),
    ("t-green", len(attempts), "readings recorded"),
    ("t-blue", this_week, "readings this week"),
    ("t-orange", len(badges), "badges earned 🏅"),
]):
    col.markdown(ui.tile(cls, val, cap), unsafe_allow_html=True)

st.markdown("#### What powers Padho")
st.markdown(ui.features_html(), unsafe_allow_html=True)

st.markdown("#### How it works")
s = st.columns(4)
for col, (n, t, d) in zip(s, [
    (1, "Register", "Add each child once, with a photo, class and language."),
    (2, "Read aloud", "Pick a level. The child reads the passage into the microphone."),
    (3, "Instant feedback", "Every word is colour-coded. Practice words are listed."),
    (4, "Watch them grow", "Profiles, graphs, badges and a printable report for parents."),
]):
    col.markdown(f'<div class="step"><div class="n">{n}</div><b>{t}</b><span>{d}</span></div>', unsafe_allow_html=True)

st.markdown("#### The reading mountain: 5 levels")
st.markdown(
    '<div class="lvlrow">' + "".join(
        f'<div class="lvl" style="background:{v["color"]}"><b>{v["emoji"]} Level {k} · {v["name"]}</b>'
        f'<span>{v["wpm"]} words/min · {v["acc"]}% accuracy<br>{v["desc"]}</span></div>'
        for k, v in config.LEVELS.items()) + "</div>",
    unsafe_allow_html=True,
)

b = st.columns(4)
b[0].page_link("views/register.py", label="Register a student", icon="📝")
b[1].page_link("views/read.py", label="Start a reading", icon="🎤")
b[2].page_link("views/profile.py", label="Student profiles", icon="🧒")
b[3].page_link("views/badges_page.py", label="What are badges?", icon="🏅")

st.divider()
st.caption(
    f"{config.TEACHER_NAME}, {config.TEACHER_ROLE} · {config.SCHOOL_NAME} · Padho is a practice and screening tool for teachers and "
    "parents, not an examination and not a diagnosis. Speech recognition can mis-hear accents and young "
    "children, so always check the transcript before acting on a low score."
)
