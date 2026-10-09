"""Core analytics (no Streamlit here): classification, spikes, risk scoring, legal mapping, assessments."""
import numpy as np
import pandas as pd

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict
    from sklearn.pipeline import make_pipeline
    HAS_SKLEARN = True
except Exception:  # app still works with keyword rules only
    HAS_SKLEARN = False

REQUIRED_COLS = ["complaint_id", "date", "company", "sector", "product", "state", "amount_inr", "complaint_text"]

# ------------------------------------------------------------------ classification
KEYWORDS = {
    "Delayed refund": ["refund", "money deducted", "credited", "paise cut"],
    "Hidden charges": ["hidden", "extra", "additional charge", "surprise", "fee"],
    "Subscription trap": ["auto-renew", "auto renew", "subscription", "unsubscribe", "free trial", "unable to cancel", "renew"],
    "Misleading advertisement": ["advertis", "misleading", "ad promised", "description said", "claimed", "false"],
    "Defective product": ["defective", "damaged", "faulty", "broken", "stopped working", "kharab"],
    "Data misuse": ["personal data", "spam call", "consent", "privacy", "contacts and location"],
}

def classify_kw(text: str) -> str:
    t = str(text).lower()
    scores = {c: sum(k in t for k in kws) for c, kws in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"

def make_model():
    # character n-grams make the model tolerant to typos and mixed Hindi-English text
    return make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2),
                         LogisticRegression(max_iter=1000))

def fit_model(texts, labels):
    return make_model().fit(list(texts), list(labels)) if HAS_SKLEARN else None

def ml_predictions(texts, labels):
    """Out-of-fold predictions, so accuracy is measured on complaints the model has not seen."""
    if not HAS_SKLEARN:
        return None
    cv = int(min(5, pd.Series(labels).value_counts().min()))
    if cv < 2:
        return None
    try:
        return cross_val_predict(make_model(), list(texts), list(labels), cv=cv)
    except Exception:
        return None

def prepare(raw: pd.DataFrame, method: str = "Keyword rules") -> pd.DataFrame:
    df = raw.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce").fillna(0)
    df["kw_category"] = df["complaint_text"].map(classify_kw)
    labels = df["_true_category"] if "_true_category" in df.columns else df["kw_category"]
    preds = ml_predictions(df["complaint_text"], labels)
    df["ml_category"] = preds if preds is not None else df["kw_category"]
    df["category"] = df["ml_category"] if method.startswith("ML") else df["kw_category"]
    return df

# ------------------------------------------------------------------ risk scoring
WEIGHTS = {"Volume": 0.30, "Growth": 0.25, "Money": 0.15, "Spread": 0.10, "Severity": 0.20}
SEVERITY = {"Data misuse": 1.0, "Subscription trap": 0.8, "Hidden charges": 0.8, "Misleading advertisement": 0.8,
            "Delayed refund": 0.6, "Defective product": 0.5, "Other": 0.3}

def _norm_w(w):
    s = sum(w.values()) or 1
    return {k: v / s for k, v in w.items()}

def _scale(s):
    return s / s.max() if s.max() > 0 else s * 0

def score_issues(df, window_days=90, min_complaints=10, weights=None, severity=None):
    """An 'issue' = company + complaint category. Compares the latest window with the one before it."""
    if df.empty:
        return pd.DataFrame()
    w, sev = _norm_w(weights or WEIGHTS), severity or SEVERITY
    ref = df["date"].max()
    recent = df[df["date"] > ref - pd.Timedelta(days=window_days)]
    prior = df[(df["date"] <= ref - pd.Timedelta(days=window_days)) &
               (df["date"] > ref - pd.Timedelta(days=2 * window_days))]
    g = recent.groupby(["company", "category"]).agg(
        recent_complaints=("complaint_id", "count"),
        total_amount=("amount_inr", "sum"),
        states_affected=("state", "nunique"),
        top_state=("state", lambda s: s.value_counts().index[0]),
        top_state_share=("state", lambda s: s.value_counts(normalize=True).iloc[0]),
    ).reset_index()
    p = prior.groupby(["company", "category"]).size().rename("prior_complaints").reset_index()
    out = g.merge(p, on=["company", "category"], how="left").fillna({"prior_complaints": 0})
    out = out[out["recent_complaints"] >= min_complaints].copy()
    if out.empty:
        return out
    out["growth_pct"] = ((out["recent_complaints"] - out["prior_complaints"]) / (out["prior_complaints"] + 1) * 100).round(0)
    parts = {
        "Volume": _scale(out["recent_complaints"]),
        "Growth": out["growth_pct"].clip(0, 500) / 500,
        "Money": _scale(out["total_amount"]),
        "Spread": out["states_affected"] / max(df["state"].nunique(), 1),
        "Severity": out["category"].map(sev).fillna(0.3),
    }
    for k, v in parts.items():
        out[k] = (100 * w[k] * v).round(1)
    out["risk_score"] = sum(out[k] for k in parts).round(1)
    out["risk_level"] = pd.cut(out["risk_score"], [-1, 35, 60, 101], labels=["Low", "Medium", "High"])
    return out.sort_values("risk_score", ascending=False).reset_index(drop=True)

# ------------------------------------------------------------------ patterns
def detect_spikes(df, z=2.5, min_total=20):
    """Weeks where a company+category count is unusually high versus its own history."""
    w = (df.set_index("date").groupby(["company", "category"]).resample("W").size().rename("n").reset_index())
    w = w[w.groupby(["company", "category"])["n"].transform("sum") >= min_total].copy()
    g = w.groupby(["company", "category"])["n"]
    sd = g.transform("std").replace(0, np.nan)
    w["z_score"] = ((w["n"] - g.transform("mean")) / sd).fillna(0).round(2)
    return w[(w["z_score"] >= z) & (w["n"] >= 5)].sort_values("z_score", ascending=False)

def emerging_categories(df, recent_days=30):
    ref = df["date"].max()
    r, b = df[df["date"] > ref - pd.Timedelta(days=recent_days)], df[df["date"] <= ref - pd.Timedelta(days=recent_days)]
    out = pd.DataFrame({"recent_share": r["category"].value_counts(normalize=True),
                        "baseline_share": b["category"].value_counts(normalize=True),
                        "recent_complaints": r["category"].value_counts()}).fillna(0)
    out["change_pct_points"] = ((out["recent_share"] - out["baseline_share"]) * 100).round(1)
    out[["recent_share", "baseline_share"]] = (out[["recent_share", "baseline_share"]] * 100).round(1)
    return out.sort_values("change_pct_points", ascending=False).reset_index(names="category")

STATE_COORDS = {
    "Maharashtra": (19.75, 75.71), "Delhi": (28.61, 77.21), "Karnataka": (15.32, 75.71), "Rajasthan": (27.02, 74.22),
    "Gujarat": (22.26, 71.19), "Tamil Nadu": (11.13, 78.66), "Uttar Pradesh": (26.85, 80.91), "West Bengal": (22.99, 87.85),
    "Telangana": (18.11, 79.02), "Kerala": (10.85, 76.27), "Punjab": (31.15, 75.34), "Haryana": (29.06, 76.09),
    "Bihar": (25.10, 85.31), "Madhya Pradesh": (22.97, 78.66), "Odisha": (20.95, 85.10), "Assam": (26.20, 92.94),
    "Andhra Pradesh": (15.91, 79.74), "Goa": (15.30, 74.12), "Jharkhand": (23.61, 85.28), "Chhattisgarh": (21.28, 81.87),
    "Uttarakhand": (30.07, 79.02), "Himachal Pradesh": (31.10, 77.17),
}

# ------------------------------------------------------------------ legal framing and reports
# Check every provision against the official text (indiacode.nic.in) before relying on it.
LEGAL = {
    "Delayed refund": ("Possible unfair trade practice (failure to refund as promised) and deficiency in service.",
                       "Consumer Protection Act, 2019 (unfair trade practice, s.2(47)); Consumer Protection (E-Commerce) Rules, 2020."),
    "Hidden charges": ("Possible drip pricing / non-transparent pricing.",
                       "CPA 2019 (unfair trade practice); Guidelines for Prevention and Regulation of Dark Patterns, 2023."),
    "Subscription trap": ("Possible subscription trap and obstructed cancellation (dark patterns).",
                          "Dark Patterns Guidelines, 2023; CPA 2019 (unfair contract, unfair trade practice)."),
    "Misleading advertisement": ("Possible misleading advertisement.",
                                 "CPA 2019 (misleading advertisement, s.2(28); CCPA powers under Chapter III)."),
    "Defective product": ("Possible defect in goods / product liability concerns.",
                          "CPA 2019 (defect, s.2(10); product liability, Chapter VI)."),
    "Data misuse": ("Possible misuse of personal data without valid consent.",
                    "Digital Personal Data Protection Act, 2023 read with CPA 2019 (unfair trade practice)."),
    "Other": ("Unclear. Needs manual review.", "N/A"),
}
DISCLAIMER = ("Automated, preliminary statistical assessment. A pattern of complaints is NOT proof of legal liability or "
              "a final legal finding. Allegations are unverified and the business has not been heard. "
              "Professional legal review is required before any action.")

def next_steps(r):
    if r.risk_level == "High":
        s = ["Open a preliminary inquiry and call for detailed information from the business.",
             "Examine the business's published policies and complaint-handling records."]
        if r.growth_pct > 150:
            s.append("Consider an advisory or notice, since complaints are rising sharply.")
    elif r.risk_level == "Medium":
        s = ["Monitor weekly and gather more information.", "Consider a sector advisory on compliance expectations."]
    else:
        s = ["Continue routine monitoring."]
    if r.top_state_share >= 0.6:
        s.append(f"Coordinate with {r.top_state} consumer authorities (regional concentration).")
    return s

def evidence(df, company, category, n=5):
    sub = df[(df["company"] == company) & (df["category"] == category)].sort_values("date").tail(n)
    return sub[["complaint_id", "date", "state", "amount_inr", "complaint_text"]]

def build_assessment(r, df, window_days=90, reviewer=None):
    concern, law = LEGAL.get(r.category, LEGAL["Other"])
    ev = "\n".join(f'  - [{x.complaint_id}] {x.state}: "{x.complaint_text}"' for x in evidence(df, r.company, r.category, 3).itertuples())
    steps = "\n".join(f"  {i}. {s}" for i, s in enumerate(next_steps(r), 1))
    rev = (f"\nLEGAL REVIEW\nReviewer: {reviewer.get('name') or 'N/A'} | Status: {reviewer.get('status')}\nNotes: {reviewer.get('notes') or 'None'}\n"
           if reviewer else "\nLEGAL REVIEW\nNot yet reviewed by a legal professional.\n")
    return f"""REGULATORY ASSESSMENT: {r.company} / {r.category}
Risk level: {r.risk_level} (score {r.risk_score}/100)

1. WHAT IS HAPPENING
{int(r.recent_complaints)} complaints in the last {window_days} days vs {int(r.prior_complaints)} in the previous {window_days} days ({r.growth_pct:+.0f}%).
Reported across {int(r.states_affected)} states (largest share: {r.top_state}, {r.top_state_share:.0%}).
Total amount involved: INR {r.total_amount:,.0f}.

2. WHY IT MAY MATTER
{concern}
Possibly relevant framework: {law}

3. WHAT SHOULD BE EXAMINED NEXT
{steps}

4. EVIDENCE (sample complaints)
{ev}

5. HOW THE SCORE WAS BUILT (points out of 100)
Volume {r.Volume} + Growth {r.Growth} + Money {r.Money} + Spread {r.Spread} + Severity {r.Severity} = {r.risk_score}
{rev}
LIMITATIONS: {DISCLAIMER}
"""
