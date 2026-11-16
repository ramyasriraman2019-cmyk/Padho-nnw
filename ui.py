"""Shared UI helpers: CSS, store access, photos, teacher login, sidebar."""

import base64
import hashlib
import hmac
import io

import streamlit as st

from . import asr, config
from .storage import Store, SQLiteBackend, SupabaseBackend

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Mukta:wght@400;600;700&display=swap');
html, body, [class*="css"]  { font-family: 'Mukta', sans-serif; }
h1, h2, h3, h4 { font-family: 'Baloo 2', sans-serif !important; }
.block-container { padding-top: 3.6rem; max-width: 1250px; }

.page-title { font-family:'Baloo 2',sans-serif; font-size:2.1rem; font-weight:800; margin:0; color:#3B1C57; }
.page-sub   { color:#6B6F73; font-weight:600; margin:0 0 14px 0; }

.passage-box { background:#FFFDF5; border:2px dashed #F0A227; border-radius:18px; padding:26px 28px;
  font-family:'Baloo 2',sans-serif; font-weight:500; font-size:1.55rem; line-height:2.15; color:#9AA29E; }
.w-ok   { color:#21A05A; }
.w-bad  { color:#E23D33; text-decoration:underline wavy #E23D33; text-underline-offset:6px; }
.w-skip { color:#B4BCB8; text-decoration:line-through; }
.w-wait { color:#9AA29E; }

.tile { border-radius:18px; padding:16px 18px; color:#fff; height:100%; box-shadow:0 6px 16px rgba(0,0,0,.10); }
.tile b { display:block; font-family:'Baloo 2',sans-serif; font-size:2.0rem; line-height:1.1; }
.tile span { font-size:.85rem; font-weight:600; opacity:.95; }
.t-green  { background:linear-gradient(135deg,#11998E,#38EF7D); }
.t-red    { background:linear-gradient(135deg,#EB3349,#F45C43); }
.t-grey   { background:linear-gradient(135deg,#606C88,#3F4C6B); }
.t-blue   { background:linear-gradient(135deg,#2193B0,#6DD5ED); }
.t-purple { background:linear-gradient(135deg,#8E2DE2,#4A00E0); }
.t-orange { background:linear-gradient(135deg,#F7971E,#FFD200); color:#3B2A00; }

.verdict { border-radius:18px; padding:20px 24px; color:#fff; margin:6px 0 14px 0; }
.verdict h2 { margin:0; font-size:1.85rem; }
.verdict p  { margin:4px 0 0 0; font-weight:600; opacity:.95; }
.v-gold { background:linear-gradient(120deg,#F2994A,#F2C94C); color:#3B2A00; }
.v-good { background:linear-gradient(120deg,#11998E,#38EF7D); }
.v-mid  { background:linear-gradient(120deg,#2193B0,#6DD5ED); }
.v-low  { background:linear-gradient(120deg,#EB3349,#F45C43); }

.chip { display:inline-block; font-family:'Baloo 2',sans-serif; font-weight:600; font-size:1.05rem;
  padding:5px 16px; border-radius:999px; margin:4px 6px 4px 0; }
.chip-bad  { background:#FFE8E6; color:#C0392B; border:1.5px solid #F5B7B1; }
.chip-skip { background:#EEF1F0; color:#5D6D66; border:1.5px solid #D5DBD8; }
.chip-lvl  { background:#F4ECFA; color:#5B2F7A; border:1.5px solid #D9C2EC; }

.legend span { font-size:.85rem; font-weight:600; margin-right:16px; }
.small-note { font-size:.8rem; color:#7A857F; }

/* student header card */
.pcard { display:flex; gap:22px; align-items:center; background:#fff; border-radius:22px; padding:18px 22px;
  box-shadow:0 8px 24px rgba(123,67,151,.13); border:1px solid #F0E4F7; margin-bottom:14px; }
.pcard img { width:112px; height:112px; border-radius:50%; object-fit:cover; border:4px solid #F2C94C;
  box-shadow:0 4px 14px rgba(0,0,0,.18); }
.pcard h2 { margin:0; font-size:2rem; color:#3B1C57; }
.pcard p { margin:2px 0 0 0; color:#6B6F73; font-weight:600; }

/* badge cards */
.bgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr)); gap:14px; margin:8px 0 18px 0; }
.bcard { border-radius:20px; padding:16px 12px; text-align:center; background:#fff; border:2px solid #F0E4F7;
  box-shadow:0 5px 14px rgba(0,0,0,.06); transition:transform .15s; }
.bcard:hover { transform:translateY(-3px); }
.bcard .em { font-size:2.5rem; line-height:1.2; }
.bcard b { display:block; font-family:'Baloo 2',sans-serif; font-size:1.05rem; color:#3B1C57; }
.bcard span { font-size:.8rem; color:#6B6F73; font-weight:600; }
.bcard.on  { border-color:#F2C94C; background:linear-gradient(160deg,#FFFDF2,#FFF1C9); }
.bcard.off { filter:grayscale(1); opacity:.5; }
.bcard.new { animation:pop .7s ease; border-color:#F2994A; }
@keyframes pop { 0%{transform:scale(.6);opacity:0} 70%{transform:scale(1.08)} 100%{transform:scale(1);opacity:1} }

.step { background:#fff; border-radius:20px; padding:18px 20px; border:1px solid #F0E4F7;
  box-shadow:0 5px 14px rgba(123,67,151,.08); height:100%; }
.step .n { display:inline-flex; width:34px; height:34px; border-radius:50%; background:#7B4397; color:#fff;
  align-items:center; justify-content:center; font-weight:800; font-family:'Baloo 2'; margin-bottom:6px; }
.step b { font-family:'Baloo 2',sans-serif; font-size:1.15rem; color:#3B1C57; display:block; }
.step span { color:#5E6368; font-size:.95rem; }

.lvlrow { display:flex; gap:10px; flex-wrap:wrap; margin:6px 0 12px 0; }
.lvl { flex:1; min-width:150px; border-radius:18px; padding:14px 16px; color:#fff; box-shadow:0 6px 14px rgba(0,0,0,.12); }
.lvl b { font-family:'Baloo 2',sans-serif; font-size:1.2rem; display:block; }
.lvl span { font-size:.82rem; font-weight:600; opacity:.95; }

/* mentor card */
.mentor { background:linear-gradient(135deg,#F4ECFA,#FFF4E6); border:2px solid #D9C2EC; border-radius:22px;
  padding:20px 24px; margin:6px 0 14px 0; box-shadow:0 8px 22px rgba(123,67,151,.12); }
.mentor h3 { margin:0 0 4px 0; font-size:1.45rem; color:#3B1C57; }
.mentor .tagline { color:#7B4397; font-weight:700; font-size:.85rem; letter-spacing:.3px; margin-bottom:6px; }
.mentor p { margin:6px 0; color:#2C2C2C; }
.mentor .day { display:flex; gap:12px; background:#fff; border-radius:14px; padding:10px 14px; margin:6px 0; border:1px solid #EADCF3; }
.mentor .day b { color:#7B4397; font-family:'Baloo 2',sans-serif; min-width:54px; }
.mentor .goal { background:#fff; border-left:6px solid #F2994A; border-radius:10px; padding:10px 14px; margin:10px 0; font-weight:600; }
.mentor .nb { background:#FFF4CC; border:1.5px solid #F2C94C; border-radius:12px; padding:8px 14px; display:inline-block; font-weight:700; }
.feat { background:#fff; border-radius:20px; padding:18px 20px; border:1px solid #F0E4F7; height:100%;
  box-shadow:0 6px 16px rgba(123,67,151,.10); }
.feat .em { font-size:2.2rem; line-height:1.1; }
.feat b { display:block; font-family:'Baloo 2',sans-serif; font-size:1.2rem; color:#3B1C57; margin:4px 0 2px 0; }
.feat span { color:#5E6368; font-size:.92rem; }
div[data-testid="stMetricValue"] { font-family:'Baloo 2',sans-serif; }
iframe { border-radius:22px; }
</style>
"""


_NEW_API = hasattr(st, "iframe")  # newer Streamlit: width="stretch", st.iframe


def stretch() -> dict:
    """Full-width kwargs that work on both old and new Streamlit."""
    return {"width": "stretch"} if _NEW_API else {"use_container_width": True}


def show_html(html: str, height: int, scrolling: bool = False):
    """Embed a self-contained HTML page (Three.js scenes, printable report)."""
    if _NEW_API:
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height, scrolling=scrolling)


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, sub: str = ""):
    st.markdown(f'<p class="page-title">{title}</p><p class="page-sub">{sub}</p>', unsafe_allow_html=True)


def mentor_html(plan: dict) -> str:
    """HTML card for a Personalised Mentor plan (see padho/mentor.py)."""
    from html import escape as e

    days = "".join(f'<div class="day"><b>{e(d)}</b><span>{e(t)}</span></div>' for d, t in plan["plan"])
    words = ""
    if plan["focus_words"]:
        words = "<p><b>Focus words:</b> " + "".join(
            f'<span class="chip chip-bad">{e(w)}</span>' for w in plan["focus_words"]) + "</p>"
    nb = f'<p><span class="nb">Next badge: {e(plan["next_badge"])} · {e(plan["next_badge_how"])}</span></p>' \
        if plan.get("next_badge") else ""
    return (f'<div class="mentor"><div class="tagline">🧑‍🏫 PERSONALISED MENTOR AI</div>'
            f'<h3>{e(plan["headline"])}</h3><p>{e(plan["diagnosis"])}</p>{words}'
            f'<div class="goal">🎯 {e(plan["goal"])}</div>'
            f'<p><b>3-day practice plan</b></p>{days}<p>💬 {e(plan["encouragement"])}</p>{nb}</div>')


def features_html() -> str:
    cols = "".join(
        f'<div class="feat"><div class="em">{f["emoji"]}</div><b>{f["name"]}</b><span>{f["text"]}</span></div>'
        for f in config.FEATURES)
    return ('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;'
            f'margin:6px 0 14px 0">{cols}</div>')


def tile(cls: str, val, cap: str) -> str:
    return f'<div class="tile {cls}"><b>{val}</b><span>{cap}</span></div>'


# ---------------------------------------------------------------- storage access
@st.cache_resource(show_spinner=False)
def get_store():
    """Supabase if configured and reachable, otherwise a local SQLite file."""
    url, key = config.get_secret("SUPABASE_URL"), config.get_secret("SUPABASE_KEY")
    note = ""
    if url and key:
        try:
            b = SupabaseBackend(url, key)
            b.select("students", columns=["id"], limit=1)  # connectivity + tables check
            return Store(b), ""
        except Exception as exc:
            note = f"Supabase is configured but failed: {exc}"
    return Store(SQLiteBackend("padho_local.db")), note


def store() -> Store:
    return get_store()[0]


def store_note() -> str:
    return get_store()[1]


# -------------------------------------------------------------------- photos
def process_photo(raw: bytes) -> str:
    """Centre-crop to a 160 px square JPEG and return base64 (about 6 KB)."""
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = ImageOps.fit(img, (160, 160), method=Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=78, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def initial_avatar(name: str) -> str:
    colors = ["#7B4397", "#F2994A", "#2193B0", "#11998E", "#EB3349", "#8E2DE2"]
    c = colors[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(colors)]
    ch = (name.strip()[:1] or "?").upper()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160"><rect width="160" height="160" '
           f'fill="{c}"/><text x="80" y="104" font-size="84" text-anchor="middle" fill="#fff" '
           f'font-family="sans-serif" font-weight="700">{ch}</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def photo_b64(student) -> str:
    """Base64 JPEG for a student ('' if none). Cached per browser session."""
    cache = st.session_state.setdefault("_photos", {})
    sid = student["id"]
    if sid not in cache:
        cache[sid] = store().photo(sid) or ""
    return cache[sid]


def photo_uri(student) -> str:
    b = photo_b64(student)
    return f"data:image/jpeg;base64,{b}" if b else initial_avatar(student["name"])


def forget_photo(sid):
    st.session_state.setdefault("_photos", {}).pop(sid, None)


# -------------------------------------------------------------- teacher login
def require_teacher() -> str:
    """Gate a page behind the school PIN. Returns the teacher's name."""
    if not config.TEACHER_PIN:
        return st.session_state.get("teacher_name", "Teacher")
    if st.session_state.get("teacher_ok"):
        return st.session_state.get("teacher_name", "Teacher")

    page_header("🔐 Teacher sign-in", "Enter your name and the school PIN to continue.")
    with st.form("login"):
        name = st.text_input("Your name", placeholder="Your name")
        pin = st.text_input("School PIN", type="password")
        if st.form_submit_button("Sign in", type="primary"):
            if hmac.compare_digest(pin.encode(), config.TEACHER_PIN.encode()):
                st.session_state.teacher_ok = True
                st.session_state.teacher_name = name.strip() or "Teacher"
                st.rerun()
            else:
                st.error("That PIN is not correct.")
    st.stop()


def student_label(s) -> str:
    sec = f" {s['section']}" if s.get("section") else ""
    return f"{s['name']} · {s['class_name']}{sec}"


def pick_student(key: str, allow_guest=False, label="Student"):
    """Selectbox of registered students. Returns the student dict, or None for guest/empty."""
    studs = store().students()
    if not studs and not allow_guest:
        st.info("No students registered yet. Use **Register student** first.")
        st.page_link("views/register.py", label="Go to registration", icon="📝")
        st.stop()
    ids = ([None] if allow_guest else []) + [s["id"] for s in studs]
    by_id = {s["id"]: s for s in studs}
    default = st.session_state.get("active_student")
    idx = ids.index(default) if default in ids else 0
    sid = st.selectbox(label, ids, index=idx, key=key,
                       format_func=lambda i: "👤 Guest (not saved)" if i is None else student_label(by_id[i]))
    st.session_state.active_student = sid
    return by_id.get(sid)


# ------------------------------------------------------------------- sidebar
def sidebar():
    with st.sidebar:
        st.markdown("### 📖 Padho!")
        st.caption(f"{config.SCHOOL_NAME}  \n{config.TEACHER_NAME}, {config.TEACHER_ROLE}")
        if config.TEACHER_PIN and st.session_state.get("teacher_ok"):
            st.success(f"Signed in: {st.session_state.get('teacher_name', 'Teacher')}")
            if st.button("Sign out", **stretch()):
                for k in ("teacher_ok", "teacher_name"):
                    st.session_state.pop(k, None)
                st.rerun()
        elif not config.TEACHER_PIN:
            st.warning("Open mode: set TEACHER_PIN in Secrets so only teachers can edit records.", icon="🔓")

        s, note = get_store()
        if s.b.permanent:
            st.success(f"Database: {s.b.label}", icon="✅")
        else:
            st.warning("Database: local test file. Data is **lost when the app restarts**. "
                       "Connect Supabase (see Admin page) before real use.", icon="⚠️")
        if note:
            st.error(note)
        st.caption("🎤 Bhashini connected" if asr.has_keys() else "🎤 Bhashini keys missing (Admin page)")
        st.divider()
        st.caption("Recordings are sent to Bhashini for transcription and are never stored by this app. "
                   "Only scores and the practice-word list are saved.")
