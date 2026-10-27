# OneRecord

*SMU DSA Data Case Competition 2026 · Modernising Master Data Management at Lives Group*

**The problem:** bad data gets into SAP B1 when a record is first requested. A new record takes **18.8 days**
(median), and duplicate customers distort the regional sales view.

**OneRecord** is one Streamlit app with two parts:

| Part | What it does | Built with |
|---|---|---|
| **Regional view** | Growth by country and product, 6-month forecasts, customers to call, duplicate clean-up | Streamlit (Python) on synthetic SAP data |
| **Request workflow** | Smart request form, parallel approvals, reminders and escalation, SAP B1 import file | Streamlit, running the same rules and logic as our Power Apps + Power Automate build |

Everything works without signing in. The workflow also runs live on Microsoft 365 (shown in the demo video); both
read the same rule lists in `sharepoint/`.

## Results (synthetic data)

- **Request to SAP:** 18.8 → **about 4–6 days** (simulated on the same 150 requests).
- **New duplicates:** the form flags **all 41** planted duplicates while typing; 3% of genuinely new customers get a warning.
- **Old duplicates:** the bulk matcher finds the **41 duplicates among 246 records (17%)**, with no false matches.
- **Forecasting:** **11.1%** error vs 13.7% for today's 6-month average (WAPE, Products A and B, 1–3 months ahead).
- **Sales:** a call list of **27 customers dropping off**, worth about **S$431k a quarter**, and 98 cross-sell leads.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501. No API key or Microsoft 365 account is needed.

## Pages

Switch user at the bottom of the sidebar; each person sees the pages for their job.

| Page | What it shows | Who |
|---|---|---|
| **Overview** | Headline numbers, growth by country and product, top actions, trend and forecast | Daniel, analyst |
| **Country deep-dive** | Growth and decline by country, product and entity (SPD, QTS, QTG) | Daniel, analyst |
| **Forecasting** | Our model vs the 6-month average, and the 6-month forecast | Daniel, analyst |
| **Customers** | Call list ranked by value at risk, customers gone quiet, cross-sell leads | Daniel, analyst |
| **MDM ops** | Request cycle time, duplicates found, SAP clean-up files | Priya |
| **Orders vs enquiries** | Emails sorted into orders, enquiries, follow-ups and setup requests | Analyst, Priya |
| **Business case** | Time and money saved, with adjustable assumptions | Daniel, analyst |
| **New request** | The request form, with format and duplicate checks while you type | Everyone |
| **My requests** | Where each request stands, who it's waiting on, its timeline; *Edit and resubmit* | Everyone |
| **Approvals** | Your approval cards: Approve, Request changes or Reject | Approvers, Priya |
| **Audit log** | Every step of every request | Priya |
| **Rules** | Who approves what, and which fields the form asks for | Everyone views; only Priya edits |

**Users:** Daniel (Regional Commercial Lead), Commercial analyst, Amy (requestor), BU Head, Wei Jie (Finance),
QA/RA Lead, Business Support, and Priya (MDM Analyst). Only Finance, MDM and the requestor see bank and credit details.

**Try it:** as Amy, raise a request on *New request*; switch to each approver and approve it on *Approvals*; as
Priya, give the final approval, download the SAP file and press *Mark as created in SAP*. The *Demo clock* in the
sidebar skips ahead days to fire reminders and escalation. Everyone shares one set of demo data; *Reset demo data*
starts it over.

**Growth** = year-on-year change in units ordered, Apr–Sep 2026 vs Apr–Sep 2025, customer orders only. Setup
requests are counted separately and never included.

## The request workflow

| Step | What happens |
|---|---|
| **Request** | The form shows only the fields that apply, checks formats, and blocks or warns on duplicates while typing |
| **Approve** | All first-stage approvers get their card **at the same time**; MDM approves last |
| **Chase** | Reminders at 9 AM in each approver's time zone; escalation to their manager after 4 days |
| **Protect** | Bank details sit in a restricted list; every step is written to an audit log |
| **Load** | After MDM approval, the flow writes a **SAP B1 DTW import file** with a proposed SAP code |

The Microsoft 365 version uses only standard connectors, so it needs no premium licence. Details and rebuild
guide: [docs/M365_BUILD.md](docs/M365_BUILD.md). The end-to-end process: [docs/PROCESS_FLOW.md](docs/PROCESS_FLOW.md).

## Repository

| Path | What |
|---|---|
| `app.py`, `views/` | The Streamlit app (`views/workflow_pages.py` is the request workflow) |
| `onerecord/` | Analysis (duplicate matching, forecasting, sales alerts, email sorting) and `workflow.py`, the workflow engine |
| `powerapps/`, `powerautomate/`, `sharepoint/` | The Microsoft 365 build: app source, flow packages, list templates |
| `data/` | Synthetic dataset (`scripts/generate_data.py` builds it; `data/README.md` explains it) |
| `docs/` | Build guide, process flow, screenshots |

## Assumptions

- **All data is synthetic**, built to look like SAP B1 exports. Validate every number in a pilot.
- **Entities:** SPD sells A (IVD reagents), QTS sells B (lab consumables), QTG sells C (equipment).
- **Business case:** hours, rates and conversion rates are estimates, adjustable in the app.
- **AI features** (optional): set `OPENAI_API_KEY` to turn on the AI action brief; without it the app shows the
  standard plan and recorded AI runs.
