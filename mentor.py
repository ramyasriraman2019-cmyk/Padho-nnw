import streamlit as st

from padho import config, mentor, ui

store = ui.store()

ui.page_header("🧑‍🏫 Personalised Mentor AI",
               "A personal practice plan built from this child's own reading history.")
stud = ui.pick_student("mentor_student")
atts = store.attempts(stud["id"])
earned = {b["badge_key"] for b in store.badges(stud["id"])}

plan = mentor.build(stud, atts, earned)
st.markdown(ui.mentor_html(plan), unsafe_allow_html=True)

if plan["has_data"]:
    s = plan["stats"]
    c = st.columns(3)
    for col, (cls, v, cap) in zip(c, [("t-purple", f"{s['wcpm']:.0f}", "words/min (last 3 readings)"),
                                      ("t-blue", f"{s['accuracy']:.0f}%", "accuracy (last 3 readings)"),
                                      ("t-orange", f"{s['coverage']:.0f}%", "of passage reached")]):
        col.markdown(ui.tile(cls, v, cap), unsafe_allow_html=True)
    st.write("")

with st.expander("How the Personalised Mentor works"):
    st.markdown(
        "The mentor looks at the child's last readings: **speed**, **accuracy**, how much of each passage they "
        "**finish**, their **difficult words** and how many oral questions they answered. It then picks the pattern "
        "that fits (tires before the end, accurate but slow, fast but careless, building skill, or on target) and "
        "writes a 3-day plan, focus words and a next goal.\n\n"
        "It works only from data already in Padho. Nothing about the child is sent to any outside AI service. It "
        "is advice for the teacher and parents, not a diagnosis, and the teacher's judgement always comes first.")
st.page_link("views/report_page.py", label="Open the progress card (includes this plan)", icon="📄")
