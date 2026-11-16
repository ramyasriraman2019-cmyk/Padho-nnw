from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from padho import badges as bd, config, ui

ui.require_teacher()
store = ui.store()
LV = config.LEVELS

ui.page_header("📊 Class dashboard", "Who is improving, who needs help, who has not read this week.")

students = store.students()
if not students:
    st.info("No students registered yet.")
    st.page_link("views/register.py", label="Register students", icon="📝")
    st.stop()

attempts = store.attempts()
by_student = {}
for a in attempts:
    by_student.setdefault(a["student_id"], []).append(a)
badge_count = {}
for b in store.badges():
    badge_count[b["student_id"]] = badge_count.get(b["student_id"], 0) + 1

today = datetime.now(config.IST).date()
rows = []
for s in students:
    at = by_student.get(s["id"], [])
    last = at[-1] if at else None
    since = (today - bd.local_date(last["ts"])).days if last else None
    trend = ""
    if len(at) >= 2:
        d = at[-1]["wcpm"] - at[0]["wcpm"]
        trend = f"▲ +{d:.0f}" if d > 0 else (f"▼ {d:.0f}" if d < 0 else "▬ 0")
    target = LV[s["level"]]["wpm"]
    flag = ""
    if not at:
        flag = "Not started"
    elif since is not None and since >= 7:
        flag = f"No reading for {since} days"
    elif last["wcpm"] < 0.6 * target:
        flag = "Below 60% of target speed"
    rows.append({
        "Student": s["name"], "Class": s["class_name"], "Section": s["section"] or "", "Level": s["level"],
        "Readings": len(at), "Latest words/min": round(last["wcpm"], 1) if last else None,
        "Latest accuracy %": round(last["accuracy"], 1) if last else None, "Change since first": trend,
        "Days since reading": since, "Badges": badge_count.get(s["id"], 0), "Needs attention": flag,
    })
df = pd.DataFrame(rows)

f1, f2 = st.columns(2)
classes = ["All"] + sorted(df["Class"].unique())
cls = f1.selectbox("Class", classes)
secs = ["All"] + sorted(x for x in df["Section"].unique() if x)
sec = f2.selectbox("Section", secs)
view = df[(df["Class"] == cls) | (cls == "All")]
view = view[(view["Section"] == sec) | (sec == "All")]

week = sum(1 for r in view["Days since reading"] if r is not None and r <= 7)
attn = view[view["Needs attention"] != ""]
t = st.columns(4)
for col, (c, v, cap) in zip(t, [
    ("t-purple", len(view), "students"), ("t-green", week, "read in the last 7 days"),
    ("t-red", len(attn), "need attention"),
    ("t-orange", f"{view['Latest words/min'].mean():.0f}" if view["Latest words/min"].notna().any() else "—",
     "average latest words/min"),
]):
    col.markdown(ui.tile(c, v, cap), unsafe_allow_html=True)
st.write("")

g1, g2 = st.columns(2, gap="large")
with g1:
    st.markdown("#### Students on each level")
    lc = view["Level"].value_counts().reindex(list(LV), fill_value=0).reset_index()
    lc.columns = ["Level", "Students"]
    lc["Name"] = lc["Level"].map(lambda k: f"L{k} {LV[k]['name']}")
    fig = px.bar(lc, x="Name", y="Students", color="Name", color_discrete_sequence=[LV[k]["color"] for k in LV])
    fig.update_layout(height=300, showlegend=False, margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="")
    st.plotly_chart(fig, **ui.stretch())
with g2:
    st.markdown("#### Class average words/min by week")
    ids = set(s["id"] for s in students if (cls == "All" or s["class_name"] == cls)
              and (sec == "All" or (s["section"] or "") == sec))
    recs = [{"week": bd.parse_ts(a["ts"]).strftime("%G-W%V"), "wcpm": a["wcpm"]} for a in attempts if a["student_id"] in ids]
    if recs:
        wk = pd.DataFrame(recs).groupby("week")["wcpm"].mean().reset_index()
        fig = px.line(wk, x="week", y="wcpm", markers=True)
        fig.update_traces(line=dict(color="#7B4397", width=3))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", yaxis_title="words/min", xaxis_title="")
        st.plotly_chart(fig, **ui.stretch())
    else:
        st.info("No readings yet.")

st.markdown("#### 🚩 Needs attention")
if len(attn):
    st.dataframe(attn[["Student", "Class", "Section", "Level", "Needs attention", "Latest words/min"]],
                 **ui.stretch(), hide_index=True)
else:
    st.success("Nobody is flagged. Everyone is reading regularly.")

st.markdown("#### 📋 Whole class")
st.dataframe(view.drop(columns=["Needs attention"]), **ui.stretch(), hide_index=True)
st.download_button("⬇️ Download class summary (CSV)", view.to_csv(index=False), "padho_class_summary.csv", "text/csv")
st.caption("There is deliberately no ranking or leaderboard. Children are compared with their own earlier readings, not with each other.")
