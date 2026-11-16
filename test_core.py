import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from padho import badges, mentor, scoring, storage  # noqa: E402
from padho.passages import PASSAGES  # noqa: E402


def test_passage_bank_complete():
    assert set(PASSAGES) == {"hi", "mr", "ta", "te", "bn", "gu", "en"}
    for lang, book in PASSAGES.items():
        assert sorted(book) == [1, 2, 3, 4, 5], lang
        lens = [len(scoring.tokenise(book[i])[1]) for i in range(1, 6)]
        assert lens == sorted(lens), (lang, lens)  # passages get longer with level


def test_scoring_perfect_and_partial():
    ref_d, ref = scoring.tokenise("the sun is up in the sky")
    r = scoring.score_reading(ref, ref)
    assert r["correct"] == 7 and r["attempted"] == 7
    # child stops after 4 words: rest is "wait", not "skip"
    _, hyp = scoring.tokenise("the sun is up")
    r = scoring.score_reading(ref, hyp)
    assert r["correct"] == 4 and r["skipped"] == 0 and r["attempted"] == 4
    # skipped middle word
    _, hyp = scoring.tokenise("the sun up in the sky")
    r = scoring.score_reading(ref, hyp)
    assert r["skipped"] == 1 and r["correct"] == 6


def test_scoring_misread_and_hindi_matra():
    _, ref = scoring.tokenise("he can run fast")
    _, hyp = scoring.tokenise("he can ran fast")
    r = scoring.score_reading(ref, hyp)
    assert r["misread"] == 1
    _, ref = scoring.tokenise("बच्चे मैदान में खेल रहे हैं।")
    _, hyp = scoring.tokenise("बच्चे मैदान में खेल रहे है")  # dropped matra: forgiven
    assert scoring.score_reading(ref, hyp, 0.80)["correct"] == 6  # lenient mode forgives it
    assert scoring.score_reading(ref, hyp)["correct"] == 5         # strict mode does not


def test_strict_catches_mispronunciation():
    for good, said in [("sooriyan", "sariyan"), ("சூரியன்", "சரியன்"), ("सूरज", "सरज"), ("birds", "burds")]:
        _, ref = scoring.tokenise(f"the {good} shines")
        _, hyp = scoring.tokenise(f"the {said} shines")
        r = scoring.score_reading(ref, hyp)
        assert r["correct"] == 2 and r["misread"] == 1, (good, said, r)


def test_strict_forgives_only_recogniser_noise():
    for good, said in [("सूरज़", "सूरज"), ("சூரியன்", "சூரியன"), ("मंच", "मँच")]:
        _, ref = scoring.tokenise(good)
        _, hyp = scoring.tokenise(said)
        assert scoring.score_reading(ref, hyp)["correct"] == 1, (good, said)


def test_metrics():
    res = {"correct": 30, "attempted": 33}
    wcpm, acc, cov = scoring.compute_metrics(res, 40, 30.0)
    assert round(wcpm) == 60 and round(acc) == 91 and round(cov) == 82


def test_trim_silence():
    sr = 16000
    y = np.zeros(sr * 10, dtype="float32")
    t = np.arange(sr * 3) / sr
    y[sr * 4 : sr * 7] = 0.3 * np.sin(2 * np.pi * 220 * t)
    out = scoring.trim_silence(y)
    assert 3.0 < len(out) / sr < 4.2


def test_storage_roundtrip(tmp_path):
    st = storage.Store(storage.SQLiteBackend(str(tmp_path / "t.db")))
    sid = st.add_student(name="Asha", class_name="Class 3", section="A", roll="7", language="ta", photo="abc", consent=1)
    assert st.students()[0]["name"] == "Asha"
    assert "photo" not in st.students()[0]
    assert st.photo(sid) == "abc"
    st.add_attempt(student_id=sid, language="ta", level=1, wcpm=40.0, accuracy=90.0, coverage=100.0, correct=20,
                   misread=1, skipped=1, extra=0, duration=30.0, comprehension=-1, met=1, bad_words="[]", skip_words="[]")
    st.award(sid, "first_steps")
    st.award(sid, "first_steps")  # duplicate must be ignored
    assert len(st.badges(sid)) == 1
    dump = st.dump()
    st2 = storage.Store(storage.SQLiteBackend(str(tmp_path / "t2.db")))
    assert st2.restore(dump) == {"students": 1, "attempts": 1, "badges": 1}
    assert st2.restore(dump)["students"] == 1  # idempotent
    assert len(st2.attempts(sid)) == 1
    st.delete_student(sid)
    assert st.students() == [] and st.attempts() == [] and st.badges() == []


def _att(day_offset, wcpm, acc=92, cov=100, level=1, met=0, lang="hi", comp=-1, base=None):
    base = base or datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    return {"ts": (base + timedelta(days=day_offset)).isoformat(), "wcpm": wcpm, "accuracy": acc,
            "coverage": cov, "level": level, "met": met, "language": lang, "comprehension": comp}


def test_badges_and_streaks():
    a = [_att(0, 20), _att(1, 28), _att(2, 35)]
    got = badges.evaluate(1, a, set())
    assert {"first_steps", "streak3", "sharp_eyes", "personal_best", "big_improver"} <= set(got)
    assert "high_five" not in got
    assert badges.evaluate(1, a, {"first_steps"}).count("first_steps") == 0
    assert "comeback" in badges.evaluate(1, [_att(0, 20), _att(9, 25)], set())
    assert "polyglot" in badges.evaluate(1, [_att(0, 20), _att(1, 22, lang="en")], set())
    assert "thinker" in badges.evaluate(1, [_att(0, 20, comp=3)], set())
    assert "lvl3" in badges.evaluate(3, [_att(0, 20)], set())
    assert badges.longest_streak([datetime(2026, 11, d).date() for d in (1, 2, 3, 5)]) == 3


def test_promotion():
    a = [_att(i, 40, level=1, met=1) for i in range(3)]
    assert badges.promotion(1, a) == 2
    assert badges.promotion(1, a[:2]) == 1
    assert badges.promotion(5, [_att(i, 99, level=5, met=1) for i in range(5)]) == 5


def _full(day, w, acc=92, cov=100, level=2, met=0, bad=()):
    import json as _j
    a = _att(day, w, acc, cov, level, met)
    a.update({"bad_words": _j.dumps(list(bad), ensure_ascii=False), "skip_words": "[]"})
    return a


STUD = {"name": "Asha Devi", "level": 2}


def test_mentor_patterns():
    assert mentor.build(STUD, [], set())["pattern"] == "new"
    assert mentor.build(STUD, [_full(i, 30, 95) for i in range(3)], set())["pattern"] == "accurate_slow"  # target 45/85
    assert mentor.build(STUD, [_full(i, 60, 70) for i in range(3)], set())["pattern"] == "fast_careless"
    assert mentor.build(STUD, [_full(i, 60, 95) for i in range(3)], set())["pattern"] == "on_target"
    assert mentor.build(STUD, [_full(i, 20, 60) for i in range(3)], set())["pattern"] == "building"
    assert mentor.build(STUD, [_full(i, 30, 95, cov=50) for i in range(3)], set())["pattern"] == "stamina"


def test_mentor_focus_words_and_badge_hint():
    a = [_full(0, 30, 80, bad=["பூக்கள்"]), _full(1, 33, 82, bad=["பூக்கள்", "பறவை"])]
    p = mentor.build(STUD, a, {"first_steps"})
    assert p["focus_words"][0] == "பூக்கள்" and "பூக்கள்" in p["persistent_words"]
    assert len(p["plan"]) >= 3 and p["next_badge"] and "High Five" in p["next_badge"]
