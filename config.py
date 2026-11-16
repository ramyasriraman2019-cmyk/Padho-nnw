"""Settings, languages and reading levels."""

import os
from datetime import timedelta, timezone

import streamlit as st


def get_secret(name: str, default: str = "") -> str:
    """Read from st.secrets first, then environment. Never from source code."""
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


SCHOOL_NAME = get_secret("SCHOOL_NAME", "Suthukeny Government High School")
TEACHER_PIN = get_secret("TEACHER_PIN")
TEACHER_NAME = get_secret("TEACHER_NAME", "K M Ramyasri")
TEACHER_ROLE = get_secret("TEACHER_ROLE", "Primary School Teacher (PST)")

IST = timezone(timedelta(hours=5, minutes=30))

LANGS = {
    "hi": {"label": "हिंदी · Hindi", "sr": "hi-IN"},
    "mr": {"label": "मराठी · Marathi", "sr": "mr-IN"},
    "ta": {"label": "தமிழ் · Tamil", "sr": "ta-IN"},
    "te": {"label": "తెలుగు · Telugu", "sr": "te-IN"},
    "bn": {"label": "বাংলা · Bengali", "sr": "bn-IN"},
    "gu": {"label": "ગુજરાતી · Gujarati", "sr": "gu-IN"},
    "en": {"label": "English", "sr": "en-IN"},
}

# Reference bands, NOT an examination standard.
# NIPUN Bharat aims for about 60 wpm by the end of Class 3 (= Level 3 here).
LEVELS = {
    1: {"name": "Sprout", "emoji": "🌱", "wpm": 30, "acc": 80, "color": "#38B26B",
        "desc": "Short, simple sentences"},
    2: {"name": "Explorer", "emoji": "🧭", "wpm": 45, "acc": 85, "color": "#2193B0",
        "desc": "A short paragraph read with understanding"},
    3: {"name": "Climber", "emoji": "🧗", "wpm": 60, "acc": 90, "color": "#F2994A",
        "desc": "NIPUN Bharat target: fluent reading with comprehension"},
    4: {"name": "Voyager", "emoji": "⛵", "wpm": 75, "acc": 92, "color": "#8E2DE2",
        "desc": "Longer text, smooth and expressive"},
    5: {"name": "Star Reader", "emoji": "🌟", "wpm": 90, "acc": 94, "color": "#E23D33",
        "desc": "A full story at near-adult pace"},
}
MAX_LEVEL = max(LEVELS)

# A "target reading" must also cover at least this much of the passage,
# so a child cannot qualify by racing through three words.
MIN_COVERAGE_FOR_TARGET = 80
# Target readings needed at the current level to be promoted.
MET_TO_PROMOTE = 3

CLASSES = ["Balvatika"] + [f"Class {i}" for i in range(1, 9)]

# How strictly a heard word must match the passage word to count as correct.
# Strict is the default: a changed vowel or sound is marked as misread.
STRICTNESS = {
    "Strict (recommended)": 1.0,
    "Standard": 0.90,
    "Lenient": 0.80,
}

# NIPUN Bharat (Ministry of Education) foundational-literacy target for oral reading:
# 45-60 words/min by the end of Class 2 and at least 60 words/min correctly, read with
# meaning, by the end of Class 3. Padho maps these to Level 2 and Level 3.
NIPUN_WPM = 60
NIPUN_ACC = LEVELS[3]["acc"]
NIPUN_SOURCE = "Ministry of Education, NIPUN Bharat Guidelines"

FEATURES = [
    {"emoji": "🎙️", "name": "Bhashini ASR",
     "short": "Govt. of India speech recognition",
     "text": "The Government of India's Bhashini speech recognition (MeitY, AI4Bharat models) listens to the child "
             "read aloud in 7 languages. It can also read the passage aloud first, word by word. Recordings are never stored."},
    {"emoji": "🇮🇳", "name": "NIPUN Bharat Standard",
     "short": "Ministry of Education reading goal",
     "text": "Targets follow the NIPUN Bharat reading-fluency goal: 45 to 60 words per minute by the end of "
             "Class 2 and at least 60 by the end of Class 3, read with meaning. Five levels climb toward it."},
    {"emoji": "📊", "name": "Student Performance Monitoring",
     "short": "Every reading tracked over time",
     "text": "Every reading is saved: words per minute, accuracy, difficult words, level progress and badges, "
             "with graphs for each child and a dashboard for the whole class."},
    {"emoji": "🧑‍🏫", "name": "Personalised Mentor AI",
     "short": "A personal practice plan for each child",
     "text": "Studies each child's own reading history, finds the pattern (slow, careless, tiring or ready to "
             "move up) and builds a personal 3-day practice plan, focus words and next goal."},
]
