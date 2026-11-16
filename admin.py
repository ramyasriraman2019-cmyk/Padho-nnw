import json
from datetime import datetime

import pandas as pd
import streamlit as st

from padho import asr, config, storage, tts, ui

ui.require_teacher()
store = ui.store()

ui.page_header("⚙️ Admin & backup", "Database status, Dropbox backup and restore, exports and the Bhashini connection test.")

# -------------------------------------------------------------------- database
st.markdown("### 🗄️ Database")
if store.b.permanent:
    st.success(f"Connected to **{store.b.label}**. Data is permanent.")
else:
    st.warning("Running on a **local test file**. Streamlit Cloud erases it whenever the app restarts, so "
               "connect Supabase before registering real students.")
    note = ui.store_note()
    if note:
        st.error(note)
    with st.expander("How to connect Supabase (free, about 5 minutes)", expanded=True):
        st.markdown(
            "1. Create a free account at **supabase.com** and make a new project.\n"
            "2. Open **SQL Editor → New query**, paste the SQL below and press **Run**.\n"
            "3. Open **Project Settings → API**. Copy the **Project URL** and the **service_role** key.\n"
            "4. In Streamlit Cloud open **⋮ → Settings → Secrets** and add `SUPABASE_URL` and `SUPABASE_KEY`.\n"
            "5. Save. The app restarts and this page shows **Connected**.\n\n"
            "The service_role key stays on the server (Secrets). Never put it in GitHub or share it.")
        try:
            sql = open("supabase_schema.sql", encoding="utf-8").read()
        except Exception:
            sql = "-- supabase_schema.sql not found"
        st.code(sql, language="sql")

students = store.students()
attempts = store.attempts()
c = st.columns(3)
c[0].metric("Students", len(students))
c[1].metric("Readings", len(attempts))
c[2].metric("Badges", len(store.badges()))

# --------------------------------------------------------------------- backup
st.markdown("### ☁️ Backup")
dump = store.dump()
payload = json.dumps(dump, ensure_ascii=False).encode("utf-8")
stamp = datetime.now(config.IST).strftime("%Y%m%d_%H%M")
st.caption(f"A full backup (students with photos, readings and badges) is {len(payload) / 1024:.0f} KB.")

b1, b2 = st.columns(2, gap="large")
with b1:
    st.markdown("**Download to this device**")
    st.download_button("⬇️ Full backup (JSON)", payload, f"padho_backup_{stamp}.json", "application/json")
    if students:
        st.download_button("⬇️ Students (CSV)", pd.DataFrame(students).to_csv(index=False), "padho_students.csv", "text/csv")
    if attempts:
        st.download_button("⬇️ All readings (CSV)", pd.DataFrame(attempts).to_csv(index=False), "padho_readings.csv", "text/csv")

with b2:
    st.markdown("**Dropbox**")
    if storage.dropbox_configured(config.get_secret):
        if st.button("☁️ Back up to Dropbox now", type="primary"):
            try:
                p = storage.dropbox_upload(config.get_secret, payload, f"/Padho/padho_backup_{stamp}.json")
                st.success(f"Saved to Dropbox: {p}")
            except Exception as exc:
                st.error("Dropbox backup failed.")
                st.code(str(exc), language=None)
        if st.button("⬇️ Restore newest Dropbox backup"):
            try:
                path, data = storage.dropbox_latest(config.get_secret)
                counts = store.restore(json.loads(data))
                st.success(f"Restored from {path}: {counts}. Existing records were kept.")
            except Exception as exc:
                st.error("Dropbox restore failed.")
                st.code(str(exc), language=None)
    else:
        st.info("Dropbox is not connected. Add `DROPBOX_ACCESS_TOKEN` (quick test) or, for a permanent link, "
                "`DROPBOX_REFRESH_TOKEN`, `DROPBOX_APP_KEY` and `DROPBOX_APP_SECRET` to Secrets.")
    st.caption("Dropbox is used only as a safe copy. The live database is Supabase.")

up = st.file_uploader("Restore from a backup file (JSON)", type=["json"])
if up and st.button("Restore this file"):
    try:
        data = json.loads(up.getvalue().decode("utf-8"))
        if data.get("app") != "padho":
            raise ValueError("This does not look like a Padho backup file")
        st.success(f"Restored: {store.restore(data)}. Existing records were kept, so restoring twice is safe.")
    except Exception as exc:
        st.error(f"Could not restore: {exc}")

# -------------------------------------------------------------------- bhashini
st.markdown("### 🎤 Bhashini connection test")
uid, key = asr.creds()
if asr.has_keys():
    st.info(f"Keys loaded · user ID ends `…{uid[-4:]}` · key ends `…{key[-4:]}`")
    if st.button("🔍 Test all 7 languages"):
        for code, meta in config.LANGS.items():
            try:
                cfg = asr.test_connection(code)
                st.success(f"{meta['label']}: works · `{cfg['service_id']}`")
            except Exception as exc:
                st.error(f"{meta['label']}: failed")
                st.code(str(exc), language=None)
else:
    st.error("Bhashini keys are missing. Add `BHASHINI_USER_ID` and `BHASHINI_API_KEY` in Secrets.")

if asr.has_keys() and st.button("🔊 Test Bhashini voice (read aloud) for all 7 languages"):
    for code, meta in config.LANGS.items():
        try:
            cfg = tts.test_voice(code)
            st.success(f"{meta['label']}: voice available · `{cfg['service_id']}`")
        except Exception as exc:
            st.warning(f"{meta['label']}: no Bhashini voice ({str(exc)[:160]}). The device voice will be used.")

st.markdown("### 🔐 Security checklist")
st.markdown(
    f"- Teacher PIN: {'✅ set' if config.TEACHER_PIN else '❌ not set. Anyone with the link can edit records. Add `TEACHER_PIN` to Secrets.'}\n"
    "- Keys live only in Streamlit Secrets, never in GitHub.\n"
    "- Recordings are not stored. Only scores and practice words are saved.\n"
    "- Keep the app link within the school and delete students who leave."
)
