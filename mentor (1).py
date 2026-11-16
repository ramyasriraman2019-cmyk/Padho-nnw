"""
Personalised Mentor: turns one child's reading history into a personal practice plan.

It is data-driven and rule-based (no outside AI service, no data leaves the app):
it reads the child's speed, accuracy, how much of each passage they finish,
their difficult words and their badge progress, picks the pattern that fits,
and writes advice for the teacher and parents. It supports the teacher; it does
not replace her.
"""

import json
from collections import Counter

from .badges import BADGES, current_streak, local_date
from .config import LEVELS, MAX_LEVEL, MET_TO_PROMOTE


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def next_badge_hint(attempts, earned):
    """The closest badge the child can win next, as a short sentence."""
    n = len(attempts)
    streak = current_streak([local_date(a["ts"]) for a in attempts])
    if "first_steps" not in earned:
        return "🌱 First Steps", "Complete one reading to earn it."
    if "high_five" not in earned:
        left = 5 - n
        return "✋ High Five", f"{left} more reading{'s' if left != 1 else ''} to go."
    if "streak3" not in earned:
        left = max(1, 3 - streak)
        return "🔥 3-Day Streak", f"Read on {left} more day{'s' if left != 1 else ''} in a row."
    if "book_buddy" not in earned:
        left = 15 - n
        return "📚 Book Buddy", f"{left} more reading{'s' if left != 1 else ''} to go."
    for key, b in BADGES.items():
        if key not in earned and b["cat"] != "level":
            return f"{b['emoji']} {b['name']}", b["how"]
    return None, ""


def build(student, attempts, earned):
    """Return a plan dict. `earned` is a set of badge keys."""
    name = (student["name"].split() or ["The student"])[0]
    lvl = student["level"]
    lv = LEVELS[lvl]
    n = len(attempts)
    badge, badge_how = next_badge_hint(attempts, earned)

    if n == 0:
        return {
            "has_data": False, "name": name, "pattern": "new", "headline": f"Welcome, {name}! Let us begin.",
            "diagnosis": f"{name} has not read yet. The first reading shows where to start.",
            "focus_words": [], "goal": f"First goal: finish the Level {lvl} passage once.",
            "plan": [("Day 1", f"Read the passage aloud together, taking turns sentence by sentence."),
                     ("Day 2", "Let the child read alone while you listen without correcting."),
                     ("Day 3", "Record the reading in Padho and look at the colours together.")],
            "next_badge": badge, "next_badge_how": badge_how, "stats": {}, "trend": "new",
            "persistent_words": [],
            "encouragement": f"Every child starts with one reading. Celebrate the first attempt, whatever the score.",
        }

    recent = attempts[-3:]
    w, a, cov = (_mean(x[k] for x in recent) for k in ("wcpm", "accuracy", "coverage"))
    gap_w, gap_a = lv["wpm"] - w, lv["acc"] - a

    # --- the pattern -------------------------------------------------------
    if cov < 80:
        pattern = "stamina"
    elif w >= lv["wpm"] and a >= lv["acc"]:
        pattern = "on_target"
    elif a >= lv["acc"]:
        pattern = "accurate_slow"
    elif w >= lv["wpm"]:
        pattern = "fast_careless"
    else:
        pattern = "building"

    # --- trend ---------------------------------------------------------------
    trend, change = "new", 0.0
    if n >= 2:
        early = _mean(x["wcpm"] for x in attempts[: min(3, n // 2 or 1)])
        change = w - early
        trend = "up" if change >= 3 else "down" if change <= -3 else "flat"

    # --- difficult words (last 8 readings); persistent = missed more than once ---
    miss = Counter()
    for x in attempts[-8:]:
        miss.update(json.loads(x["bad_words"] or "[]") + json.loads(x["skip_words"] or "[]"))
    focus = [wd for wd, _ in miss.most_common(6)]
    persistent = [wd for wd, c in miss.items() if c >= 2]

    step = int(round(min(max(gap_w, 0), 8)))
    if gap_w > 0:
        step = max(step, 2)  # always a real, visible next step
    near = 0 < gap_w < 3  # just under the target
    goal_w = int(round(w + step))
    if pattern == "on_target":
        goal = (f"Keep reaching {lv['wpm']} words/min with {lv['acc']}% accuracy. "
                + (f"{max(MET_TO_PROMOTE - sum(1 for x in attempts if x['level'] == lvl and x['met']), 0)} more "
                   f"target reading(s) will move {name} up to Level {lvl + 1}." if lvl < MAX_LEVEL
                   else "That is the top level. Now read for expression."))
    elif pattern == "stamina":
        goal = f"Reach the end of the passage. Aim to finish at least 80% (now about {cov:.0f}%)."
    elif pattern == "fast_careless":
        goal = f"Raise accuracy from {a:.0f}% to {lv['acc']}% while keeping the same pace."
    else:
        goal = (f"Next small step: about {min(goal_w, lv['wpm'])} words/min (now {w:.0f}). "
                f"The Level {lvl} target is {lv['wpm']}.")

    headlines = {
        "stamina": f"{name} runs out of steam before the end",
        "on_target": f"{name} is on target. Time to stretch!",
        "accurate_slow": f"{name} reads carefully. Speed is the next step",
        "fast_careless": f"{name} reads fast. Slow down for accuracy",
        "building": f"{name} is building skill step by step",
    }
    diagnosis = {
        "stamina": f"On average {name} reaches only about {cov:.0f}% of the passage. Long passages tire or worry the "
                   f"child, so practise in short chunks first.",
        "on_target": f"Speed ({w:.0f} words/min) and accuracy ({a:.0f}%) both meet the Level {lvl} reference.",
        "accurate_slow": (f"Accuracy is good ({a:.0f}%) and speed is just under the target ({w:.1f} against {lv['wpm']} "
                          f"words/min). Very close! Smoothness comes from re-reading." if near else
                          f"Accuracy is good ({a:.0f}%) but speed is {w:.0f} words/min against a target of "
                          f"{lv['wpm']}. The child decodes well and needs smoothness, which comes from re-reading."),
        "fast_careless": f"Speed is on target ({w:.0f} words/min) but accuracy is {a:.0f}% against {lv['acc']}%. "
                         f"Words are being guessed or skipped.",
        "building": f"Speed ({w:.0f} words/min) and accuracy ({a:.0f}%) are both below the Level {lvl} reference. "
                    f"This is normal at the start of a level. Short daily practice closes the gap.",
    }[pattern]
    if trend == "up":
        diagnosis += f" Good news: speed is up about {change:.0f} words/min since the early readings."
    elif trend == "down":
        diagnosis += f" Speed has dipped about {-change:.0f} words/min lately, so go back to easier practice and rebuild confidence."

    comps = [x["comprehension"] for x in recent if x["comprehension"] is not None and x["comprehension"] >= 0]
    low_comp = bool(comps) and _mean(comps) < 2

    wordstep = (f"Practise these words five times each: {', '.join(focus[:5])}." if focus
                else "No difficult words this week. Read a new passage for pleasure.")
    plans = {
        "stamina": [("Day 1", "Read one sentence at a time. Stop, breathe, then read the next."),
                    ("Day 2", "Echo reading: you read a sentence, the child repeats it. Add one sentence each round."),
                    ("Day 3", "Record again. The only goal is to reach the last word.")],
        "on_target": [("Day 1", "Read the passage with expression, as if telling a story to a friend."),
                      ("Day 2", f"Ask 3 questions about it and record how many {name} answers."),
                      ("Day 3", "Record again for a target reading, or try a passage in another language.")],
        "accurate_slow": [("Day 1", "Reread the passage together, you and the child in turns, at a steady pace."),
                          ("Day 2", "Child reads the same passage 3 times. Notice how it gets smoother each time."),
                          ("Day 3", f"Record again and try to beat the last speed by {max(step, 3)} words/min.")],
        "fast_careless": [("Day 1", "Slow down: point a finger under each word and read every one."),
                          ("Day 2", wordstep),
                          ("Day 3", "Record again. Accuracy counts more than speed.")],
        "building": [("Day 1", "Read the passage aloud together so the child hears it done well."),
                     ("Day 2", wordstep),
                     ("Day 3", "Child reads alone, then record in Padho.")],
    }[pattern]
    if pattern != "fast_careless" and pattern != "building" and focus:
        plans[1] = (plans[1][0], plans[1][1] + " " + wordstep)
    if low_comp:
        plans.append(("Extra", "After each reading, ask 'what happened?' and 'why?'. Understanding needs practice too."))

    if pattern == "on_target":
        encouragement = f"{name} has earned a celebration. Say the achievement out loud in class!"
    elif trend == "up":
        encouragement = f"{name} is improving. Show the child their own graph, so they can see it."
    else:
        encouragement = f"Praise the effort, not just the score. Every reading is practice that counts."

    return {
        "has_data": True, "name": name, "pattern": pattern, "trend": trend, "headline": headlines[pattern],
        "diagnosis": diagnosis, "focus_words": focus, "persistent_words": persistent, "goal": goal,
        "plan": plans, "encouragement": encouragement, "next_badge": badge, "next_badge_how": badge_how,
        "stats": {"wcpm": w, "accuracy": a, "coverage": cov, "readings": n},
    }
