import altair as alt
import streamlit as st

from core.analysis import detect_spikes, emerging_categories
from core.data import get_filtered

df = get_filtered()
st.title("🔎 Patterns")
st.write("Isolated complaints become evidence when they repeat. This page finds repeated, spiking and emerging problems.")
t1, t2, t3 = st.tabs(["Repeated complaints", "Spikes", "Emerging categories"])

with t1:
    rep = df.groupby(["company", "category"]).agg(complaints=("complaint_id", "count"), states=("state", "nunique"),
                                                  amount_inr=("amount_inr", "sum")).reset_index()
    rep["share_of_company_%"] = (rep["complaints"] / rep.groupby("company")["complaints"].transform("sum") * 100).round(1)
    top = st.slider("Minimum complaints", 5, 100, 20)
    st.dataframe(rep[rep["complaints"] >= top].sort_values("complaints", ascending=False), hide_index=True)
    st.caption("A high share of one category within a company points to a specific practice, not general dissatisfaction.")

with t2:
    z = st.slider("Spike threshold (z-score)", 1.5, 5.0, 2.5, 0.1)
    sp = detect_spikes(df, z=z)
    st.write("A spike is a week whose complaint count is unusually high compared with that company's own history for the category.")
    if sp.empty:
        st.info("No spikes at this threshold.")
    else:
        st.dataframe(sp.rename(columns={"n": "complaints_that_week"}), hide_index=True)
        pairs = (sp["company"] + " / " + sp["category"]).unique().tolist()
        pick = st.selectbox("Plot a flagged issue", pairs)
        comp, cat = pick.split(" / ")
        s = df[(df["company"] == comp) & (df["category"] == cat)].set_index("date").resample("W").size().rename("complaints").reset_index()
        base = alt.Chart(s).encode(x="date:T", y="complaints:Q")
        st.altair_chart((base.mark_line() + base.mark_point()).properties(width="container", height=260))

with t3:
    days = st.slider("Recent window (days)", 14, 90, 30)
    em = emerging_categories(df, days)
    st.dataframe(em, hide_index=True)
    st.caption("Positive change means the category is taking a larger share of complaints than before.")
