"""Printable progress report as one self-contained HTML page (all scripts render
correctly because the browser does the text shaping; use Print -> Save as PDF)."""

import json
from datetime import datetime
from html import escape

from .badges import BADGES, local_date, met_count
from .config import FEATURES, IST, LANGS, LEVELS, MAX_LEVEL, MET_TO_PROMOTE, NIPUN_ACC, NIPUN_WPM


def svg_line(vals, target=None, color="#7B4397", w=520, h=190, fmt="{:.0f}", ymax=None):
    if not vals:
        return '<p style="color:#888">No readings yet.</p>'
    pl, pr, pt, pb = 40, 16, 14, 26
    top = ymax or (max(max(vals), target or 0) * 1.18) or 1
    n = len(vals)
    X = lambda i: pl + (w - pl - pr) * (i / (n - 1) if n > 1 else 0.5)
    Y = lambda v: pt + (h - pt - pb) * (1 - v / top)
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">']
    for f in (0, 0.5, 1):
        y = Y(top * f / 1.0 * 1.0)
        out.append(f'<line x1="{pl}" x2="{w - pr}" y1="{y:.1f}" y2="{y:.1f}" stroke="#EEE"/>'
                   f'<text x="{pl - 6}" y="{y + 4:.1f}" font-size="11" fill="#999" text-anchor="end">{top * f:.0f}</text>')
    if target:
        y = Y(target)
        out.append(f'<line x1="{pl}" x2="{w - pr}" y1="{y:.1f}" y2="{y:.1f}" stroke="#E74C3C" stroke-dasharray="6 4"/>'
                   f'<text x="{w - pr}" y="{y - 4:.1f}" font-size="11" fill="#E74C3C" text-anchor="end">target {target}</text>')
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
    if n > 1:
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/>')
    step = max(1, n // 10)
    for i, v in enumerate(vals):
        out.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4.5" fill="{color}" stroke="#fff" stroke-width="1.5"/>')
        if i % step == 0 or i == n - 1:
            out.append(f'<text x="{X(i):.1f}" y="{h - 8}" font-size="11" fill="#999" text-anchor="middle">{i + 1}</text>')
    out.append(f'<text x="{X(n - 1):.1f}" y="{Y(vals[-1]) - 10:.1f}" font-size="12" font-weight="700" fill="{color}" '
               f'text-anchor="middle">{fmt.format(vals[-1])}</text></svg>')
    return "".join(out)


def auto_comment(name, attempts, level):
    first_name = name.split()[0] if name.split() else name
    n = len(attempts)
    if n == 0:
        return f"{first_name} has not completed a reading yet. Let us begin with a short passage."
    lv = LEVELS[level]
    last = attempts[-1]
    parts = []
    if n >= 2:
        d = last["wcpm"] - attempts[0]["wcpm"]
        if d > 0:
            parts.append(f"{first_name} now reads {d:.0f} words per minute faster than at the first reading.")
        elif d < 0:
            parts.append(f"{first_name}'s speed has dipped by {-d:.0f} words per minute, so a little daily practice will help.")
    if last["accuracy"] >= lv["acc"]:
        parts.append("Accuracy is on target.")
    else:
        parts.append("The next step is to read more carefully; practise the words listed below.")
    if last["wcpm"] >= lv["wpm"]:
        parts.append("Reading speed is on target.")
    return " ".join(parts)


def build_report(student, photo_uri, attempts, earned_keys, school, teacher, comment, streak, mentor=None):
    lvl = student["level"]
    lv = LEVELS[lvl]
    n = len(attempts)
    wc = [a["wcpm"] for a in attempts]
    ac = [a["accuracy"] for a in attempts]
    best = max(wc) if wc else 0
    avg_acc = sum(ac) / n if n else 0
    last_date = local_date(attempts[-1]["ts"]).strftime("%d %b %Y") if n else "—"

    miss = {}
    for a in attempts[-8:]:
        for w in json.loads(a["bad_words"] or "[]") + json.loads(a["skip_words"] or "[]"):
            miss[w] = miss.get(w, 0) + 1
    top_miss = [w for w, _ in sorted(miss.items(), key=lambda kv: -kv[1])[:14]]

    got = met_count(attempts, lvl)
    if lvl < MAX_LEVEL:
        nxt = LEVELS[lvl + 1]
        prog_txt = f"{min(got, MET_TO_PROMOTE)} of {MET_TO_PROMOTE} target readings toward Level {lvl + 1} · {nxt['name']} {nxt['emoji']}"
    else:
        prog_txt = "Top level reached 🎉"
    prog_pct = min(100, int(100 * got / MET_TO_PROMOTE)) if lvl < MAX_LEVEL else 100

    badge_html = "".join(
        f'<span class="bd">{BADGES[k]["emoji"]} {escape(BADGES[k]["name"])}</span>' for k in BADGES if k in earned_keys
    ) or '<span class="muted">No badges yet. The first one is just one reading away!</span>'
    miss_html = "".join(f'<span class="mw">{escape(w)}</span>' for w in top_miss) or '<span class="muted">None. Well done!</span>'

    rows = "".join(
        f"<tr><td>{local_date(a['ts']).strftime('%d %b')}</td><td>L{a['level']}</td><td>{a['wcpm']:.0f}</td>"
        f"<td>{a['accuracy']:.0f}%</td><td>{a['coverage']:.0f}%</td><td>{'✔' if a['met'] else ''}</td></tr>"
        for a in reversed(attempts[-8:])
    )
    # --- the four features, shown as a strip at the top --------------------------
    strip = '<div class="strip">' + "".join(
        f'<span class="fp">{f["emoji"]} {escape(f["name"])}</span>' for f in FEATURES) + "</div>"

    # --- NIPUN Bharat standard ----------------------------------------------------
    last3 = attempts[-3:]
    nip_w = sum(a["wcpm"] for a in last3) / len(last3) if last3 else 0
    nip_a = sum(a["accuracy"] for a in last3) / len(last3) if last3 else 0
    nip_pct = min(100, int(100 * nip_w / NIPUN_WPM))
    if not last3:
        nip_status = "No readings yet."
    elif nip_w >= NIPUN_WPM and nip_a >= NIPUN_ACC:
        nip_status = "✅ Meets the NIPUN Bharat reading-fluency reference."
    elif nip_w >= NIPUN_WPM:
        nip_status = f"Speed is on the reference. Accuracy needs to reach {NIPUN_ACC}%."
    else:
        nip_status = f"{NIPUN_WPM - nip_w:.0f} words per minute to go to reach the reference."
    nipun_card = (
        '<div class="card"><h3>🇮🇳 NIPUN Bharat standard</h3>'
        f'<div class="bar"><i style="width:{nip_pct}%;background:#138808"></i></div>'
        f'<p style="margin:6px 0 0;font-weight:600"><b>{nip_w:.0f}</b> of <b>{NIPUN_WPM}</b> words/min '
        f'(average of last 3 readings) · accuracy {nip_a:.0f}% (reference {NIPUN_ACC}%)</p>'
        f'<p style="margin:2px 0 0;font-weight:700">{nip_status}</p>'
        '<p class="muted" style="margin:4px 0 0;font-size:.8rem">NIPUN Bharat (Ministry of Education) aims for 45 to 60 '
        'words per minute by the end of Class 2 and at least 60 by the end of Class 3, read with meaning. '
        'Padho uses these as reference bands for practice. This is not an examination result.</p></div>')

    # --- Personalised Mentor AI -----------------------------------------------------
    mentor_card = ""
    if mentor:
        days = "".join(f'<div class="dy"><b>{escape(d)}</b><span>{escape(t)}</span></div>' for d, t in mentor["plan"])
        words = ("<p><b>Focus words:</b> " + "".join(f'<span class="mw">{escape(w)}</span>' for w in mentor["focus_words"])
                 + "</p>") if mentor["focus_words"] else ""
        nb = (f'<p><span class="bd">Next badge: {escape(mentor["next_badge"])}</span> '
              f'<span class="muted">{escape(mentor["next_badge_how"])}</span></p>') if mentor.get("next_badge") else ""
        mentor_card = (
            '<div class="card mentor"><h3>🧑‍🏫 Personalised Mentor AI</h3>'
            f'<p style="margin:2px 0;font-weight:700;color:#7B4397">{escape(mentor["headline"])}</p>'
            f'<p style="margin:4px 0">{escape(mentor["diagnosis"])}</p>{words}'
            f'<div class="goal">🎯 {escape(mentor["goal"])}</div>{days}'
            f'<p style="margin:6px 0 0">💬 {escape(mentor["encouragement"])}</p>{nb}</div>')

    lang = LANGS.get(student["language"], {}).get("label", student["language"])
    sec = f" · Section {escape(student['section'])}" if student.get("section") else ""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Progress card - {escape(student['name'])}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Mukta:wght@400;600;700&display=swap');
*{{box-sizing:border-box}} body{{margin:0;font-family:'Mukta',sans-serif;color:#1F2A26;background:#f4eefa;}}
.page{{max-width:820px;margin:0 auto;background:#fff;padding:26px 32px;}}
h1,h2,h3{{font-family:'Baloo 2',sans-serif;margin:0}}
.head{{background:linear-gradient(120deg,#F7971E,#FF5F6D 50%,#7B4397);color:#fff;border-radius:18px;padding:16px 22px;display:flex;justify-content:space-between;align-items:center}}
.head h1{{font-size:1.6rem}} .head small{{font-weight:600;opacity:.95}}
.who{{display:flex;gap:20px;align-items:center;margin:18px 0}}
.who img{{width:120px;height:120px;border-radius:50%;object-fit:cover;border:5px solid #F2C94C}}
.who h2{{font-size:1.9rem;color:#3B1C57}} .who p{{margin:2px 0;color:#555;font-weight:600}}
.lvl{{display:inline-block;background:{lv['color']};color:#fff;border-radius:999px;padding:3px 14px;font-weight:700;font-family:'Baloo 2'}}
.tiles{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:8px 0 16px}}
.t{{border-radius:14px;padding:12px;background:#FDF3E3;text-align:center}} .t b{{display:block;font-size:1.7rem;font-family:'Baloo 2';color:#7B4397}} .t span{{font-size:.8rem;font-weight:700;color:#666}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.card{{border:1px solid #EEE;border-radius:14px;padding:12px 14px;margin-bottom:14px}}
.card h3{{font-size:1.05rem;color:#3B1C57;margin-bottom:6px}}
.bar{{height:14px;background:#EEE;border-radius:99px;overflow:hidden}} .bar i{{display:block;height:100%;width:{prog_pct}%;background:{lv['color']}}}
.bd{{display:inline-block;background:#FFF4CC;border:1.5px solid #F2C94C;border-radius:999px;padding:3px 12px;margin:3px 4px 3px 0;font-weight:700;font-size:.9rem}}
.mw{{display:inline-block;background:#FFE8E6;color:#C0392B;border-radius:999px;padding:3px 12px;margin:3px 4px 3px 0;font-weight:700;font-family:'Baloo 2'}}
.muted{{color:#888}} table{{width:100%;border-collapse:collapse;font-size:.88rem}} th,td{{padding:5px 6px;border-bottom:1px solid #EEE;text-align:center}} th{{color:#777}}
.cm{{background:#F4ECFA;border-left:5px solid #7B4397;border-radius:8px;padding:10px 14px}}
.sig{{display:flex;justify-content:space-between;margin-top:30px;color:#555;font-weight:600}}
.foot{{margin-top:14px;font-size:.74rem;color:#888}}
.btn{{display:block;margin:10px auto;padding:10px 22px;border:0;border-radius:999px;background:#7B4397;color:#fff;font-weight:700;font-size:1rem;cursor:pointer}}
.strip{{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 0}}
.fp{{background:#F4ECFA;color:#5B2F7A;border:1.5px solid #D9C2EC;border-radius:999px;padding:3px 12px;font-weight:700;font-size:.8rem}}
.sec{{font-size:1.05rem;color:#3B1C57;margin:8px 0 2px}}
.mentor{{background:linear-gradient(135deg,#F4ECFA,#FFF4E6);border:2px solid #D9C2EC}}
.mentor .goal{{background:#fff;border-left:6px solid #F2994A;border-radius:8px;padding:8px 12px;margin:8px 0;font-weight:600}}
.dy{{display:flex;gap:10px;background:#fff;border-radius:10px;padding:6px 10px;margin:4px 0;border:1px solid #EADCF3}}
.dy b{{color:#7B4397;min-width:48px}}
@media print{{ .noprint{{display:none}} body{{background:#fff}} .page{{padding:0}} }}
</style></head><body><div class="page">
<button class="btn noprint" onclick="window.print()">🖨️ Print / Save as PDF</button>
<div class="head"><div><h1>📖 Reading Progress Card</h1><small>{escape(school)}</small></div><small>Generated {datetime.now(IST).strftime('%d %b %Y')}</small></div>
{strip}<div class="who"><img src="{photo_uri}" alt="">
  <div><h2>{escape(student['name'])}</h2><p>{escape(student['class_name'])}{sec}{' · Roll ' + escape(student['roll']) if student.get('roll') else ''}</p>
  <p>Language: {escape(lang)}</p><span class="lvl">Level {lvl} · {lv['name']} {lv['emoji']}</span></div></div>
<h3 class="sec">📊 Student performance monitoring</h3><div class="tiles"><div class="t"><b>{n}</b><span>readings</span></div><div class="t"><b>{best:.0f}</b><span>best words/min</span></div>
<div class="t"><b>{avg_acc:.0f}%</b><span>average accuracy</span></div><div class="t"><b>{streak}</b><span>day streak 🔥</span></div></div>
<div class="card"><h3>Level progress</h3><div class="bar"><i></i></div><p style="margin:6px 0 0;font-weight:600">{prog_txt}</p>
<p class="muted" style="margin:2px 0 0;font-size:.82rem">Target for this level: {lv['wpm']} words/min at {lv['acc']}% accuracy.</p></div>
{nipun_card}
<div class="grid"><div class="card"><h3>Words per minute</h3>{svg_line(wc, lv['wpm'], '#7B4397')}</div>
<div class="card"><h3>Accuracy %</h3>{svg_line(ac, lv['acc'], '#11998E', ymax=100)}</div></div>
<div class="grid"><div class="card"><h3>🏅 Badges earned</h3>{badge_html}</div>
<div class="card"><h3>📝 Words to practise</h3>{miss_html}</div></div>
<div class="card"><h3>Recent readings</h3><table><tr><th>Date</th><th>Level</th><th>Words/min</th><th>Accuracy</th><th>Passage read</th><th>Target</th></tr>{rows}</table></div>
{mentor_card}
<div class="card"><h3>Teacher's note</h3><div class="cm">{escape(comment)}</div></div>
<div class="sig"><span>Teacher: {escape(teacher)}</span><span>Parent's signature: ____________</span></div>
<p class="foot">Speech recognised by Bhashini ASR (MeitY, Government of India). Last reading: {last_date}. Padho is a practice and screening tool, not an examination or a diagnosis. Speech recognition can mis-hear accents, so the numbers are a guide for the teacher, not a final judgement of the child.</p>
</div></body></html>"""
