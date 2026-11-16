"""Bhashini text-to-speech: the app reads a passage aloud before the child tries."""

import base64
import io
import re

import numpy as np
import streamlit as st

from . import asr

MAX_CHARS = 200  # per request; long passages are sent as sentence groups and joined


def split_text(text: str, limit: int = MAX_CHARS):
    """Group sentences into chunks of at most `limit` characters."""
    sentences = [s.strip() for s in re.findall(r"[^।॥.!?]+[।॥.!?]*", text) if s.strip()]
    chunks, cur = [], ""
    for s in sentences:
        if cur and len(cur) + 1 + len(s) > limit:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    # a single very long sentence: cut at spaces
    out = []
    for c in chunks:
        while len(c) > limit * 1.5:
            cut = c.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            out.append(c[:cut].strip())
            c = c[cut:].strip()
        out.append(c)
    return out


@st.cache_data(ttl=3000, show_spinner=False)
def _service(lang_code: str, gender: str, pid: str, uid: str, key: str):
    headers = {"Content-Type": "application/json", "userID": uid, "ulcaApiKey": key}
    payload = {
        "pipelineTasks": [{"taskType": "tts", "config": {"language": {"sourceLanguage": lang_code},
                                                          "gender": gender}}],
        "pipelineRequestConfig": {"pipelineId": pid},
    }
    cfg = asr.post_json(asr.CONFIG_URL, headers, payload, timeout=20)
    try:
        pipe = cfg["pipelineResponseConfig"][0]["config"]
        ep = cfg["pipelineInferenceAPIEndPoint"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected reply shape: {str(cfg)[:300]}")
    if not pipe:
        raise RuntimeError(f"No Bhashini voice for language '{lang_code}' on this pipeline.")
    return {"service_id": pipe[0]["serviceId"], "url": ep["callbackUrl"],
            "auth_name": ep["inferenceApiKey"]["name"], "auth_value": ep["inferenceApiKey"]["value"]}


def test_voice(lang_code: str, gender: str = "female"):
    uid, key = asr.creds()
    return _service(lang_code, gender, asr.pipeline_id(), uid, key)


def _speak_chunk(cfg, text, lang_code, gender):
    headers = {"Content-Type": "application/json", cfg["auth_name"]: cfg["auth_value"]}
    payload = {
        "pipelineTasks": [{"taskType": "tts", "config": {"language": {"sourceLanguage": lang_code},
                                                          "serviceId": cfg["service_id"], "gender": gender}}],
        "inputData": {"input": [{"source": text}]},
    }
    out = asr.post_json(cfg["url"], headers, payload, timeout=90)
    try:
        return base64.b64decode(out["pipelineResponse"][0]["audio"][0]["audioContent"])
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"No audio in reply: {str(out)[:300]}")


def _join_wavs(parts):
    import soundfile as sf

    arrays, sr0 = [], None
    for raw in parts:
        data, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
        data = data.mean(axis=1)
        if sr0 is None:
            sr0 = sr
        elif sr != sr0:
            from scipy.signal import resample_poly
            g = int(np.gcd(int(sr), int(sr0)))
            data = resample_poly(data, int(sr0) // g, int(sr) // g)
        arrays.append(data)
        arrays.append(np.zeros(int(sr0 * 0.25), dtype="float32"))  # short pause between sentences
    buf = io.BytesIO()
    sf.write(buf, np.concatenate(arrays), sr0, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@st.cache_data(ttl=86400, show_spinner=False, max_entries=300)
def synthesize(text: str, lang_code: str, gender: str, pid: str, uid: str, key: str) -> str:
    """Return the spoken passage as base64 WAV. Cached, so each passage is generated once."""
    cfg = _service(lang_code, gender, pid, uid, key)
    parts = [_speak_chunk(cfg, c, lang_code, gender) for c in split_text(text)]
    if not parts:
        raise RuntimeError("Nothing to read")
    wav = parts[0] if len(parts) == 1 else _join_wavs(parts)
    return base64.b64encode(wav).decode()


def speak(text: str, lang_code: str, gender: str = "female") -> str:
    uid, key = asr.creds()
    if not (uid and key):
        raise RuntimeError("Bhashini keys are not set")
    return synthesize(text, lang_code, gender, asr.pipeline_id(), uid, key)
