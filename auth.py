"""Simple login with roles. Demo-grade: for production use a real identity provider (OIDC / SSO)."""
import hashlib
import hmac
from datetime import datetime

import streamlit as st

SALT = b"complaint-radar-demo-salt"

def _hash(pw: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), SALT, 100_000).hex()

DEFAULT_USERS = {  # shown on the login page so judges can enter; override via secrets (see README)
    "regulator": {"hash": _hash("Regulator@2026"), "role": "Regulator", "name": "Demo Regulator"},
    "analyst": {"hash": _hash("Analyst@2026"), "role": "Analyst", "name": "Demo Analyst"},
}

def _users():
    try:
        cfg = st.secrets.get("users", None)
        if cfg:
            return {u: {"hash": _hash(v["password"]), "role": v.get("role", "Analyst"), "name": v.get("name", u)}
                    for u, v in cfg.items()}
    except Exception:
        pass
    return DEFAULT_USERS

def log_event(event: str):
    u = st.session_state.get("user", {}).get("username", "-")
    st.session_state.setdefault("audit", []).append(
        {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "user": u, "event": event})

def current_user():
    return st.session_state.get("user")

def logout():
    log_event("logout")
    st.session_state.pop("user", None)

def login_screen():
    st.title("📡 Complaint Radar")
    st.caption("From consumer complaints to regulatory action | National Legal Hackathon 2.0, Problem Statement 4")
    left, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.subheader("Sign in")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            ok = st.form_submit_button("Log in")
        if ok:
            if st.session_state.get("fails", 0) >= 5:
                st.error("Too many failed attempts. Reload the page to try again.")
            else:
                rec = _users().get(username.strip().lower())
                if rec and hmac.compare_digest(rec["hash"], _hash(password)):
                    st.session_state["user"] = {"username": username.strip().lower(), "role": rec["role"], "name": rec["name"]}
                    st.session_state["fails"] = 0
                    log_event("login")
                    st.rerun()
                else:
                    st.session_state["fails"] = st.session_state.get("fails", 0) + 1
                    st.error("Invalid username or password.")
        with st.expander("Demo credentials (for judges)"):
            st.markdown("**Regulator** (full access): `regulator` / `Regulator@2026`  \n"
                        "**Analyst** (cannot download assessments): `analyst` / `Analyst@2026`")
