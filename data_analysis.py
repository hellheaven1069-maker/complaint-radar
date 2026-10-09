import altair as alt
import pandas as pd
import streamlit as st

from core.analysis import REQUIRED_COLS
from core.data import current_raw, get_filtered, missing_columns

df = get_filtered()
st.title("🧮 Data analysis")
t1, t2, t3, t4 = st.tabs(["Overview", "Distributions", "Browse data", "Upload your own data"])

with t1:
    c = st.columns(4)
    c[0].metric("Rows", f"{len(df):,}")
    c[1].metric("Date span (days)", (df["date"].max() - df["date"].min()).days)
    c[2].metric("Median amount (INR)", f"{df['amount_inr'].median():,.0f}")
    c[3].metric("Duplicate texts", int(df["complaint_text"].duplicated().sum()))
    st.subheader("Data quality")
    q = pd.DataFrame({"missing": df[REQUIRED_COLS].isna().sum(), "unique values": df[REQUIRED_COLS].nunique()})
    st.dataframe(q)
    st.subheader("Summary of numeric fields")
    st.dataframe(df[["amount_inr"]].describe())

with t2:
    st.subheader("Amount involved per complaint")
    st.altair_chart(alt.Chart(df).mark_bar().encode(alt.X("amount_inr:Q", bin=alt.Bin(maxbins=30), title="INR"), y="count()")
                    .properties(width="container", height=250))
    a, b = st.columns(2)
    a.subheader("By sector"); a.bar_chart(df["sector"].value_counts())
    b.subheader("By state"); b.bar_chart(df["state"].value_counts())
    st.subheader("Business x category")
    pivot = df.groupby(["company", "category"]).size().reset_index(name="complaints")
    st.altair_chart(alt.Chart(pivot).mark_rect().encode(
        x="category:N", y="company:N", color=alt.Color("complaints:Q", scale=alt.Scale(scheme="reds")),
        tooltip=["company", "category", "complaints"]).properties(width="container", height=300))

with t3:
    q = st.text_input("Search complaint text")
    view = df[df["complaint_text"].str.contains(q, case=False, na=False)] if q else df
    st.dataframe(view[["complaint_id", "date", "company", "category", "state", "amount_inr", "complaint_text"]], hide_index=True)
    st.download_button("Download filtered data (CSV)", view.to_csv(index=False), "complaints_filtered.csv", "text/csv")

with t4:
    st.write("Upload a CSV with these columns: " + ", ".join(f"`{c}`" for c in REQUIRED_COLS))
    up = st.file_uploader("CSV file", type="csv")
    if up is not None:
        new = pd.read_csv(up)
        miss = missing_columns(new)
        if miss:
            st.error("Missing columns: " + ", ".join(miss))
        else:
            st.success(f"{len(new):,} rows look valid.")
            st.dataframe(new.head())
            if st.button("Use this dataset"):
                st.session_state["uploaded_df"] = new
                st.rerun()
    if "uploaded_df" in st.session_state:
        st.info("Currently using your uploaded dataset.")
        if st.button("Reset to sample data"):
            del st.session_state["uploaded_df"]
            st.rerun()
