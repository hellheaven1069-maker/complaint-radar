import altair as alt
import pandas as pd
import streamlit as st

from core.analysis import HAS_SKLEARN, classify_kw, fit_model
from core.data import get_filtered

df = get_filtered()
st.title("🏷️ Classification")
st.write("Every complaint is sorted into a category. Two methods are compared: transparent **keyword rules** and a "
         "**machine-learning model** (TF-IDF character n-grams + logistic regression, which tolerates typos and Hindi-English text).")

has_truth = "_true_category" in df.columns
if has_truth:
    st.subheader("Accuracy against known labels")
    acc = pd.DataFrame({"Method": ["Keyword rules", "ML (TF-IDF)"],
                        "Accuracy %": [(df["kw_category"] == df["_true_category"]).mean() * 100,
                                       (df["ml_category"] == df["_true_category"]).mean() * 100]}).round(1)
    st.dataframe(acc, hide_index=True)
    st.caption("ML accuracy uses cross-validation, so each complaint is predicted by a model that has not seen it. "
               "The sample data is simulated and fairly clean; real complaints will score lower.")
else:
    st.info("No `_true_category` column in this dataset, so accuracy cannot be measured. The ML model is trained on "
            "keyword labels only, which makes it a weak check.")

a, b = st.columns(2)
with a:
    st.subheader("Category distribution")
    st.bar_chart(df["category"].value_counts())
with b:
    st.subheader("Where the two methods disagree")
    dis = df[df["kw_category"] != df["ml_category"]]
    st.metric("Disagreements", f"{len(dis)} ({len(dis) / len(df):.1%})")
    st.dataframe(dis[["complaint_text", "kw_category", "ml_category"]].head(10), hide_index=True)

if has_truth:
    st.subheader("Confusion matrix (selected method)")
    cm = pd.crosstab(df["_true_category"], df["category"]).reset_index().melt("_true_category", var_name="predicted", value_name="n")
    st.altair_chart(alt.Chart(cm).mark_rect().encode(
        x="predicted:N", y=alt.Y("_true_category:N", title="actual"),
        color=alt.Color("n:Q", scale=alt.Scale(scheme="blues")), tooltip=["_true_category", "predicted", "n"])
        .properties(width="container", height=320))

st.subheader("Try it")
text = st.text_area("Type a complaint", "I was charged an extra fee at checkout that was not mentioned earlier")
if text.strip():
    st.write(f"Keyword rules: **{classify_kw(text)}**")
    if HAS_SKLEARN:
        @st.cache_resource
        def _model(n):
            labels = df_full["_true_category"] if has_truth else df_full["kw_category"]
            return fit_model(df_full["complaint_text"], labels)
        df_full = st.session_state["df_full"]
        model = _model(len(df_full))
        probs = pd.Series(model.predict_proba([text])[0], index=model.classes_).sort_values(ascending=False)
        st.write(f"ML model: **{probs.index[0]}** ({probs.iloc[0]:.0%} confidence)")
        st.bar_chart(probs.head(4))
