"""Run every page headlessly against a seeded temporary database."""
import json, os, shutil, sys, tempfile
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest
from padho import storage, badges

PAGES = ["views/home.py", "views/badges_page.py", "views/register.py", "views/read.py", "views/profile.py", "views/mentor.py",
         "views/report_page.py", "views/dashboard.py", "views/admin.py"]

def seed(db):
    st = storage.Store(storage.SQLiteBackend(db))
    a = st.add_student(name="Asha Devi", class_name="Class 3", section="A", roll="1", language="ta", level=2, consent=1, photo=None)
    b = st.add_student(name="Ravi Kumar", class_name="Class 4", section="B", roll="2", language="hi", level=1, consent=1)
    base = datetime.now(timezone.utc) - timedelta(days=6)
    for i, w in enumerate([18, 24, 31, 38, 44, 52]):
        st.b.insert("attempts", {"id": f"x{i}", "student_id": a, "ts": (base + timedelta(days=i)).isoformat(timespec="seconds"),
            "language": "ta", "level": 1 if i < 4 else 2, "wcpm": w, "accuracy": 80 + i * 3, "coverage": 100, "correct": 20, "misread": 2,
            "skipped": 1, "extra": 0, "duration": 30, "comprehension": 3 if i == 5 else -1, "met": 1 if w >= 30 else 0,
            "bad_words": json.dumps(["பூக்கள்", "பறக்கிறது"], ensure_ascii=False), "skip_words": "[]"})
    atts = st.attempts(a)
    for k in badges.evaluate(2, atts, set()):
        st.award(a, k)
    return a, b

APP = None
def main():
    global APP
    tmp = tempfile.mkdtemp()
    shutil.copytree(ROOT, tmp + "/app", ignore=shutil.ignore_patterns("*.db", "__pycache__", ".git"))
    os.chdir(tmp + "/app"); APP = tmp + "/app/app.py"
    a, b = seed("padho_local.db")
    bad = 0
    for p in PAGES:
        at = AppTest.from_file(APP, default_timeout=60)
        at.session_state["active_student"] = a
        at.run()
        at.switch_page(p).run()
        errs = [e.value for e in at.exception]
        print(("FAIL " if errs else "ok   ") + p, errs[:1])
        bad += bool(errs)
    # profile for a student with no readings
    at = AppTest.from_file(APP, default_timeout=60); at.session_state["active_student"] = b; at.run()
    for p in ("views/profile.py", "views/mentor.py", "views/report_page.py"):
        at.switch_page(p).run(); errs = [e.value for e in at.exception]
        print(("FAIL " if errs else "ok   ") + p + " (no readings)", errs[:1]); bad += bool(errs)
    sys.exit(1 if bad else 0)
main()
