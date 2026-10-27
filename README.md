# OneRecord: clean master data and a five-country regional view for Lives Group

*SMU DSA Data Case Competition 2026 · Modernising Master Data Management at Lives Group*

> **Demo video:** [youtube.com/watch?v=1l3sva9yBHI](https://www.youtube.com/watch?v=1l3sva9yBHI) · **Summary slides:** _add link_

OneRecord has **two parts**, joined by clean master data:

| | Part 1: Regional dashboard | Part 2: Request workflow |
|---|---|---|
| **What it does** | Turns clean records into decisions: growth by country, forecasts, sales call lists, duplicate clean-up | Gets clean records in: smart request form, parallel approvals, SAP B1 import file |
| **Who uses it** | Daniel (Regional Commercial Lead), commercial analysts, Priya (MDM) | Amy and other requestors, approvers, Priya (MDM) |
| **Built with** | Streamlit (Python), running locally | Power Apps, Power Automate, SharePoint, Teams |
| **In production** | Power BI | As built: Microsoft 365, which Lives Group already licenses |
| **Start here** | [Run the dashboard](#run-the-dashboard) | [Microsoft 365 build guide](docs/M365_BUILD.md) |

The [process flow](docs/PROCESS_FLOW.md) follows one request person by person, from the form to SAP B1 to the
regional view.

**Contents:** [The problem](#the-problem-in-one-line) · [What OneRecord does](#what-onerecord-does) ·
[Results](#results) · [Part 1: Regional dashboard](#part-1-regional-dashboard) ·
[Part 2: Request workflow](#part-2-request-workflow-microsoft-365) · [Repository map](#repository-map) ·
[Assumptions](#assumptions)

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

The first three rows are Part 2 (Microsoft 365); the last row is Part 1 (the dashboard).

## Results

*All on synthetic data; see [Assumptions](#assumptions).*

**From the request workflow (Part 2)**

- **Request → SAP:** median 18.8 → **about 4–6 days**, simulated on the same 150 requests. Parallel approvals and the
  smart form alone give about 6 days (slowest 10%: 28 → about 6) even if notifications and reminders changed nothing.
  If half of each approver's wait was "not seeing it" and reminders remove that, it's about 4 days (slowest 10%: about 6).
- **Stopping new duplicates:** the request form flags all 41 planted duplicates when each is typed in as a new
  request, from the name alone (typos included); 6 of 205 genuinely new customers (3%) get a warning, which only asks
  for a reason.

**From the dashboard (Part 1)**

- **Cleaning up old duplicates:** the bulk matcher finds the 41 duplicate records among 246 (17%), 100% precision and
  recall on the synthetic answer key, with look-alikes sent to human review. Like the form's figure above, this is on
  data we generated, so validate it in a pilot.
- **Forecasting:** 11.1% error vs 13.7% for today's 6-month average (WAPE, Products A/B, forecasting 1–3 months ahead,
  tested on data the model hadn't seen); MAPE 12.3% vs 15.3%. The dashboard forecasts **6 months ahead**: tested from
  each month Jan–Sep 2026, the model's error is 10.5% one month ahead and 13.0% six months ahead, against 13.7% and 14.9%
  for the 6-month average. 7–12 months ahead can't be checked yet with 18 months of history.
- **Sales signals:** 27 customers dropping off (catching 18 of the 19 real cases), compared with 56 alerts on raw
  records, worth about S$431k a quarter. They form a **call list** ranked by value at risk, with the reason in plain
  words; the top 10 are called within two weeks. An **early warning** flags 5 larger customers who have gone quiet (no
  order for longer than 9 in 10 of their own past gaps, and at least 45 days) before a full quarter of lower orders
  shows; 4 of them are already dropping off. 98 cross-sell leads with no false gaps.
- **One customer across entities:** after merging duplicates, 124 of the 204 customers active in Apr–Sep 2026 buy from
  more than one of SPD, QTS and QTG, and they make up 79% of order value. In this data each entity sells one product
  line (SPD: A, QTS: B, QTG: C).
- **Email sorting:** the rules never mislabelled anything, but sent most messy, hand-written emails to review. That gap is
  why the design adds an AI step and a human check.

---

## Part 1: Regional dashboard

The Streamlit app is the regional business view: one place to see growth across the five countries, forecasts,
which customers to call, and the MDM team's clean-up work. In production this would be Power BI on the same
SharePoint data.

### Run the dashboard

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

It opens at http://localhost:8501 on the **Overview** page as Daniel. Everything runs on the synthetic data in
`data/`; no Microsoft 365 account or API key is needed.

### Who sees what

Switch user at the bottom of the sidebar. Each user sees only the pages for their job.

| User | Role | Pages |
|---|---|---|
| **Daniel** (default) | Regional Commercial Lead | Overview, Country deep-dive, Forecasting, Customers, Business case |
| **Commercial analyst** | Sales operations | Daniel's pages plus Orders vs enquiries |
| **Priya** | MDM Analyst | MDM ops, Orders vs enquiries |

### Pages

| Page | What it answers |
|---|---|
| **Overview** | How is the region doing? Headline numbers, growth by country and product, the top actions, and the trend with its forecast. Filter by country and period. |
| **Country deep-dive** | Which countries and product lines are growing or falling, by entity (SPD, QTS, QTG). |
| **Forecasting** | How much better the business-calendar model is than today's 6-month average, how far ahead it holds, and the 6-month forecast per country and product. |
| **Customers** | Who is ordering much less (the call list, ranked by value at risk), who has gone quiet, and cross-sell leads. A toggle reruns it on raw SAP records to show what duplicates do to the alerts. |
| **MDM ops** | Today's request cycle time, the duplicates the bulk matcher found, and the SAP DTW files that freeze them. |
| **Orders vs enquiries** | How incoming emails are sorted into orders, enquiries, follow-ups and setup requests (rules first, then AI, then a person). |
| **Business case** | Time and money saved, with every assumption adjustable. |

### Demo walkthrough

1. As **Daniel**, start on *Overview*: the headline numbers, the growth heatmap and the actions. Pick a country.
2. Open *Country deep-dive* to see where that growth comes from.
3. Open *Forecasting*: the calendar model against the 6-month average, and the 6-month forecast.
4. Open *Customers*: the call list. Switch on *Data check: show raw SAP records* to see the false alerts duplicates cause.
5. Open *Business case* and change an assumption.
6. Switch to **Priya**: *MDM ops* shows the duplicates found and the clean-up files to download.

### Optional: AI features

Two features call OpenAI and need an `OPENAI_API_KEY`, set in your shell or in `.streamlit/secrets.toml`
(git ignores it). The model is `gpt-5.4-nano` by default; set `OPENAI_MODEL` to change it. On Streamlit Community
Cloud, paste `OPENAI_API_KEY = "..."` into the app's **Settings → Secrets**.

- **AI action brief** (bottom of *Forecasting*): a preview of a planned Phase 2 feature. Without a key the page
  shows the standard plan instead.
- **AI step for messy emails** (*Orders vs enquiries*): the page shows recorded runs, so it works without a key.
  To record a fresh run, use `python3 scripts/run_ai_step.py`.

### Try the workflow without Microsoft 365

The real request workflow (Part 2) needs our Teams tenant. So that it can be tried in the browser, the app also has a
**Workflow mock-up** section (sidebar, bottom) with the same steps: New request, Request status, Approvals, MDM check,
Audit log and Rules. Switch *Workflow persona* to act as Amy, an approver or Priya, and use the demo clock to fire
reminders. Its duplicate check is simpler than the Power App's (names only). Everyone using a deployed copy shares one
demo database; *Reset demo data* starts it over. Hide it with `SHOW_WORKFLOW_MOCKUP` in `app.py`.

---

## Part 2: Request workflow (Microsoft 365)

The workflow runs for real in a Teams team, built only with **standard connectors** (SharePoint, Approvals, Teams,
Outlook), so it needs no premium licence and no custom code on a server.

**Full details, the setup guide and known limits are in [docs/M365_BUILD.md](docs/M365_BUILD.md).**

### What's built

| Brief asks for | What we built |
|---|---|
| A standard intake for Customer, Item, Vendor and Cost Center requests | **Power App "NewRequestForm"**: shows only the fields that apply, checks formats (e.g. each country's registration no.), and keeps *Submit* off until the request is complete. Shows who will approve before submitting. |
| No duplicates reaching an approver | Live checks while typing, against SAP records and pending requests. A matching ID is **blocked**; a similar name (typos included) is **warned** and needs a reason. |
| Faster approvals | **Flow "Route and approve"**: every first-stage approval goes out **in parallel** in Teams, then MDM approves last. Approvers can approve, reject or send it back for changes. |
| Knowing where a request stands | **Flow "Reminders and escalation"**: 9 AM reminders in each approver's time zone, escalation to their manager after 4 days. Requestors get Teams messages and a *My requests* screen with a timeline. |
| Closing the email route | **Flow "Email auto-reply"**: emailed requests to the MDM mailbox get a reply with the form link. |
| A trustworthy record | **ApprovalLog**: every step is logged; staff can read it but only the flows write to it. Each approval is tied to the exact version approved. |
| Protecting sensitive fields | Bank details and credit terms live in a restricted **SensitiveDetails** list; approval cards carry a link, never the values. |
| Changing rules without IT | The app's **Rules** screen lets MDM add approval steps, fields, business units, people and product lines in plain words. |
| Getting the record into SAP B1 | After MDM approval, the flow writes a **SAP DTW import file** and proposes the SAP code. MDM marks it created after importing. |

### Tested end to end (synthetic data, on our tenant)

| Request | What it showed |
|---|---|
| REQ-0004 (Customer) | Three stage-1 approvals in parallel, then MDM. Status *Created in SAP*, SAP file created, requestor notified in Teams. |
| REQ-0005 (regulated Item) | Quality/Regulatory added only because the item is regulated. With Assigned dates back-dated: a reminder at 3 days, an escalation to `EscalateTo` at 5 days. (Tested on the earlier, message-only escalation; the re-send-to-manager version is not yet tested on the tenant.) |
| REQ-0006 (Item for the new BU "LGD") | No BU Head in Roles, so the step went to the MDM Analyst. Teams nudge, *Routing gap* log row, request stage *"BU Head missing for LGD in Roles; sent to MDM"*. |
| REQ-0007 (Customer) | Finance card linked to the restricted SensitiveDetails row. After approval: `REQ-0007_BusinessPartners_DTW.txt` with code `C20007`, payment terms and credit limit taken from the restricted list. |
| Duplicate checks | Blocked: registration no. `200288778W`, part no. `BN-DEN-NS1-25`, tax ID `TX40404038`, SPD + Sales cost centre. Warned: *"Dengue NS1 rapid test 25T"* (matches item A-1001). |

### How the pieces fit

```
Power App (New request)  ──writes──▶  Requests + SensitiveDetails (SharePoint)
        │                                       │ new item (checked every minute)
        │ reads rules & master data             ▼
        ├── RequiredFields, BusinessUnits   Flow: Route and approve
        ├── CustomerMaster, Aliases            ├─ reads RoutingRules, Roles, RequiredFields
        ├── ItemMaster, VendorMaster           ├─ stage 1: parallel approvals (Teams/Outlook) ─┐
        ├── CostCentres                        ├─ stage 2: MDM Analyst                         ├─▶ ApprovalLog
        ├── (My requests) Roles, ApprovalLog   └─ SAP DTW file → SAP_Imports, status, Teams    ┘
        └── (Rules, MDM) edits RoutingRules, Roles, RequiredFields, BusinessUnits, Aliases
                                            Flow: Reminders and escalation (hourly, 9 AM local) ─▶ ApprovalLog
```

To demo it, follow [Amy's story](docs/M365_BUILD.md#demo-script-amys-story). To set it up in another tenant
(about an hour), follow the [rebuild guide](docs/M365_BUILD.md#rebuild-it-in-another-microsoft-365-tenant).

---

## Repository map

**Part 1: Regional dashboard and analysis**

| Path | What |
|---|---|
| `app.py`, `views/` | The Streamlit dashboard (plus the workflow mock-up in `views/workflow_pages.py`) |
| `onerecord/dedup.py` | Duplicate matching across SPD/QTS/QTG (deterministic rules, nothing to retrain) |
| `onerecord/forecast.py` | 6-month average baseline vs business-calendar model, tested on held-back months |
| `onerecord/insights.py` | Growth table, drop-off and cross-sell alerts on clean data |
| `onerecord/classify.py` | Sorting orders / enquiries / follow-ups / master-data requests (rules → AI → person) |
| `onerecord/process.py` | Baseline cycle-time breakdown and future-state simulation |

**Part 2: Microsoft 365 build**

| Path | What |
|---|---|
| `docs/M365_BUILD.md` | What's built in detail, demo script, rebuild guide and known limits |
| `sharepoint/` | The SharePoint list templates (CSV), `import/` copies of the empty lists, and the `LISTS.md` design notes |
| `powerapps/` | The Power App's source: `gen_form.py` generates it, `NewRequestForm/Src` holds the unpacked app, and `paste/` holds the files to paste into Studio |
| `powerautomate/` | The flows: the `build_*.py` scripts generate the importable packages (`*.zip`); `pkg.py` holds the shared settings |
| `NewRequestForm*.msapp` | Packed copies of the app (pasting into Studio is how it was actually loaded) |
| `onerecord/livecheck.py` | The form's duplicate check, mirrored in Python to measure it |
| `onerecord/workflow.py` | Workflow engine mirroring the Power Automate flows (SQLite), used by the workflow mock-up |

**Shared**

| Path | What |
|---|---|
| `docs/PROCESS_FLOW.md` | The end-to-end process with a diagram: request, parallel approvals, SAP B1 import, regional view |
| `data/`, `scripts/generate_data.py` | Synthetic dataset and its generator; `data/README.md` explains what's planted |

## Assumptions

- **All data is synthetic.** No client data was provided. The generator builds it to look like SAP B1 exports,
  with timings calibrated to the brief (2–3 weeks, Amy's 18 days). Validate every number in a pilot.
- **Entity → product mapping:** SPD = A (IVD reagents), QTS = B (lab consumables), QTG = C (equipment).
- **Growth measure:** year-on-year units, Apr–Sep 2026 vs Apr–Sep 2025, counting customer orders only.
- **Business case:** sales-driven benefits are counted at gross margin. Hours, rates and conversion rates are placeholders, adjustable on the
  *Business case* page.
