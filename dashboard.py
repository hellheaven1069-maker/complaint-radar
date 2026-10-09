import altair as alt
import pandas as pd
import streamlit as st

from core.data import get_filtered, get_issues

df = get_filtered()
issues = get_issues(df)
st.title("📊 Dashboard")
st.write("**What is happening?** A snapshot of complaints, trends and the issues that most need attention.")

c = st.columns(5)
c[0].metric("Complaints", f"{len(df):,}")
c[1].metric("Businesses", df["company"].nunique())
c[2].metric("Amount involved (INR)", f"{df['amount_inr'].sum():,.0f}")
c[3].metric("High-risk issues", 0 if issues.empty else int((issues["risk_level"] == "High").sum()))
c[4].metric("Latest complaint", df["date"].max().strftime("%d %b %Y"))

weekly = df.groupby([pd.Grouper(key="date", freq="W"), "category"]).size().reset_index(name="complaints")
st.subheader("Weekly complaints by category")
st.altair_chart(alt.Chart(weekly).mark_line().encode(
    x=alt.X("date:T", title="Week"), y="complaints:Q", color="category:N",
    tooltip=["date:T", "category:N", "complaints:Q"]).properties(width="container", height=300))

a, b = st.columns(2)
with a:
    st.subheader("Top flagged issues")
    if issues.empty:
        st.info("No issue crosses the minimum complaint threshold.")
    else:
        st.dataframe(issues[["company", "category", "recent_complaints", "growth_pct", "risk_score", "risk_level"]].head(6),
                     hide_index=True)
        st.caption("Open **Assessments** for the full report on each issue.")
with b:
    st.subheader("Complaints by business")
    st.bar_chart(df["company"].value_counts())
