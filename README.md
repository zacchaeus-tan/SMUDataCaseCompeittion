# OneRecord: clean master data for Lives Group

*SMU DSA Data Case Competition 2026 · Modernising Master Data Management at Lives Group*

> **Demo video:** _add YouTube link_ · **Summary slides:** _add link_

## The problem in one line

Bad data gets into SAP B1 when it's first entered. That one root cause makes a new record take
**18.8 days** (median), and it scrambles the per-customer view that sales needs to grow across five countries.

## What OneRecord does

| | Today | OneRecord |
|---|---|---|
| **Capture** | Free-text email, fields guessed, 41% bounce back | Smart form: only the fields that apply, can't submit incomplete, duplicate check while typing |
| **Approve** | Email chain, one approver after another, nobody notified | Parallel approval cards in Teams, reminders, escalation, live status |
| **Govern** | Scattered emails; bank details in email | Audit log that's only ever added to; sensitive fields in a restricted list; rules the MDM team edits without IT |
| **Use** | 6-month average forecasts; 17% of customer records are duplicates | Clean golden records, a forecast based on the business calendar, drop-off and cross-sell alerts for sales |

**Production build:** Microsoft 365, which Lives Group already licenses. Power Apps for the form, Power Automate for
approvals, SharePoint lists for data and rules, Power BI for the dashboard. The SAP B1 import file is generated
automatically. **This repository** contains a working Python prototype of the same design, plus the analysis engine.

## Results (on synthetic data, see *Assumptions*)

- **Request → SAP:** median 18.8 → about 4 days, and the slowest 10% go from 28 → about 6 days. This is simulated on the same 150 requests.
- **Duplicates:** 41 of 246 customer records (17%) found. On the synthetic answer key that's 100% precision and
  100% recall; look-alike records go to a human review queue rather than being merged automatically.
- **Forecasting:** 11.1% error vs 13.7% for today's 6-month average (WAPE, Products A/B, forecasting 1–3 months ahead, tested on data the model hadn't seen).
- **Sales signals:** 27 customers dropping off (catching 18 of the 19 real cases), compared with 56 alerts on raw records. 98 cross-sell leads with no false gaps.
- **Email sorting:** the rules never mislabelled anything, but sent most messy, hand-written emails to review. That gap is
  why the design adds an AI step and a human check.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Use the sidebar to switch persona (Amy, Wei Jie, Priya…) and to fast-forward the demo clock so reminders
and escalation fire. The optional AI step for ambiguous emails needs an `ANTHROPIC_API_KEY`; without one, those emails stay in human review.

## Repository map

| Path | What |
|---|---|
| `app.py`, `views/` | Streamlit prototype: workflow mock-up + regional business view |
| `onerecord/dedup.py` | Duplicate matching across SPD/QTS/QTG (deterministic rules, nothing to retrain) |
| `onerecord/forecast.py` | 6-month average baseline vs business-calendar model, tested on held-back months |
| `onerecord/insights.py` | Growth table, drop-off and cross-sell alerts on clean data |
| `onerecord/classify.py` | Sorting orders / enquiries / follow-ups / master-data requests (rules → AI → person) |
| `onerecord/process.py` | Baseline cycle-time breakdown and future-state simulation |
| `onerecord/workflow.py` | Workflow engine mirroring the Power Automate flows (SQLite) |
| `sharepoint/` | The SharePoint list templates + `LISTS.md` build guide for Power Apps / Power Automate |
| `data/`, `scripts/generate_data.py` | Synthetic dataset and its generator; `data/README.md` explains what's planted |

## Assumptions

- **All data is synthetic.** No client data was provided. The generator builds it to look like SAP B1 exports,
  with timings calibrated to the brief (2–3 weeks, Amy's 18 days). Validate every number in a pilot.
- **Entity → product mapping:** SPD = A (IVD reagents), QTS = B (lab consumables), QTG = C (equipment).
- **Growth measure:** year-on-year units, Apr–Sep 2026 vs Apr–Sep 2025, counting customer orders only.
- **Business case:** sales-driven benefits are counted at gross margin. Hours, rates and conversion rates are placeholders, adjustable on the
  *Business case* page.
