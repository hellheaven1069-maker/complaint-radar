"""Shared data layer: loading, validation, sidebar filters, cached scoring."""
from pathlib import Path

import pandas as pd
import streamlit as st

from core.analysis import HAS_SKLEARN, REQUIRED_COLS, SEVERITY, WEIGHTS, prepare, score_issues

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "complaints.csv"

@st.cache_data
def _default_raw():
    return pd.read_csv(DATA_PATH)

@st.cache_data
def _prepared(raw, method):
    return prepare(raw, method)

def current_raw():
    return st.session_state.get("uploaded_df", _default_raw())

def missing_columns(df):
    return [c for c in REQUIRED_COLS if c not in df.columns]

def sidebar_filters():
    """Rendered once in app.py so filters persist across pages. Stores results in session_state."""
    sb = st.sidebar
    sb.divider()
    options = ["Keyword rules", "ML (TF-IDF)"] if HAS_SKLEARN else ["Keyword rules"]
    method = sb.radio("Classifier used for analysis", options, index=len(options) - 1, key="clf_method")
    full = _prepared(current_raw(), method)
    sb.subheader("Filters")
    d0, d1 = full["date"].min().date(), full["date"].max().date()
    rng = sb.date_input("Date range", (d0, d1), min_value=d0, max_value=d1, key="f_dates")
    start, end = (rng[0], rng[1]) if isinstance(rng, (tuple, list)) and len(rng) == 2 else (d0, d1)
    sectors = sb.multiselect("Sector", sorted(full["sector"].unique()), key="f_sector")
    states = sb.multiselect("State", sorted(full["state"].unique()), key="f_state")
    f = full[(full["date"].dt.date >= start) & (full["date"].dt.date <= end)]
    if sectors:
        f = f[f["sector"].isin(sectors)]
    if states:
        f = f[f["state"].isin(states)]
    st.session_state["df_full"], st.session_state["df_f"] = full, f
    sb.caption(f"{len(f):,} of {len(full):,} complaints selected")

def get_filtered():
    df = st.session_state["df_f"]
    if df.empty:
        st.warning("No complaints match the current filters.")
        st.stop()
    return df

def get_issues(df):
    return score_issues(df, window_days=st.session_state.get("window", 90),
                        min_complaints=st.session_state.get("min_n", 10),
                        weights=st.session_state.get("weights", WEIGHTS),
                        severity=st.session_state.get("severity", SEVERITY))
