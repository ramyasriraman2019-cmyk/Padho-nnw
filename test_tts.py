import base64, io, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import soundfile as sf
from padho import asr, tts, listen


def _wav(seconds, sr=16000):
    buf = io.BytesIO()
    sf.write(buf, (0.2 * np.sin(2 * np.pi * 300 * np.arange(int(sr * seconds)) / sr)).astype("float32"), sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def test_split_text():
    t = "ஒரு சிறிய முயல் காட்டில் வாழ்ந்தது. அது எப்போதும் மகிழ்ச்சியாக ஓடி விளையாடும். அனைவரும் அதன் நண்பர்கள்."
    parts = tts.split_text(t, 60)
    assert len(parts) >= 2 and all(len(p) <= 90 for p in parts)
    assert " ".join(parts).replace("  ", " ") == t
    assert tts.split_text("सूरज चमक रहा है। चिड़िया गा रही है।", 200) == ["सूरज चमक रहा है। चिड़िया गा रही है।"]


def test_synthesize_joins_chunks(monkeypatch):
    calls = []

    def fake_post(url, headers, payload, timeout=20, _hop=0):
        calls.append(payload)
        if "pipelineRequestConfig" in payload:  # config request
            return {"pipelineResponseConfig": [{"config": [{"serviceId": "svc-tts"}]}],
                    "pipelineInferenceAPIEndPoint": {"callbackUrl": "https://x/cb",
                                                     "inferenceApiKey": {"name": "Authorization", "value": "tok"}}}
        text = payload["inputData"]["input"][0]["source"]
        return {"pipelineResponse": [{"audio": [{"audioContent": base64.b64encode(_wav(1.0)).decode()}]}]}

    monkeypatch.setattr(asr, "post_json", fake_post)
    text = "ஒரு சிறிய முயல் காட்டில் வாழ்ந்தது. " * 12  # forces several chunks
    b64 = tts.synthesize(text, "ta", "female", "pipe-test", "uid-test", "key-test")
    data, sr = sf.read(io.BytesIO(base64.b64decode(b64)))
    n_chunks = len(tts.split_text(text))
    assert n_chunks >= 2
    assert abs(len(data) / sr - n_chunks * 1.25) < 0.2  # 1 s per chunk + 0.25 s pause
    assert calls[0]["pipelineTasks"][0]["taskType"] == "tts"


def test_listen_html_is_safe_and_parses():
    html = listen.listen_html(["<b>x</b>", "பூக்கள்"], "<b>x</b> பூக்கள்", "", "ta-IN")
    assert "&lt;b&gt;x&lt;/b&gt;" in html and "<\\/b>" in html and "__PARAMS__" not in html
