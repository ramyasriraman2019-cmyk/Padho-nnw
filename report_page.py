import streamlit as st

from padho import badges as bd, config, mentor, report, ui

store = ui.store()

ui.page_header("📄 Progress card", "Photo, performance graphs, NIPUN Bharat standard, mentor plan, badges and a teacher's note. Print it or save as PDF.")
stud = ui.pick_student("report_student")
atts = store.attempts(stud["id"])
earned = {b["badge_key"] for b in store.badges(stud["id"])}
streak = bd.current_streak([bd.local_date(a["ts"]) for a in atts])

default_note = report.auto_comment(stud["name"], atts, stud["level"])
note = st.text_area("Teacher's note (edit before printing)", value=default_note, height=90,
                    key=f"note_{stud['id']}_{len(atts)}")
teacher = st.text_input("Teacher name on the report", config.TEACHER_NAME)
teacher = f"{teacher}, {config.TEACHER_ROLE}"

plan = mentor.build(stud, atts, earned)
html = report.build_report(stud, ui.photo_uri(stud), atts, earned, config.SCHOOL_NAME, teacher, note, streak, plan)

c1, c2 = st.columns([1, 3])
c1.download_button("⬇️ Download progress card (HTML)", html, f"{stud['name'].replace(' ', '_')}_progress_card.html",
                   "text/html", type="primary")
c2.caption("Open the downloaded file in any browser and press Print → Save as PDF to share on WhatsApp.")
ui.show_html(html, 1250, True)
