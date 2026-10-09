import streamlit as st

from core.analysis import DISCLAIMER, build_assessment, evidence
from core.auth import current_user, log_event
from core.data import get_filtered, get_issues

df = get_filtered()
issues = get_issues(df)
user = current_user()
st.title("📝 Assessments")
st.write("**Why might it matter? What should be examined next?** A structured report for each flagged issue.")

if issues.empty:
    st.info("Nothing flagged.")
    st.stop()

labels = [f"{r.company} / {r.category} ({r.risk_level}, {r.risk_score})" for r in issues.itertuples()]
i = st.selectbox("Flagged issue", range(len(labels)), format_func=lambda k: labels[k])
row = next(issues.iloc[[i]].itertuples())

with st.expander("Legal review (optional, included in the report)"):
    name = st.text_input("Reviewer name")
    status = st.selectbox("Status", ["Pending review", "Reviewed: needs more evidence", "Reviewed: recommend action", "Reviewed: no action"])
    notes = st.text_area("Reviewer notes")
reviewer = {"name": name, "status": status, "notes": notes} if (name or notes or status != "Pending review") else None

report = build_assessment(row, df, st.session_state.get("window", 90), reviewer)
a, b = st.columns([3, 2])
with a:
    st.code(report, language=None, wrap_lines=True)
with b:
    st.subheader("Supporting complaints")
    st.dataframe(evidence(df, row.company, row.category, 8), hide_index=True)
    st.warning(DISCLAIMER)

if user["role"] == "Regulator":
    if st.download_button("Download this assessment (.txt)", report, f"assessment_{row.company}_{row.category}.txt".replace(" ", "_")):
        log_event(f"downloaded assessment {row.company}/{row.category}")
    st.download_button("Download all flagged issues (CSV)", issues.to_csv(index=False), "flagged_issues.csv", "text/csv")
else:
    st.info("Downloads are available to the Regulator role only.")

if user["role"] == "Regulator":
    with st.expander("Audit log (this session)"):
        st.dataframe(st.session_state.get("audit", []), hide_index=True)
