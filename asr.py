"""Audio decoding and Bhashini speech recognition."""

import base64
import io
from urllib.parse import urljoin

import numpy as np
import requests
import streamlit as st

from .config import get_secret

CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
DEFAULT_PIPELINE = "64392f96daac500b55c543cd"


def creds():
    return get_secret("BHASHINI_USER_ID"), get_secret("BHASHINI_API_KEY")


def has_keys() -> bool:
    uid, key = creds()
    return bool(uid and key)


def pipeline_id() -> str:
    return get_secret("BHASHINI_PIPELINE_ID", DEFAULT_PIPELINE)


def post_json(url, headers, payload, timeout=20, _hop=0):
    """POST and raise errors that CONTAIN Bhashini's own message. Redirects are
    followed by hand so a 302 is never replayed as a GET."""
    r = requests.post(url, headers=headers, json=payload, timeout=timeout, allow_redirects=False)
    if r.status_code in (301, 302, 303, 307, 308) and _hop < 3:
        target = r.headers.get("Location")
        if target:
            return post_json(urljoin(url, target), headers, payload, timeout, _hop + 1)
    if r.status_code >= 400:
        body = (r.text or "").strip()[:500] or "(empty response body)"
        raise RuntimeError(f"HTTP {r.status_code} — {body}")
    try:
        return r.json()
    except Exception:
        raise RuntimeError(f"Bhashini returned non-JSON: {r.text[:300]}")


def decode_audio(raw: bytes):
    """Return mono float32 samples at 16 kHz. soundfile first, then ffmpeg via pydub."""
    try:
        import soundfile as sf
        from scipy.signal import resample_poly

        data, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
        y = data.mean(axis=1)
        if sr != 16000:
            g = np.gcd(int(sr), 16000)
            y = resample_poly(y, 16000 // g, int(sr) // g)
        return y.astype("float32")
    except Exception:
        pass
    try:
        from pydub import AudioSegment

        seg = AudioSegment.from_file(io.BytesIO(raw))
        seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        return np.array(seg.get_array_of_samples(), dtype="float32") / 32768.0
    except Exception as exc:
        raise RuntimeError(f"Could not read the recording: {exc}")


def to_wav_b64(samples: np.ndarray) -> str:
    import soundfile as sf

    buf = io.BytesIO()
    sf.write(buf, samples, 16000, format="WAV", subtype="PCM_16")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@st.cache_data(ttl=3000, show_spinner=False)
def pipeline_config(lang_code: str, pid: str, uid: str, key: str):
    headers = {"Content-Type": "application/json", "userID": uid, "ulcaApiKey": key}
    payload = {
        "pipelineTasks": [{"taskType": "asr", "config": {"language": {"sourceLanguage": lang_code}}}],
        "pipelineRequestConfig": {"pipelineId": pid},
    }
    cfg = post_json(CONFIG_URL, headers, payload, timeout=20)
    try:
        pipe = cfg["pipelineResponseConfig"][0]["config"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected reply shape: {str(cfg)[:300]}")
    if not pipe:
        raise RuntimeError(f"This pipeline has no ASR model for language '{lang_code}'.")
    ep = cfg["pipelineInferenceAPIEndPoint"]
    return {
        "service_id": pipe[0]["serviceId"],
        "callback_url": ep["callbackUrl"],
        "auth_name": ep["inferenceApiKey"]["name"],
        "auth_value": ep["inferenceApiKey"]["value"],
    }


def test_connection(lang_code: str):
    uid, key = creds()
    return pipeline_config(lang_code, pipeline_id(), uid, key)


def transcribe_bhashini(samples, lang_code):
    uid, key = creds()
    cfg = pipeline_config(lang_code, pipeline_id(), uid, key)
    headers = {"Content-Type": "application/json", cfg["auth_name"]: cfg["auth_value"]}
    payload = {
        "pipelineTasks": [{
            "taskType": "asr",
            "config": {
                "language": {"sourceLanguage": lang_code},
                "serviceId": cfg["service_id"],
                "audioFormat": "wav",
                "samplingRate": 16000,
            },
        }],
        "inputData": {"audio": [{"audioContent": to_wav_b64(samples)}]},
    }
    out = post_json(cfg["callback_url"], headers, payload, timeout=90)
    try:
        text = out["pipelineResponse"][0]["output"][0]["source"]
    except (KeyError, IndexError):
        raise RuntimeError(f"No transcript in reply: {str(out)[:300]}")
    return text.strip(), "Bhashini ASR (MeitY / AI4Bharat, Govt. of India)"


def transcribe_fallback(samples, sr_code):
    """Optional backup. NOTE: this sends the audio to Google, so it is OFF by default."""
    try:
        import soundfile as sf
        import speech_recognition as sr_lib
    except ImportError:
        raise RuntimeError("SpeechRecognition is not installed")
    buf = io.BytesIO()
    sf.write(buf, samples, 16000, format="WAV", subtype="PCM_16")
    buf.seek(0)
    rec = sr_lib.Recognizer()
    with sr_lib.AudioFile(buf) as src:
        audio = rec.record(src)
    try:
        text = rec.recognize_google(audio, language=sr_code)
    except sr_lib.UnknownValueError:
        raise RuntimeError("could not make out any speech in the recording")
    except sr_lib.RequestError as exc:
        raise RuntimeError(f"backup service unreachable ({exc})")
    return text.strip(), "Backup recogniser (Google, not Bhashini)"


def transcribe(samples, lang_code, sr_code, allow_backup):
    errors = []
    if has_keys():
        try:
            return transcribe_bhashini(samples, lang_code)
        except Exception as exc:
            errors.append(f"Bhashini: {exc}")
    else:
        errors.append("Bhashini keys are not set in Secrets")
    if allow_backup:
        try:
            return transcribe_fallback(samples, sr_code)
        except Exception as exc:
            errors.append(f"Backup: {exc}")
    raise RuntimeError("  •  ".join(errors))
