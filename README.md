# OneRecord: clean master data and a five-country regional view for Lives Group

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

**Process flow, person by person, from request to SAP B1 to the regional view:** [docs/PROCESS_FLOW.md](docs/PROCESS_FLOW.md).

## Results (on synthetic data, see *Assumptions*)

- **Request → SAP:** median 18.8 → **about 4–6 days**, simulated on the same 150 requests. Parallel approvals and the
  smart form alone give about 6 days (slowest 10%: 28 → about 6) even if notifications and reminders changed nothing.
  If half of each approver's wait was "not seeing it" and reminders remove that, it's about 4 days (slowest 10%: about 6).
- **Duplicates, two layers.** *Stopping new ones:* the request form flags all 41 planted duplicates when each is typed
  in as a new request, from the name alone (typos included); 6 of 205 genuinely new customers (3%) get a warning, which
  only asks for a reason. *Cleaning up old ones:* the bulk matcher finds the 41 duplicate records among 246 (17%),
  100% precision and recall on the synthetic answer key, with look-alikes sent to human review. Both figures are on
  data we generated, so validate them in a pilot.
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

## Microsoft 365 build

The workflow half of OneRecord also runs for real on Microsoft 365. We built it in a Teams team, using only
**standard connectors** (SharePoint, Approvals, Teams), so it needs no premium licence and no custom code on a server.
The Streamlit app remains the place for the regional business view and forecasting (Power BI in production).

### What's built

| Brief asks for | How the M365 build does it |
|---|---|
| A standard intake for Customer, Item, Vendor and Cost Center requests | **Power App "NewRequestForm"**, *New request* screen. It shows only the fields that apply. Labels, help text and required/conditional rules come from the **RequiredFields** list (e.g. *Regulatory licence no.* appears when an item is regulated). **Submit** stays disabled until the request is complete **and plausible**: placeholders such as *N/A*, *TBC* or *-* never pass, and each field has a format check (registration no. against the country's format: SG UEN, MY SSM, TH 13-digit tax ID, ID NPWP, VN MST; HS code 6–10 digits; generic checks for tax ID, licence, bank account). The problem shows in red under the field. MDM picks a field's check on the Rules screen (`RequiredFields.Check`). *Is this regulated?* has no default and offers **Not sure**, which sends the item to Quality/Regulatory to decide instead of skipping them; a hint shows whether the closest existing item is regulated. A *Who will approve* card shows the approvers by name before submitting, read from the same **RoutingRules** and **Roles** the flow uses, and says when a step has nobody set up. |
| No duplicates reaching an approver | Live checks while typing, against SAP's records **and** against requests already waiting for approval. **Names** (customer, item, vendor) are cleaned up and compared by the letter pairs they share, so typos still match: 82% or more similar is a *Possible match* (customers within the same country, items within the same product family). **IDs** (registration no., manufacturer part no., tax ID) are compared without punctuation, so `200288778-W` = `200288778W`: a match is *Blocked*, as is a known short name (`Aliases`) or a second cost centre for the same entity + department. A block names the existing code to use instead (records are shared by SPD, QTS and QTG). If the requestor is sure it's different, they switch on *Not the same* / *This is a different …* and **must give a reason**, which every approval card shows with a warning sign. The ID checks are direct lookups on an `IDKey` column and the name checks only load one country's or product family's records, so the check keeps working as the lists grow. The same logic is mirrored in `onerecord/livecheck.py`, which measures it. |
| Faster approvals | **Flow "OneRecord - Route and approve"**. It reads **RoutingRules** and **Roles** and sends every stage-1 check **in parallel** as an approval card in Teams/Outlook. Conditional rules (e.g. Quality/Regulatory only for regulated items) come from the list. The MDM Analyst approves last. Each card offers **Approve / Request changes / Reject**. *Request changes* sends the request back to the requestor at once (Teams message, status *Changes requested*); they press **Edit and resubmit** in *My requests*, the form opens with their answers filled in, and only the approver who asked sees it again. The others carry on meanwhile. Every edit is written to the request's **ChangeNote** (sensitive fields are named, never shown), which the re-check and the MDM final check display. A request not resubmitted within 14 days is closed. A rejection now reaches the requestor straight away. |
| Requestors and approvers know where a request stands | Approvers get cards plus **"OneRecord - Reminders and escalation"**: a reminder at 9 AM in the approver's own time zone once `SLADays` pass. A stage-1 card not answered within **4 days** is **escalated**: the flow re-sends it to the approver *and* their `EscalateTo` (e.g. Wei Jie's manager while he's on leave), the first answer counts, and both get the daily reminder from then on. Only open requests are chased: once a request is rejected or cancelled, the other approvers' cards are left alone and later answers on them change nothing. MDM gets a 9 AM nudge for every request that has been *Ready for SAP import* for a day or more. Requestors get Teams messages on rejection, changes requested, approval and completion, each with a **link that opens the request** in the app (*My requests*, request selected). The app's **My requests** screen shows status, stage, days open, **who it is still waiting on**, a **timeline** of everything logged for the request, the submitted details and (permissions allowing) the sensitive details. The MDM team can switch to all requests. |
| Closing the email route | **Flow "OneRecord - Email auto-reply"** (standard Outlook connector) watches the MDM mailbox. When a staff member emails a master data request (same phrases as the email classifier), it replies with the form link and the rule that emailed requests aren't set up in SAP. Customers and our own replies are ignored. |
| A trustworthy record of who approved what | **ApprovalLog** list: every assignment, decision, reminder, escalation, routing gap and SAP file is a row. Team members have **read-only** access; only the flows (running as the owner) write to it. Sensitive values are never logged. |
| Protecting sensitive fields | Bank details and credit terms are saved to **SensitiveDetails**, separate from the request. Item-level permissions let requestors read only their own rows; Finance and MDM have Design access to read all. Approval cards for roles allowed to see them (from **RequiredFields → VisibleToRoles**) carry a **link** to the row, never the values, so nothing sensitive goes into Teams or email. |
| Changing rules, fields and approvers without IT | The app's **Rules** screen (MDM only) puts every rule in one place: a *rules check* that lists any business unit with nobody set up for an approval step, an **Add a business unit** form (creates the BU and its BU Head in one step), and editable tables for business units, approval steps, form fields, people and known names. New rows start switched off or blank, so a half-finished row can't change routing. Under the hood these are list rows: A new business unit is a **BusinessUnits** row plus its people in **Roles**. A new approval step is a **RoutingRules** row. Making a field required or conditional is a **RequiredFields** row. If a business unit has no approver for a step yet (Marcus's story), the request goes to the MDM Analyst instead of stalling. MDM is told in Teams, and the gap is logged and shown on the request. |
| Getting the record into SAP B1 | After MDM approval, the flow writes a **SAP Data Transfer Workbench** file (tab-delimited `.txt` with DTW's two header rows) to `SAP_Imports`, which only Owners can open. The file is one per request and per object: BusinessPartners, Items or ProfitCenters. The flow proposes the SAP code (e.g. `C20007`) and **adds the record to its master list straight away** (`SAPStatus` = *Pending SAP import*), so the next request's duplicate check already sees it. The request becomes **Ready for SAP import** and MDM gets a Teams message. After importing the file, MDM presses **Mark as created in SAP** in *My requests* (correcting the code if SAP gave another); only then does the status say *Created in SAP*, the master list row switch to *In SAP*, and the requestor hear that it's live. |
| Cleaning up duplicates already in SAP | The Streamlit **MDM ops** page lists the duplicate groups the bulk matcher found (plus borderline pairs, unticked, for review). MDM confirms them and downloads DTW files that **freeze** the extra business partners and items, with a note naming the code to use, plus an old-to-new code list for reporting. Freezing keeps past orders in place; nothing is deleted. |

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

### Rebuild it in another Microsoft 365 tenant

The app and flows are generated from code in this repo. Rebuilding takes about an hour of clicking and needs no premium licences.

1. **Team and lists.** Create a Teams team (this also creates its SharePoint site). For each CSV in `sharepoint/`, use
   **New → List → From CSV**, keeping the file name as the list name. The three lists that start empty (Requests,
   SensitiveDetails, ApprovalLog) import from `sharepoint/import/`, which has one test row each; delete that row afterwards.
   Creating lists from CSV matters, because the flows use SharePoint's generated internal names (`field_1`, `field_2`, … in CSV order).
   Set these column types and leave the rest as single line of text:
   - **Requests:** `SubmittedAt`, `CompletedAt` = Date and time; `IsRegulated`, `SuppliesRegulatedGoods` = Yes/No;
     `ShelfLifeMonths`, `BudgetYear` = Number. SharePoint imports `ContactEmail` as a Person column; delete it
     and create a single-line text column called `ContactEmail`. Then add single-line text columns `ManufacturerPartNo`
     and `RegulatedAnswer`, and a **multiple lines of text** column (plain text) called `ChangeNote`.
   - **RequiredFields:** if your list predates the `Check` column, add it as a single-line text column (blank = the app's default check).
   - **Duplicate check:** run `python3 sharepoint/match_keys.py` before importing the master list CSVs (it adds
     `MatchKey`, `IDKey` and `SAPStatus`). On Requests, add single-line text columns `MatchKey`, `IDKey` and `DupReason`.
     In the app's settings, set the data row limit to 2,000.
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
      RequiredFields, BusinessUnits, CustomerMaster, ItemMaster, Aliases, VendorMaster, CostCentres, Roles, RoutingRules and ApprovalLog.
   2. Add two blank screens named `MyRequestsScreen` and `AdminScreen`.
   3. Run `python3 powerapps/gen_form.py powerapps/NewRequestForm/Src`, then paste the four files in `powerapps/paste/`:
      `1-App-Formulas.txt` into **App → Formulas**, `2-ScreenContainer1.yaml` onto **NewRequestScreen → Paste code**,
      `3-MyRequestsScreen-ScreenContainer2.yaml` onto **MyRequestsScreen → Paste code**, and
      `4-AdminScreen-ScreenContainer3.yaml` onto **AdminScreen → Paste code**.
   4. Set **App → StartScreen** to `If(IsBlank(Param("requestId")), NewRequestScreen, MyRequestsScreen)`, so the links in Teams messages open *My requests*.
   5. Save and publish.
   6. **Pin it in Teams:** in the team's channel, press **+** (Add a tab) → **Power Apps** → choose the app → **Save**. Requestors then open it from the channel instead of hunting for a link.
4. **Flows.**
   1. In `powerautomate/pkg.py`, set `SITE` to your site URL and `LISTS` to your list IDs. The ID is the `List=` value in each list's settings URL.
   2. Also set `APP_URL` (the app's web link) and `INTERNAL_DOMAIN` (staff email domain) in `pkg.py`. Run
      `python3 powerautomate/build_route_approve.py`, `python3 powerautomate/build_reminders.py` and
      `python3 powerautomate/build_email_autoreply.py`.
   3. In Power Automate, go to **Import → Import Package (Legacy)** and import each zip, choosing your SharePoint, Approvals and Teams connections (Office 365 Outlook for the auto-reply, signed in as the mailbox it should watch).
   4. Turn the flows on. If you re-import a flow later, the import creates a second copy: switch the old one off, so requests don't get two sets of approvals.
5. **Test.** Submit one request of each type, approve them in Teams, and run *OneRecord - Reminders (send now)* to see reminders.

### Limits we know about

- Escalation time is fixed in the flow (`ESCALATE_AFTER` in `pkg.py`, 4 days): an approval card's timeout can't be read from a list, so `RoutingRules.EscalateAfterDays` is now a note that should match it. To demo escalation, build a copy with `ESCALATE_AFTER=PT10M python3 powerautomate/build_route_approve.py`. The approver's original card stays in their Approvals list after it's re-sent, but answering it no longer changes anything (the new card says so). If the re-sent card is not answered within 20 days, the request is cancelled and the requestor told. MDM's own card is not escalated.
- While a request is sent back, the other approvers' cards stay open on the values they saw. Their decision still counts; the MDM final check shows what changed afterwards (ChangeNote). The approval steps are fixed at submission, so switching *regulated* from No to Yes during an edit doesn't add Quality/Regulatory; MDM sees that change.
- *Cancel request* on an approval card (only the flow's owner sees it) withdraws the request: status *Cancelled*, the requestor is told, and it's logged. Any result other than Approve / Reject / Request changes counts as cancelled, so nothing slips through as approved. As with a rejection, the flow still waits for the other parallel cards before it finishes, but their answers no longer change the request and they are not reminded.
- *Reassign* works, and Teams tells the new approver. The standard connectors don't report a reassignment until the card is answered, so the log records *Reassigned (from → to)* at that point, and reminders still go to the original approver (worded so they can ignore it). Following the card live would need the premium Dataverse connector.
- The flow checks for a resubmit every 5 minutes, so a resubmitted request reaches the approver within about 5 minutes.
- Format checks are deliberately simple patterns (no checksum). The MY check also accepts 14 digits, because the synthetic data uses 14-digit SSM numbers; real SSM numbers have 12.
- Conditional routing understands two conditions (`IsRegulated`, `SuppliesRegulatedGoods`). A new kind of condition needs a flow change.
- The Rules screen is hidden from everyone but the MDM Analyst in **Roles**, but that is display only. To stop others editing the rule lists directly in SharePoint, give Members **Read** on them.
- RequiredFields can show, hide or require fields the app already has. A brand-new field needs an app change (one line in `gen_form.py`).
- The SAP file carries segment and payment terms as text ("Clinic", "45 days"). Real SAP uses numeric codes, so MDM would map them once.
- The form's name check compares letter pairs; it doesn't use address or city like the bulk matcher, so two branches of one chain in the same country (e.g. *Mercy Medical Clinic Bandung* vs *Medical Clinic Bandung*) can get a warning. That's why it only warns and asks for a reason.
- The 82% threshold was tuned on our synthetic duplicates. Re-check it on real SAP data in the pilot (`onerecord/livecheck.py` measures it).
- Vendors are compared across all countries, because the vendor country is free text. With thousands of vendors this list would need a country or first-letter filter.
- The flow waits for *Mark as created in SAP* by checking every 5 minutes for up to about 17 days; after that it reminds MDM and stops waiting.
- Requests are picked up within a minute, because the SharePoint trigger polls the list.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The Streamlit app is the regional business view (switch user at the bottom of the sidebar; Priya sees *MDM ops*).
The request workflow is demoed in the Microsoft 365 build; the older Streamlit mock-up of it is hidden
(`SHOW_WORKFLOW_MOCKUP` in `app.py`). The optional AI step for ambiguous emails and the AI action brief need an `OPENAI_API_KEY`
(model `gpt-5.4-nano` by default; set `OPENAI_MODEL` to change it). Without a key, those emails stay in human review.

### Demo script (Amy's story)

1. As **Amy**, open *New request*, choose Item, set regulated to **Not sure** (Quality/Regulatory joins the approvers; try *N/A* as the HS code to see it blocked) and type
   *Dengue NS1 rapid test 25T* to trigger the duplicate warning.
2. As **Wei Jie**, **QA** and the **BU Head**, open *Approvals* and approve. The three checks run at the same time.
3. In the sidebar, press **+3 days** on a stalled request to fire a reminder and an escalation.
4. As **Priya**, open *MDM check*, approve, and download the SAP file.
5. As **Priya**, open *Rules* and onboard Marcus's new BU. Then as **Marcus**, a *New request* for that BU routes to
   its own BU Head, with no IT change.
6. Finish on *Country deep-dive*, *Forecasting* and *Customers*.

## Repository map

| Path | What |
|---|---|
| `docs/PROCESS_FLOW.md` | The end-to-end process with a diagram: request, parallel approvals, SAP B1 import, regional view |
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
