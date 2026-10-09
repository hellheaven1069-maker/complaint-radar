"""Complaint Radar: entry point (login + navigation).  Run: streamlit run app.py"""
import streamlit as st

from core.analysis import DISCLAIMER
from core.auth import current_user, login_screen, logout
from core.data import sidebar_filters

st.set_page_config(page_title="Complaint Radar", page_icon="📡", layout="wide")

user = current_user()
if not user:
    login_screen()
    st.stop()

nav = st.navigation([
    st.Page("views/dashboard.py", title="Dashboard", icon="📊", default=True),
    st.Page("views/data_analysis.py", title="Data analysis", icon="🧮"),
    st.Page("views/classification.py", title="Classification", icon="🏷️"),
    st.Page("views/patterns.py", title="Patterns", icon="🔎"),
    st.Page("views/spacetime.py", title="Time-space research", icon="🗺️"),
    st.Page("views/risk_scoring.py", title="Risk scoring", icon="⚖️"),
    st.Page("views/assessments.py", title="Assessments", icon="📝"),
])

with st.sidebar:
    st.markdown(f"**{user['name']}**  \n{user['role']}")
    st.button("Log out", on_click=logout)
sidebar_filters()
st.caption("⚠️ " + DISCLAIMER)
nav.run()
