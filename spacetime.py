import altair as alt
import pandas as pd
import streamlit as st

from core.analysis import STATE_COORDS
from core.data import get_filtered

df = get_filtered()
st.title("🗺️ Time-space research")
st.write("Where and when are complaints concentrated? Filter by business or category, then move the time slider.")

c1, c2 = st.columns(2)
comp = c1.selectbox("Business", ["All"] + sorted(df["company"].unique()))
cat = c2.selectbox("Category", ["All"] + sorted(df["category"].unique()))
d = df
if comp != "All":
    d = d[d["company"] == comp]
if cat != "All":
    d = d[d["category"] == cat]
if d.empty:
    st.info("No complaints for this selection.")
    st.stop()

d = d.assign(week=d["date"].dt.to_period("W-SUN").dt.end_time.dt.normalize())
weeks = sorted(d["week"].dt.date.unique())
end = st.select_slider("Show the 4 weeks ending", options=weeks, value=weeks[-1])
sub = d[(d["date"].dt.date > end - pd.Timedelta(days=28)) & (d["date"].dt.date <= end)]
prev = d[(d["date"].dt.date > end - pd.Timedelta(days=56)) & (d["date"].dt.date <= end - pd.Timedelta(days=28))]

st.subheader("Hotspots (last 4 weeks)")
by = sub.groupby("state").size().rename("complaints").to_frame().join(prev.groupby("state").size().rename("previous_4_weeks")).fillna(0)
by["change"] = by["complaints"] - by["previous_4_weeks"]
by = by.reset_index()
m = by.assign(lat=by["state"].map(lambda s: STATE_COORDS.get(s, (None, None))[0]),
              lon=by["state"].map(lambda s: STATE_COORDS.get(s, (None, None))[1])).dropna(subset=["lat"])
m["size"] = m["complaints"] * 6000
a, b = st.columns([3, 2])
with a:
    if m.empty:
        st.info("No complaints in this window.")
    else:
        st.map(m, latitude="lat", longitude="lon", size="size")
with b:
    st.dataframe(by.sort_values("complaints", ascending=False), hide_index=True)

st.subheader("State x week heatmap")
hm = d.groupby(["state", "week"]).size().reset_index(name="complaints")
st.altair_chart(alt.Chart(hm).mark_rect().encode(
    x=alt.X("week:T", title="Week"), y="state:N", color=alt.Color("complaints:Q", scale=alt.Scale(scheme="oranges")),
    tooltip=["state", "week:T", "complaints"]).properties(width="container", height=320))
st.caption("A bright block in one state for several weeks suggests a regional problem; bright across all states suggests a national one.")
