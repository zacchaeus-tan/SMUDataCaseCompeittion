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
automatically. **This repository** contains a working Python prototype of the same design, plus the analysis engine,
and the working Microsoft 365 build itself (see [Microsoft 365 build](#microsoft-365-build)).

## Results (on synthetic data, see *Assumptions*)

- **Request → SAP:** median 18.8 → about 4 days, and the slowest 10% go from 28 → about 6 days. This is simulated on the same 150 requests.
- **Duplicates:** 41 of 246 customer records (17%) found. On the synthetic answer key that's 100% precision and
  100% recall; look-alike records go to a human review queue rather than being merged automatically.
- **Forecasting:** 11.1% error vs 13.7% for today's 6-month average (WAPE, Products A/B, forecasting 1–3 months ahead, tested on data the model hadn't seen).
- **Sales signals:** 27 customers dropping off (catching 18 of the 19 real cases), compared with 56 alerts on raw records. 98 cross-sell leads with no false gaps.
- **Email sorting:** the rules never mislabelled anything, but sent most messy, hand-written emails to review. That gap is
  why the design adds an AI step and a human check.

## Microsoft 365 build

The workflow half of OneRecord also runs for real on Microsoft 365. We built it in a Teams team, using only
**standard connectors** (SharePoint, Approvals, Teams), so it needs no premium licence and no custom code on a server.
The Streamlit app remains the place for the regional business view and forecasting (Power BI in production).

### What's built

| Brief asks for | How the M365 build does it |
|---|---|
| A standard intake for Customer, Item, Vendor and Cost Center requests | **Power App "NewRequestForm"**, *New request* screen. It shows only the fields that apply. Labels, help text and required/conditional rules come from the **RequiredFields** list (e.g. *Regulatory licence no.* appears when an item is regulated). **Submit** stays disabled until the request is complete. |
| No duplicates reaching an approver | Live checks while typing. **Customer:** same registration no. or a known alias blocks; all main words of the name in the same country warns. **Item:** same manufacturer part no. blocks; similar description (any entity) warns. **Vendor:** same tax ID blocks. **Cost Center:** an existing cost centre for that entity + department blocks. A warning can be overridden with an explicit "this is a different …" switch. |
| Faster approvals | **Flow "OneRecord - Route and approve"**. It reads **RoutingRules** and **Roles** and sends every stage-1 check **in parallel** as an approval card in Teams/Outlook. Conditional rules (e.g. Quality/Regulatory only for regulated items) come from the list. The MDM Analyst approves last. |
| Requestors and approvers know where a request stands | Approvers get cards plus **"OneRecord - Reminders and escalation"**: a reminder at 9 AM in the approver's own time zone once `SLADays` pass, escalation to `EscalateTo` after `EscalateAfterDays`. Requestors get Teams messages on rejection or completion. The app's **My requests** screen shows status, stage, days open, **who it is still waiting on**, the submitted details and (permissions allowing) the sensitive details. The MDM team can switch to all requests. |
| A trustworthy record of who approved what | **ApprovalLog** list: every assignment, decision, reminder, escalation, routing gap and SAP file is a row. Team members have **read-only** access; only the flows (running as the owner) write to it. Sensitive values are never logged. |
| Protecting sensitive fields | Bank details and credit terms are saved to **SensitiveDetails**, separate from the request. Item-level permissions let requestors read only their own rows; Finance and MDM have Design access to read all. Approval cards for roles allowed to see them (from **RequiredFields → VisibleToRoles**) carry a **link** to the row, never the values, so nothing sensitive goes into Teams or email. |
| Changing rules, fields and approvers without IT | Edit list rows. A new business unit is a **BusinessUnits** row plus its people in **Roles**. A new approval step is a **RoutingRules** row. Making a field required or conditional is a **RequiredFields** row. If a business unit has no approver for a step yet (Marcus's story), the request goes to the MDM Analyst instead of stalling. MDM is told in Teams, and the gap is logged and shown on the request. |
| Getting the record into SAP B1 | After MDM approval, the flow writes a **SAP Data Transfer Workbench** file (tab-delimited `.txt` with DTW's two header rows) to `SAP_Imports`, which only Owners can open. The file is one per request and per object: BusinessPartners, Items or ProfitCenters. The flow proposes the SAP code (e.g. `C20007`), writes it to the request, and tells the requestor. |

### Tested end to end (synthetic data, on our tenant)

| Request | What it showed |
|---|---|
| REQ-0004 (Customer) | Three stage-1 approvals in parallel, then MDM. Status *Created in SAP*, SAP file created, requestor notified in Teams. |
| REQ-0005 (regulated Item) | Quality/Regulatory added only because the item is regulated. With Assigned dates back-dated: a reminder at 3 days, an escalation to `EscalateTo` at 5 days. |
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
        └── (My requests) Roles, ApprovalLog   └─ SAP DTW file → SAP_Imports, status, Teams    ┘
                                            Flow: Reminders and escalation (hourly, 9 AM local) ─▶ ApprovalLog
```

### Rebuild it in another Microsoft 365 tenant

The app and flows are generated from code in this repo. Rebuilding takes about an hour of clicking and needs no premium licences.

1. **Team and lists.** Create a Teams team (this also creates its SharePoint site). For each CSV in `sharepoint/`, use
   **New → List → From CSV**, keeping the file name as the list name. The three lists that start empty (Requests,
   SensitiveDetails, ApprovalLog) import from `sharepoint/import/`, which has one test row each; delete that row afterwards.
   Creating lists from CSV matters, because the flows use SharePoint's generated internal names (`field_1`, `field_2`, … in CSV order).
   Set these column types and leave the rest as single line of text:
   - **Requests:** `SubmittedAt`, `CompletedAt` = Date and time; `IsRegulated`, `SuppliesRegulatedGoods` = Yes/No;
     `ShelfLifeMonths`, `BudgetYear` = Number. SharePoint imports `ContactEmail` as a Person column; delete it
     and create a single-line text column called `ContactEmail`. Then add a single-line text column `ManufacturerPartNo`.
   - **SensitiveDetails:** `CreditLimit` = Number. **ApprovalLog:** `Timestamp` = Date and time.
   - **BusinessUnits:** `Active` = Yes/No. **ItemMaster:** `Regulated` = Yes/No.
   - **RoutingRules:** `Stage`, `SLADays`, `EscalateAfterDays` = Number; `Active` = Yes/No.
2. **People and permissions.**
   - **Roles:** put real email addresses in `PersonEmail` and `EscalateTo`.
   - **SensitiveDetails:** in Advanced settings, set *Read items that were created by the user* and *Create items and edit items
     that were created by the user*. Then stop inheriting permissions and give Finance and MDM **Design**.
   - **ApprovalLog:** stop inheriting permissions and set Members to **Read**.
   - Create a `SAP_Imports` folder in Documents, stop inheriting permissions, and remove Members and Visitors.
3. **Power App.**
   1. Create a blank tablet canvas app and add these SharePoint lists as data: Requests, SensitiveDetails,
      RequiredFields, BusinessUnits, CustomerMaster, ItemMaster, Aliases, VendorMaster, CostCentres, Roles and ApprovalLog.
   2. Add a blank screen named `MyRequestsScreen`.
   3. Run `python3 powerapps/gen_form.py powerapps/NewRequestForm/Src`, then paste the three files in `powerapps/paste/`:
      `1-App-Formulas.txt` into **App → Formulas**, `2-ScreenContainer1.yaml` onto **Screen1 → Paste code**, and
      `3-MyRequestsScreen-ScreenContainer2.yaml` onto **MyRequestsScreen → Paste code**.
   4. Save and publish.
4. **Flows.**
   1. In `powerautomate/pkg.py`, set `SITE` to your site URL and `LISTS` to your list IDs. The ID is the `List=` value in each list's settings URL.
   2. Run `python3 powerautomate/build_route_approve.py` and `python3 powerautomate/build_reminders.py`.
   3. In Power Automate, go to **Import → Import Package (Legacy)** and import each zip, choosing your SharePoint, Approvals and Teams connections.
   4. Turn the flows on. If you re-import a flow later, the import creates a second copy: switch the old one off, so requests don't get two sets of approvals.
5. **Test.** Submit one request of each type, approve them in Teams, and run *OneRecord - Reminders (send now)* to see reminders.

### Limits we know about

- A rejection reaches the requestor only after **all** stage-1 approvers have answered, because the flow waits for the whole parallel step.
- Conditional routing understands two conditions (`IsRegulated`, `SuppliesRegulatedGoods`). A new kind of condition needs a flow change.
- RequiredFields can show, hide or require fields the app already has. A brand-new field needs an app change (one line in `gen_form.py`).
- The SAP file carries segment and payment terms as text ("Clinic", "45 days"). Real SAP uses numeric codes, so MDM would map them once.
- Duplicate checks are rule-based, so a misspelt name only gets a warning if all its main words still match. The bulk matcher
  in `onerecord/dedup.py` is typo-tolerant. In production, the form would call the same engine through one premium connector.
- Requests are picked up within a minute, because the SharePoint trigger polls the list.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Use the sidebar to switch persona (Amy, Wei Jie, Priya…) and to fast-forward the demo clock so reminders
and escalation fire. The optional AI step for ambiguous emails needs an `ANTHROPIC_API_KEY`; without one, those emails stay in human review.

### Demo script (Amy's story)

1. As **Amy**, open *New request*, choose Item, set regulated to **Yes** (the licence field appears) and type
   *Dengue NS1 rapid test 25T* to trigger the duplicate warning.
2. As **Wei Jie**, **QA** and the **BU Head**, open *Approvals* and approve. The three checks run at the same time.
3. In the sidebar, press **+3 days** on a stalled request to fire a reminder and an escalation.
4. As **Priya**, open *MDM check*, approve, and download the SAP file.
5. As **Priya**, open *Rules* and onboard Marcus's new BU. Then as **Marcus**, a *New request* for that BU routes to
   its own BU Head, with no IT change.
6. Finish on *Five-country growth*, *Forecasting* and *Sales actions*.

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
| `sharepoint/` | The SharePoint list templates (CSV), `import/` copies of the empty lists, and the `LISTS.md` design notes |
| `powerapps/` | The Power App's source: `gen_form.py` generates it, `NewRequestForm/Src` holds the unpacked app, and `paste/` holds the files to paste into Studio |
| `powerautomate/` | The flows: `build_route_approve.py` and `build_reminders.py` generate the importable packages (`*.zip`); `pkg.py` holds the shared settings |
| `NewRequestForm*.msapp` | Packed copies of the app (the paste route above is how it was actually loaded into Studio) |
| `data/`, `scripts/generate_data.py` | Synthetic dataset and its generator; `data/README.md` explains what's planted |

## Assumptions

- **All data is synthetic.** No client data was provided. The generator builds it to look like SAP B1 exports,
  with timings calibrated to the brief (2–3 weeks, Amy's 18 days). Validate every number in a pilot.
- **Entity → product mapping:** SPD = A (IVD reagents), QTS = B (lab consumables), QTG = C (equipment).
- **Growth measure:** year-on-year units, Apr–Sep 2026 vs Apr–Sep 2025, counting customer orders only.
- **Business case:** sales-driven benefits are counted at gross margin. Hours, rates and conversion rates are placeholders, adjustable on the
  *Business case* page.
