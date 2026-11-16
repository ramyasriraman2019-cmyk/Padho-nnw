"""Motivation badges, streaks and level promotion. Pure logic, no Streamlit."""

from datetime import date, datetime, timedelta

from .config import IST, LEVELS, MAX_LEVEL, MET_TO_PROMOTE

CATEGORIES = {
    "effort": ("💪 Effort", "Earned by showing up and practising. Every child can earn these."),
    "skill": ("🎯 Skill", "Earned by reading accurately, fluently and with understanding."),
    "growth": ("📈 Growth", "Earned by getting better than before. Progress counts, not rank."),
    "level": ("🏔️ Levels", "One badge for every level of the reading mountain."),
}

BADGES = {
    "first_steps": {"emoji": "🌱", "name": "First Steps", "cat": "effort", "color": "#38B26B",
                    "how": "Complete your first reading."},
    "high_five": {"emoji": "✋", "name": "High Five", "cat": "effort", "color": "#F2994A",
                  "how": "Complete 5 readings."},
    "book_buddy": {"emoji": "📚", "name": "Book Buddy", "cat": "effort", "color": "#2193B0",
                   "how": "Complete 15 readings."},
    "streak3": {"emoji": "🔥", "name": "3-Day Streak", "cat": "effort", "color": "#E23D33",
                "how": "Read on 3 days in a row."},
    "streak7": {"emoji": "⚡", "name": "Week Warrior", "cat": "effort", "color": "#8E2DE2",
                "how": "Read on 7 days in a row."},
    "polyglot": {"emoji": "🌏", "name": "Polyglot", "cat": "effort", "color": "#11998E",
                 "how": "Read in two different languages."},
    "sharp_eyes": {"emoji": "🎯", "name": "Sharp Eyes", "cat": "skill", "color": "#2193B0",
                   "how": "Read with 90% accuracy or more (at least 80% of the passage)."},
    "perfect": {"emoji": "⭐", "name": "Perfect Read", "cat": "skill", "color": "#F2C94C",
                "how": "Read with 100% accuracy and reach the end of the passage."},
    "speed_star": {"emoji": "🚀", "name": "Speed Star", "cat": "skill", "color": "#EB3349",
                   "how": "Reach the speed target for your level."},
    "nipun": {"emoji": "🏆", "name": "Target Champion", "cat": "skill", "color": "#F2994A",
              "how": "Reach both the speed and accuracy targets in one reading."},
    "thinker": {"emoji": "🧠", "name": "Thinker", "cat": "skill", "color": "#7B4397",
                "how": "Answer all 3 questions your teacher asks after reading."},
    "personal_best": {"emoji": "📈", "name": "Personal Best", "cat": "growth", "color": "#11998E",
                      "how": "Beat your own best words-per-minute score."},
    "big_improver": {"emoji": "🧗", "name": "Big Improver", "cat": "growth", "color": "#F2994A",
                     "how": "Read 10 words per minute faster than your very first reading."},
    "comeback": {"emoji": "💪", "name": "Comeback Kid", "cat": "growth", "color": "#8E2DE2",
                 "how": "Return to reading after a break of a week or more."},
    "lvl2": {"emoji": "🧭", "name": "Explorer", "cat": "level", "color": "#2193B0",
             "how": "Reach Level 2."},
    "lvl3": {"emoji": "🧗", "name": "Climber", "cat": "level", "color": "#F2994A",
             "how": "Reach Level 3."},
    "lvl4": {"emoji": "⛵", "name": "Voyager", "cat": "level", "color": "#8E2DE2",
             "how": "Reach Level 4."},
    "lvl5": {"emoji": "🌟", "name": "Star Reader", "cat": "level", "color": "#E23D33",
             "how": "Reach Level 5, the top of the mountain."},
}


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts).astimezone(IST)


def local_date(ts: str) -> date:
    return parse_ts(ts).date()


def longest_streak(days) -> int:
    days = sorted(set(days))
    best = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        best = max(best, run)
        prev = d
    return best


def current_streak(days, today=None) -> int:
    """Consecutive reading days ending today or yesterday."""
    days = set(days)
    today = today or datetime.now(IST).date()
    d = today if today in days else today - timedelta(days=1)
    n = 0
    while d in days:
        n += 1
        d -= timedelta(days=1)
    return n


def met_count(attempts, level) -> int:
    return sum(1 for a in attempts if a["level"] == level and a["met"])


def promotion(student_level, attempts):
    """Return the level the student should now be on."""
    if student_level < MAX_LEVEL and met_count(attempts, student_level) >= MET_TO_PROMOTE:
        return student_level + 1
    return student_level


def evaluate(student_level, attempts, earned):
    """
    attempts: all of this student's attempts, oldest first (newest included).
    earned:   set of badge keys already held.
    Returns the list of badge keys newly deserved.
    """
    got = set()
    n = len(attempts)
    if n >= 1: got.add("first_steps")
    if n >= 5: got.add("high_five")
    if n >= 15: got.add("book_buddy")

    days = [local_date(a["ts"]) for a in attempts]
    run = longest_streak(days)
    if run >= 3: got.add("streak3")
    if run >= 7: got.add("streak7")
    if len({a["language"] for a in attempts}) >= 2: got.add("polyglot")

    for a in attempts:
        if a["accuracy"] >= 90 and a["coverage"] >= 80: got.add("sharp_eyes")
        if a["accuracy"] >= 99.5 and a["coverage"] >= 95: got.add("perfect")
        if a["wcpm"] >= LEVELS[a["level"]]["wpm"] and a["coverage"] >= 80: got.add("speed_star")
        if a["met"]: got.add("nipun")
        if a["comprehension"] == 3: got.add("thinker")

    if n >= 2 and attempts[-1]["wcpm"] > max(a["wcpm"] for a in attempts[:-1]):
        got.add("personal_best")
    if n >= 3 and max(a["wcpm"] for a in attempts) >= attempts[0]["wcpm"] + 10:
        got.add("big_improver")
    for prev, cur in zip(attempts, attempts[1:]):
        if (parse_ts(cur["ts"]) - parse_ts(prev["ts"])).days >= 7:
            got.add("comeback")

    for lv in range(2, MAX_LEVEL + 1):
        if student_level >= lv:
            got.add(f"lvl{lv}")

    return [k for k in BADGES if k in got and k not in earned]
