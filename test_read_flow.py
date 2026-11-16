"""Simulate recording + recognition on the Read page: scoring, saving, badges, level-up."""
import os, shutil, sys, tempfile
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from streamlit.testing.v1 import AppTest
from padho import storage

tmp = tempfile.mkdtemp(); shutil.copytree(ROOT, tmp + "/app", ignore=shutil.ignore_patterns("*.db", "__pycache__"))
os.chdir(tmp + "/app"); sys.path.insert(0, tmp + "/app")
st_ = storage.Store(storage.SQLiteBackend("padho_local.db"))
sid = st_.add_student(name="Meena", class_name="Class 3", section="A", roll="3", language="en", level=1, consent=1)

SCRIPT = '''
import runpy, io, streamlit as st, numpy as np
from padho import asr
class Fake:
    def getvalue(self): return b"x"
st.audio_input = lambda *a, **k: Fake()
st.page_link = lambda *a, **k: None
asr.decode_audio = lambda raw: (0.3*np.sin(2*np.pi*220*np.arange(16000*12)/16000)).astype("float32")
PASSAGE = "The sun is up in the sky. Little birds are singing in the green tree. Children run and play."
asr.transcribe = lambda samples, lang, sr, backup: (PASSAGE, "stub")
st.session_state["active_student"] = "%s"
runpy.run_path("views/read.py")
''' % sid

for i in range(1, 4):
    at = AppTest.from_string(SCRIPT, default_timeout=60).run()
    assert not at.exception, at.exception
    btn = [b for b in at.button if "Check the reading" in b.label][0]
    btn.click().run()
    assert not at.exception, at.exception
    atts = st_.attempts(sid); stud = st_.student(sid)
    print(f"reading {i}: attempts={len(atts)} wcpm={atts[-1]['wcpm']} acc={atts[-1]['accuracy']} met={atts[-1]['met']} level={stud['level']} badges={sorted(b['badge_key'] for b in st_.badges(sid))}")
assert st_.student(sid)["level"] == 2, "should be promoted after 3 target readings"
assert {"first_steps", "nipun", "lvl2"} <= {b["badge_key"] for b in st_.badges(sid)}
print("READ FLOW OK")
