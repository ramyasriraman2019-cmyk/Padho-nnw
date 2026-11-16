"""Scoring engine: align what the child said with the passage. No Streamlit here."""

import difflib
import re
import unicodedata

import numpy as np

PUNCT = re.compile(r"[।॥,.\?!;:\"'“”‘’()\-–—…]")


# Only differences that are recogniser spelling noise, never a child's pronunciation:
#   nukta dots (ज़ / ज), chandrabindu vs anusvara (ँ / ं), and a word-final virama
#   or pulli (சூரியன் / சூரியன), which recognisers write inconsistently.
_NUKTAS = dict.fromkeys(map(ord, "\u093c\u09bc\u0abc"))
_FINAL_VIRAMAS = "\u094d\u09cd\u0acd\u0bcd\u0c4d"
_ZERO_WIDTH = ("\u200d", "\u200c")


def normalise(word: str) -> str:
    w = unicodedata.normalize("NFC", word).lower().strip()
    w = PUNCT.sub("", w)
    for z in _ZERO_WIDTH:
        w = w.replace(z, "")
    w = w.translate(_NUKTAS).replace("\u0901", "\u0902")
    return w.rstrip(_FINAL_VIRAMAS) or w


def tokenise(text: str):
    """Return (display tokens, normalised tokens), index-aligned."""
    raw = [t for t in re.split(r"\s+", text.strip()) if t]
    disp, norm = [], []
    for t in raw:
        n = normalise(t)
        if n:
            disp.append(t)
            norm.append(n)
    return disp, norm


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def score_reading(ref_norm, hyp_norm, ok_ratio=1.0):
    """
    ok_ratio: how alike a heard word must be to the passage word to count as
    correct. 1.0 = must match exactly (after the harmless clean-up in normalise).
    Lower values forgive more, but then real mispronunciations slip through.

    status per passage word:
      ok   = read correctly       bad  = misread
      skip = jumped over          wait = never reached (excluded from accuracy)
    """
    status = ["wait"] * len(ref_norm)
    extra = 0
    matcher = difflib.SequenceMatcher(None, ref_norm, hyp_norm, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                status[i] = "ok"
        elif tag == "delete":
            for i in range(i1, i2):
                status[i] = "skip"
        elif tag == "insert":
            extra += j2 - j1
        elif tag == "replace":
            for k, i in enumerate(range(i1, i2)):
                j = j1 + k
                if j < j2:
                    r = ratio(ref_norm[i], hyp_norm[j])
                    status[i] = "ok" if r >= ok_ratio else ("bad" if r >= 0.55 else "skip")
                else:
                    status[i] = "skip"
            extra += max(0, (j2 - j1) - (i2 - i1))

    reached = max((i for i, s in enumerate(status) if s in ("ok", "bad")), default=-1)
    for i in range(reached + 1, len(status)):
        status[i] = "wait"

    return {
        "status": status,
        "attempted": reached + 1,
        "correct": status.count("ok"),
        "misread": status.count("bad"),
        "skipped": status.count("skip"),
        "extra": extra,
    }


def trim_silence(y, sr=16000, frame_ms=30, pad_ms=250):
    """
    Cut quiet time before the child starts and after they finish, so WCPM
    measures reading time, not how long the teacher took to press the buttons.
    """
    n = int(sr * frame_ms / 1000)
    if len(y) < n * 4:
        return y
    frames = len(y) // n
    rms = np.sqrt((y[: frames * n].reshape(frames, n) ** 2).mean(axis=1))
    thr = max(0.008, 0.08 * float(np.percentile(rms, 95)))
    idx = np.where(rms > thr)[0]
    if len(idx) == 0:
        return y
    pad = int(pad_ms / frame_ms)
    a = max(0, int(idx[0]) - pad)
    b = min(frames, int(idx[-1]) + 1 + pad)
    return y[a * n : b * n]


def compute_metrics(res, ref_len, duration_s):
    minutes = duration_s / 60.0
    wcpm = res["correct"] / minutes if minutes > 0 else 0.0
    accuracy = 100 * res["correct"] / res["attempted"] if res["attempted"] else 0.0
    coverage = 100 * res["attempted"] / ref_len if ref_len else 0.0
    return wcpm, accuracy, coverage


def verdict_for(wcpm, accuracy, target_wpm, target_acc):
    hit_speed = wcpm >= target_wpm
    hit_acc = accuracy >= target_acc
    if hit_speed and hit_acc:
        return "v-gold", "🏆 Target reached!", "Speed and accuracy are both on target. Wonderful reading."
    if hit_acc and not hit_speed:
        return "v-good", "🎯 Accurate, now build speed", "Very few mistakes. Keep re-reading the same passage until it flows faster."
    if hit_speed and not hit_acc:
        return "v-mid", "⚡ Fast, now slow down a little", "Good pace, but words are being missed. Accuracy matters more than speed."
    if wcpm >= target_wpm * 0.6:
        return "v-mid", "🌱 Getting there", "Steady progress. A few minutes of daily reading aloud will close the gap."
    return "v-low", "📚 Needs practice", "Read this passage together first, then let the child try alone."
