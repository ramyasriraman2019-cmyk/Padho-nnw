"""
Padho! — AI Oral Reading Fluency Meter (v2)
==========================================
Registration, student profiles, reading history, 5 reading levels, motivation
badges and printable progress reports, powered by Bhashini speech recognition.

K M Ramyasri, Primary School Teacher (PST) · Suthukeny Government High School
"""

import streamlit as st

st.set_page_config(
    page_title="Padho! — Reading Fluency Meter",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from padho import ui  # noqa: E402  (after set_page_config)

ui.inject_css()

pages = {
    "Padho": [
        st.Page("views/home.py", title="Home", icon="🏠", default=True),
        st.Page("views/badges_page.py", title="Motivation Badges", icon="🏅"),
    ],
    "Students": [
        st.Page("views/register.py", title="Register student", icon="📝"),
        st.Page("views/read.py", title="Read & Assess", icon="🎤"),
        st.Page("views/profile.py", title="Student profile", icon="🧒"),
        st.Page("views/mentor.py", title="Personalised Mentor AI", icon="🧑‍🏫"),
        st.Page("views/report_page.py", title="Progress card", icon="📄"),
    ],
    "Teacher": [
        st.Page("views/dashboard.py", title="Class dashboard", icon="📊"),
        st.Page("views/admin.py", title="Admin & backup", icon="⚙️"),
    ],
}

nav = st.navigation(pages)
ui.sidebar()
nav.run()
