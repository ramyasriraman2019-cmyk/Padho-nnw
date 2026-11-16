import csv
import io

import streamlit as st

from padho import config, ui

teacher = ui.require_teacher()
store = ui.store()

ui.page_header("📝 Register a student", "Add each child once. Their photo, level and history stay linked to this profile.")

lang_codes = list(config.LANGS)

left, right = st.columns([3, 2], gap="large")
with left:
    name = st.text_input("Student's full name *", placeholder="e.g. Asha Devi")
    c1, c2, c3 = st.columns(3)
    class_name = c1.selectbox("Class *", config.CLASSES, index=3)
    section = c2.text_input("Section", placeholder="A", max_chars=3)
    roll = c3.text_input("Roll no.", placeholder="12")
    c4, c5 = st.columns(2)
    language = c4.selectbox("Reading language *", lang_codes, format_func=lambda c: config.LANGS[c]["label"])
    level = c5.selectbox(
        "Starting level", list(config.LEVELS), index=0,
        format_func=lambda k: f"Level {k} · {config.LEVELS[k]['name']} {config.LEVELS[k]['emoji']}",
        help="Start low. A child is promoted automatically after 3 target readings.",
    )
    consent = st.checkbox(
        "I confirm the parent or guardian has agreed (and the school permits) that this child's name, photo and "
        "reading scores are stored for classroom use. *"
    )

with right:
    st.markdown("**Photo** (optional, shown on the profile and report)")
    mode = st.radio("Photo source", ["Take a picture", "Upload a file", "Skip for now"], horizontal=True,
                    label_visibility="collapsed")
    raw = None
    if mode == "Take a picture":
        shot = st.camera_input("Camera", label_visibility="collapsed")
        raw = shot.getvalue() if shot else None
    elif mode == "Upload a file":
        up = st.file_uploader("Photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        raw = up.getvalue() if up else None
    if raw:
        st.image(raw, width=140, caption="Will be cropped to a square")

if st.button("✅ Register student", type="primary", **ui.stretch()):
    existing = store.students()
    if not name.strip():
        st.error("Please enter the student's name.")
    elif not consent:
        st.error("Please tick the consent box. It protects the child and the school.")
    elif any(s["name"].lower() == name.strip().lower() and s["class_name"] == class_name
             and (s["section"] or "") == section.strip() and (s["roll"] or "") == roll.strip() for s in existing):
        st.warning("A student with the same name, class, section and roll number is already registered.")
    else:
        try:
            photo = ui.process_photo(raw) if raw else None
            sid = store.add_student(name=name.strip(), class_name=class_name, section=section.strip(),
                                    roll=roll.strip(), language=language, level=level, photo=photo,
                                    consent=1, teacher=teacher)
            st.session_state.active_student = sid
            st.success(f"{name.strip()} is registered at Level {level}.")
            st.balloons()
            st.page_link("views/read.py", label="Start the first reading", icon="🎤")
        except Exception as exc:
            st.error("Could not save the student.")
            st.code(str(exc), language=None)

st.divider()
with st.expander("📥 Register a whole class from a CSV file"):
    st.caption("Columns: **name, class, section, roll, language** (language is hi, mr, ta, te, bn, gu or en). "
               "Photos can be added later from each profile. Only tick this if consent has been collected for the whole class.")
    sample = "name,class,section,roll,language\nAsha Devi,Class 3,A,1,ta\nRavi Kumar,Class 3,A,2,ta\n"
    st.download_button("Download a sample CSV", sample, "padho_students_sample.csv", "text/csv")
    f = st.file_uploader("Upload CSV", type=["csv"], key="bulk")
    ok = st.checkbox("Consent has been collected for every child in this file", key="bulkconsent")
    if f and st.button("Import students", disabled=not ok):
        rows = list(csv.DictReader(io.StringIO(f.getvalue().decode("utf-8-sig"))))
        have = {(s["name"].lower(), s["class_name"], s["section"] or "", s["roll"] or "") for s in store.students()}
        added = skipped = 0
        for r in rows:
            nm = (r.get("name") or "").strip()
            cl = (r.get("class") or "").strip()
            lg = (r.get("language") or "en").strip().lower()
            if not nm or cl not in config.CLASSES or lg not in config.LANGS:
                skipped += 1
                continue
            key = (nm.lower(), cl, (r.get("section") or "").strip(), (r.get("roll") or "").strip())
            if key in have:
                skipped += 1
                continue
            store.add_student(name=nm, class_name=cl, section=key[2], roll=key[3], language=lg, level=1,
                              consent=1, teacher=teacher)
            have.add(key)
            added += 1
        st.success(f"Imported {added} students. Skipped {skipped} (duplicates or invalid rows).")
