import streamlit as st

from padho import badges as bd, config, three, ui

store = ui.store()
LV = config.LEVELS

# --------------------------------------------------------------------- hero
h1, h2 = st.columns([3, 2], gap="large")
with h1:
    ui.page_header("🏅 What are Motivation Badges?",
                   "Small, visible celebrations that tell a child: “I can see you are getting better.”")
    st.markdown(
        "A **motivation badge** is a small reward a child earns for something specific they did: reading five times, "
        "beating their own best score, coming back after a break. It appears on their profile and report so "
        "that progress is **seen**, not just marked.\n\n"
        "Reading fluency grows slowly, a few words per minute at a time. Without something to notice along the way, "
        "a child who improves from 12 to 20 words per minute may still feel “bad at reading”. Badges make that "
        "invisible progress visible, so the next practice feels worth doing."
    )
with h2:
    ui.show_html(three.medal_html("🏅", "#F2994A"), 300)

st.divider()

# -------------------------------------------------------------- principles
st.markdown("### Three rules Padho follows")
r = st.columns(3)
for col, (n, t, d) in zip(r, [
    (1, "Progress, not rank",
     "Badges compare a child with their own earlier readings. There is no leaderboard, because a ranking tells half the "
     "class they are behind before they have started."),
    (2, "Reward effort as well as skill",
     "Showing up, coming back and improving earn badges too, so a child who is still learning can win just as often "
     "as a fast reader."),
    (3, "Always within reach",
     "Every badge is earned by something the child can do. The first one arrives after a single reading, so "
     "every child starts with a win."),
]):
    col.markdown(f'<div class="step"><div class="n">{n}</div><b>{t}</b><span>{d}</span></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------- gallery
st.markdown("### All badges and how to earn them")
studs = store.students()
by_id = {s["id"]: s for s in studs}
ids = [None] + [s["id"] for s in studs]
sid = st.selectbox("Show which badges this student has earned", ids,
                   index=ids.index(st.session_state.get("active_student")) if st.session_state.get("active_student") in ids else 0,
                   format_func=lambda i: "Show all badges (no student)" if i is None else ui.student_label(by_id[i]))
earned = {b["badge_key"] for b in store.badges(sid)} if sid else set()
if sid:
    st.progress(len(earned) / len(bd.BADGES), text=f"{by_id[sid]['name']} has earned {len(earned)} of {len(bd.BADGES)} badges")

for cat, (title, blurb) in bd.CATEGORIES.items():
    st.markdown(f"#### {title}")
    st.caption(blurb)
    st.markdown('<div class="bgrid">' + "".join(
        f'<div class="bcard {("on" if k in earned else "off") if sid else "on"}"><div class="em">{b["emoji"]}</div>'
        f'<b>{b["name"]}</b><span>{b["how"]}</span></div>'
        for k, b in bd.BADGES.items() if b["cat"] == cat) + "</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------- levels
st.markdown("### The reading mountain")
st.markdown(
    f"Each child climbs five levels. A child moves up after **{config.MET_TO_PROMOTE} target readings** at their "
    f"current level, meaning the speed **and** accuracy target met, with at least {config.MIN_COVERAGE_FOR_TARGET}% of the passage read.")
st.markdown('<div class="lvlrow">' + "".join(
    f'<div class="lvl" style="background:{v["color"]}"><b>{v["emoji"]} Level {k} · {v["name"]}</b>'
    f'<span>{v["wpm"]} words/min · {v["acc"]}% accuracy<br>{v["desc"]}</span></div>' for k, v in LV.items()) + "</div>",
    unsafe_allow_html=True)
st.caption("These are reference bands for practice, not an examination standard. NIPUN Bharat aims for about 60 "
           "words per minute by the end of Class 3, which is Level 3 here.")

# ------------------------------------------------------------------ teacher tips
st.markdown("### Tips for teachers")
t1, t2 = st.columns(2, gap="large")
with t1:
    st.markdown(
        "**Do**\n"
        "- Say the badge out loud: “You earned Comeback Kid because you came back after a break.”\n"
        "- Celebrate in assembly or on the board: a **Badge of the Week** for effort, not only the top scorer.\n"
        "- Link the badge to the practice-word list so the child knows the next step.\n"
        "- Point to the child's own graph: “Look, you were at 14 and now you are at 27.”"
    )
with t2:
    st.markdown(
        "**Avoid**\n"
        "- Comparing children’s badge counts or reading them out as a ranking.\n"
        "- Giving badges for free. They only mean something when they are earned.\n"
        "- Treating a missing badge as a failure. Some children need more time and that is fine.\n"
        "- Using badges as a punishment or a threat."
    )
st.info("Badges are encouragement, not assessment. A child can score well here and still need help with "
        "understanding, which is why Padho also lets you record how many of 3 oral questions they answered.", icon="💡")
