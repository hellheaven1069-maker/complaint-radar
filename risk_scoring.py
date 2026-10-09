import altair as alt
import streamlit as st

from core.analysis import SEVERITY, WEIGHTS
from core.data import get_filtered, get_issues

df = get_filtered()
st.title("⚖️ Risk scoring")
st.write("The score is a transparent, adjustable formula, not a black box. Change the weights and watch the ranking update.")

with st.expander("Scoring settings", expanded=True):
    c = st.columns(5)
    w = {k: c[i].slider(k, 0, 100, int(v * 100), key=f"w_{k}") for i, (k, v) in enumerate(WEIGHTS.items())}
    st.session_state["weights"] = {k: v / 100 for k, v in w.items()}
    d1, d2 = st.columns(2)
    st.session_state["window"] = d1.slider("Comparison window (days)", 30, 180, 90, 15)
    st.session_state["min_n"] = d2.slider("Minimum complaints to be flagged", 5, 50, 10)
    st.caption("Weights are normalised to add up to 100%. Growth = change versus the previous window of equal length.")
    sev_cols = st.columns(len(SEVERITY))
    st.session_state["severity"] = {k: sev_cols[i].number_input(k, 0.0, 1.0, v, 0.1, key=f"sev_{k}")
                                    for i, (k, v) in enumerate(SEVERITY.items())}

issues = get_issues(df)
if issues.empty:
    st.info("No issue crosses the threshold.")
    st.stop()

st.subheader("Ranked issues")
st.dataframe(issues[["company", "category", "recent_complaints", "prior_complaints", "growth_pct", "states_affected",
                     "total_amount", "risk_score", "risk_level"]], hide_index=True)

st.subheader("What drives each score")
long = issues.head(10).assign(issue=lambda x: x["company"] + " / " + x["category"]).melt(
    id_vars="issue", value_vars=list(WEIGHTS), var_name="factor", value_name="points")
st.altair_chart(alt.Chart(long).mark_bar().encode(
    y=alt.Y("issue:N", sort="-x", title=None), x=alt.X("sum(points):Q", title="Risk points"),
    color="factor:N", tooltip=["issue", "factor", "points"]).properties(width="container", height=320))
st.caption("Levels: Low below 35, Medium 35 to 60, High above 60. These thresholds are judgement calls; explain yours in the demo.")
