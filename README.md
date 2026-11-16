# 📖 Padho! — AI Oral Reading Fluency Meter (v2)

Listens to a child read aloud and measures **how fluently they read**, in seven Indian
languages, using the Government of India's **Bhashini** speech recognition. Built for the
**NIPUN Bharat** mission.

By **K M Ramyasri**, Primary School Teacher (PST), **Suthukeny Government High School**.

## The four pillars (shown on the Home page and on every Progress Card)

| | |
|---|---|
| 🎙️ **Bhashini ASR** | Government of India speech recognition (MeitY, AI4Bharat models) listens to the child in 7 languages |
| 🇮🇳 **NIPUN Bharat Standard** | Reference targets follow the Ministry of Education goal: 45-60 words/min by end of Class 2, at least 60 by end of Class 3, read with meaning |
| 📊 **Student Performance Monitoring** | Every reading saved; graphs per child; class dashboard |
| 🧑‍🏫 **Personalised Mentor AI** | Reads each child's own history and writes a personal 3-day practice plan, focus words and next goal |

The mentor is data-driven and rule-based (see `padho/mentor.py`). It runs inside the app, so nothing about the
child is sent to any outside AI service. It supports the teacher and does not replace her.

## Read-along: the app reads the passage first

On **Read & Assess**, switch on **"Let the app read this passage aloud first"**. The passage appears with a
**🔊 Listen** button (and a **🐢 Slow** option). Each word lights up as it is spoken, then the child reads it
aloud into the microphone.

- **Bhashini voice:** tries the Government's text-to-speech (female or male) using your Bhashini keys. The voice
  is generated once per passage and remembered, so repeat listens are instant.
- **Device voice:** the phone or computer's own voice. Works without Bhashini, but depends on the device having a
  voice for that language (Android Chrome usually does; some Windows PCs lack Tamil or Telugu).
- If the Bhashini voice is not available for a language, the app tells you and uses the device voice.
- Word highlighting is approximate (timed across the speech), and is a guide for the child's eyes only.
- Admin page → **Test Bhashini voice** shows which languages have a Bhashini voice on your account.

## What is new in v2

| Area | Feature |
|---|---|
| Students | Registration with photo (camera or upload), consent tick-box, CSV import for a whole class |
| Profile | Photo card, level, streak, WPM and accuracy graphs, full reading history, 3D "reading mountain" |
| Levels | 5 levels × 7 languages (35 passages). Promotion after 3 target readings |
| Motivation | 18 badges + a **Motivation Badges** page for children and teachers. No leaderboard |
| Reports | Printable one-page progress report with photo, graphs, badges, practice words, teacher's note |
| Teacher | PIN login, class dashboard ("needs attention" list), CSV exports |
| Storage | **Supabase** (permanent, free) with local SQLite fallback; **Dropbox** backup and restore |
| 3D | Three.js hero scene, reading-mountain journey, level-up confetti, spinning badge medal |
| Fixes | Silence trimmed before computing words/min; Google backup recogniser is **off by default** |

## Pages

Home · Motivation Badges · Register student · Read & Assess · Student profile · Personalised Mentor AI ·
Progress card · Class dashboard · Admin & backup

## Deploying (Streamlit Community Cloud)

1. Put this folder on GitHub (the `.gitignore` already blocks secrets and `*.db`).
2. share.streamlit.io → **New app** → main file `app.py` → Deploy.
3. **⋮ → Settings → Secrets**: paste the lines from `.streamlit/secrets.toml.example` with your real values.

### Database: Supabase (free)
1. supabase.com → new project.
2. SQL Editor → paste `supabase_schema.sql` → Run.
3. Project Settings → API → copy **Project URL** and the **service_role** key into Secrets as
   `SUPABASE_URL` and `SUPABASE_KEY`. The key stays on the server; never put it in GitHub.

Free-tier note: a Supabase project that sees no use for a week is paused; open the dashboard and press
**Restore**. The Dropbox backup button on the Admin page protects you either way.

### Dropbox backup
Dropbox is used as a **safe copy**, not as the live database (it has no record locking and its access
tokens expire). On the Admin page, **Back up to Dropbox** writes `/Padho/padho_backup_<date>.json`;
**Restore newest backup** reads it back (existing records are kept, so restoring twice is safe).
Use `DROPBOX_REFRESH_TOKEN` + app key/secret for a permanent link; `DROPBOX_ACCESS_TOKEN` alone expires in hours.

## Running locally
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit
streamlit run app.py
```
Without Supabase keys the app runs on a local file `padho_local.db` (fine for trying it out).

## Tests
```bash
pytest tests/test_core.py          # scoring, badges, storage
python tests/test_pages.py         # every page runs with seeded data
python tests/test_read_flow.py     # record → score → save → badge → level-up
pytest tests/test_tts.py           # read-aloud (Bhashini voice stubbed)
python tests/test_listen_page.py   # Read page with read-along on
```

## Adding passages
Built-in: `padho/passages.py`. To add more without code, create `data/passages_extra.json`:
```json
{"ta": {"2": ["another Tamil level-2 passage"]}}
```
Levels 4 and 5 were newly written; **please have a native speaker of each language check them once.**

## Privacy
- Recordings are sent to Bhashini and **never stored**. Only scores and the practice-word list are saved.
- Student name, class and photo are stored; the consent tick-box is required at registration.
  Check your school's and state's rules on children's data (India's DPDP Act 2023 asks for verifiable parental consent).
- Set `TEACHER_PIN`. Without it anyone with the link can edit records.

## Honest limits
- Speech recognition mis-hears strong accents and young children. The transcript is always shown.
- Padho measures **fluency**, not comprehension. Teachers can record how many of 3 oral questions a child answered.
- Level targets are **reference bands**, not an examination standard (NIPUN Bharat: about 60 wpm by end of Class 3 = Level 3).
- It needs internet (Bhashini and the 3D library load online; the app still works without the 3D scenes).

## Licence
MIT
