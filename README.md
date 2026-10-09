# 📡 Complaint Radar

**From consumer complaints to regulatory action** | National Legal Hackathon 2.0, Problem Statement 4

A Streamlit application that helps a consumer-protection regulator turn raw complaints into an evidence-based assessment, answering three questions: **What is happening? Why might it matter? What should be examined next?**

> ⚠️ **Not legal advice.** Outputs are preliminary statistical indications. A pattern of complaints is *not* proof of legal liability. All company names and data in this repository are **fictional and simulated**.

## Features

| Page | What it does |
|---|---|
| **Login** | Role-based access (Regulator / Analyst), failed-attempt lockout, session audit log |
| **Dashboard** | KPIs, weekly trends by category, top flagged issues |
| **Data analysis** | Data-quality checks, distributions, searchable table, CSV upload with schema validation |
| **Classification** | Keyword rules vs ML (TF-IDF + logistic regression), cross-validated accuracy, confusion matrix, live "try it" box |
| **Patterns** | Repeated complaints, weekly spike detection (z-score), emerging categories |
| **Time-space research** | State hotspot map, 4-week time slider, state x week heatmap |
| **Risk scoring** | Adjustable, explainable score (volume, growth, money, spread, severity) with a per-factor breakdown |
| **Assessments** | Structured report per issue: evidence, legal framing, next steps, legal-review block, downloads |

## Run locally

```bash
pip install -r requirements.txt
python generate_data.py        # optional, data/complaints.csv is included
streamlit run app.py
```
On Windows, if `streamlit` is not recognised, use `python -m streamlit run app.py`.

**Demo logins:** `regulator` / `Regulator@2026` (full access), `analyst` / `Analyst@2026` (no downloads).
To use your own accounts, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` (or paste it into Streamlit Cloud > Settings > Secrets).

## Deploy (free)

1. Push this folder to a **public** GitHub repository (keep the folder structure).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, choose **Create app**.
3. Repository: yours. Branch: `main`. Main file path: `app.py`. Click **Deploy**.

## Project structure

```
app.py                  entry point: login gate + navigation + sidebar filters
core/analysis.py        classification, spikes, risk score, legal mapping, report builder (no Streamlit)
core/auth.py            login, roles, audit log
core/data.py            loading, validation, filters, cached scoring
views/                  one file per page
data/complaints.csv     simulated dataset (planted patterns)
generate_data.py        regenerates the dataset
```

## Method in brief

* **Issue** = company + complaint category. The latest window (default 90 days) is compared with the previous equal window.
* **Risk score (0-100)** = Volume 30% + Growth 25% + Money 15% + Spread 10% + Severity 20% (all adjustable in the app). Levels: Low < 35, Medium 35-60, High > 60.
* **Spikes**: a week is flagged when its count is at least 2.5 standard deviations above that company-category's own weekly average.
* **Planted patterns in the sample data** (so the system has something to find): QuickKart refund surge, StreamNova rising subscription trap, FreshBasket regional hidden charges, PayEasy small but severe data-misuse cluster, ShopEase steady misleading-ad background (should stay Low).

## Legal framing and limits

Each category is mapped to possibly relevant provisions (Consumer Protection Act, 2019; E-Commerce Rules, 2020; Dark Patterns Guidelines, 2023; DPDP Act, 2023). **Verify every provision against the official text before relying on it.** Limitations: simulated data; keyword and ML classifiers can misclassify; complaints are unverified allegations; volume can reflect company size, not wrongdoing; demo login is not production-grade security.
