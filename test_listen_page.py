"""Read page with the 'read aloud first' toggle on: device voice and (stubbed) Bhashini voice."""
import base64, io, os, shutil, sys, tempfile
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import soundfile as sf
from streamlit.testing.v1 import AppTest

tmp = tempfile.mkdtemp(); shutil.copytree(ROOT, tmp + "/app", ignore=shutil.ignore_patterns("*.db", "__pycache__"))
os.chdir(tmp + "/app"); sys.path.insert(0, tmp + "/app")

buf = io.BytesIO(); sf.write(buf, (0.2*np.sin(np.arange(16000)/20)).astype("float32"), 16000, format="WAV", subtype="PCM_16")
WAV = base64.b64encode(buf.getvalue()).decode()

def run(stub_keys):
    script = '''
import runpy, streamlit as st
from padho import asr, tts
st.page_link = lambda *a, **k: None
%s
runpy.run_path("views/read.py")
''' % ("asr.has_keys = lambda: True\ntts.speak = lambda *a, **k: %r" % WAV if stub_keys else "asr.has_keys = lambda: False")
    at = AppTest.from_string(script, default_timeout=60).run()
    assert not at.exception, at.exception
    tg = [t for t in at.toggle if "read this passage aloud" in t.label][0]
    tg.set_value(True).run()
    assert not at.exception, at.exception
    return at

at = run(False)
print("device voice only: ok; radio options:", [r.options for r in at.radio if r.key == "voice_mode"])
at = run(True)
print("with Bhashini voice: ok; radio options:", [r.options for r in at.radio if r.key == "voice_mode"])
print("LISTEN PAGE OK")
