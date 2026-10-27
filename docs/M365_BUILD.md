# Microsoft 365 build: the request workflow

*Part 2 of OneRecord. For the overview and the regional dashboard, see the [README](../README.md).*

The workflow half of OneRecord runs for real on Microsoft 365. We built it in a Teams team, using only
**standard connectors** (SharePoint, Approvals, Teams), so it needs no premium licence and no custom code on a server.

**On this page:** [What's built](#whats-built) · [Demo script](#demo-script-amys-story) ·
[Rebuild it in another tenant](#rebuild-it-in-another-microsoft-365-tenant) · [Limits we know about](#limits-we-know-about)

For how the pieces connect and what we tested end to end, see the README's
[Part 2](../README.md#part-2-request-workflow-microsoft-365).

## What's built

| Brief asks for | How the M365 build does it |
|---|---|
| A standard intake for Customer, Item, Vendor and Cost Center requests | **Power App "NewRequestForm"**, *New request* screen. It shows only the fields that apply. Labels, help text and required/conditional rules come from the **RequiredFields** list (e.g. *Regulatory licence no.* appears when an item is regulated). **Submit** stays disabled until the request is complete **and plausible**: placeholders such as *N/A*, *TBC* or *-* never pass, and each field has a format check (registration no. against the country's format: SG UEN, MY SSM, TH 13-digit tax ID, ID NPWP, VN MST; HS code 6–10 digits; generic checks for tax ID, licence, bank account). The problem shows in red under the field. MDM picks a field's check on the Rules screen (`RequiredFields.Check`). *Is this regulated?* has no default and offers **Not sure**, which sends the item to Quality/Regulatory to decide instead of skipping them; a hint shows whether the closest existing item is regulated. A *Who will approve* card shows the approvers by name before submitting, read from the same **RoutingRules** and **Roles** the flow uses, and says when a step has nobody set up. |
| No duplicates reaching an approver | Live checks while typing, against SAP's records **and** against requests already waiting for approval. **Names** (customer, item, vendor) are cleaned up and compared by the letter pairs they share, so typos still match: 82% or more similar is a *Possible match* (customers within the same country, items within the same product family). **IDs** (registration no., manufacturer part no., tax ID) are compared without punctuation, so `200288778-W` = `200288778W`: a match is *Blocked*, as is a known short name (`Aliases`) or a second cost centre for the same entity + department. A block names the existing code to use instead (records are shared by SPD, QTS and QTG). If the requestor is sure it's different, they switch on *Not the same* / *This is a different …* and **must give a reason**, which every approval card shows with a warning sign. The ID checks are direct lookups on an `IDKey` column and the name checks only load one country's or product family's records, so the check keeps working as the lists grow. The same logic is mirrored in `onerecord/livecheck.py`, which measures it. |
| Faster approvals | **Flow "OneRecord - Route and approve"**. It reads **RoutingRules** and **Roles** and sends every stage-1 check **in parallel** as an approval card in Teams/Outlook. Conditional rules (e.g. Quality/Regulatory only for regulated items) come from the list. The MDM Analyst approves last. Each card offers **Approve / Request changes / Reject**. *Request changes* sends the request back to the requestor at once (Teams message, status *Changes requested*); they press **Edit and resubmit** in *My requests*, the form opens with their answers filled in, and only the approver who asked sees it again. The others carry on meanwhile. Every edit is written to the request's **ChangeNote** (sensitive fields are named, never shown), which the re-check and the MDM final check display. A request not resubmitted within 14 days is closed. A rejection reaches the requestor straight away. |
| Requestors and approvers know where a request stands | Approvers get cards plus **"OneRecord - Reminders and escalation"**: a reminder at 9 AM in the approver's own time zone once `SLADays` pass. A stage-1 card not answered within **4 days** is **escalated**: the flow re-sends it to the approver *and* their `EscalateTo` (e.g. Wei Jie's manager while he's on leave), the first answer counts, and both get the daily reminder from then on. Only open requests are chased: once a request is rejected or cancelled, the other approvers' cards are left alone and later answers on them change nothing. MDM gets a 9 AM nudge for every request that has been *Ready for SAP import* for a day or more. Requestors get Teams messages on rejection, changes requested, approval and completion, each with a **link that opens the request** in the app (*My requests*, request selected). The app's **My requests** screen shows status, stage, days open, **who it is still waiting on**, a **timeline** of everything logged for the request, the submitted details and (permissions allowing) the sensitive details. The MDM team can switch to all requests. |
| Closing the email route | **Flow "OneRecord - Email auto-reply"** (standard Outlook connector) watches the MDM mailbox. When a staff member emails a master data request (same phrases as the email classifier), it replies with the form link and the rule that emailed requests aren't set up in SAP. Customers and our own replies are ignored. |
| A trustworthy record of who approved what | **ApprovalLog** list: every assignment, decision, reminder, escalation, routing gap and SAP file is a row. Team members have **read-only** access; only the flows (running as the owner) write to it. Sensitive values are never logged. **Every approval is pinned to the version it was given for**: each decision row records the request's SharePoint version, an approval given on an older version (sent before a resubmit) is logged as *Approval not counted* and asked again, and a request changed directly in SharePoint, outside *Edit and resubmit*, goes **On hold** with MDM told. Just before the SAP file is written, the request and its payment / bank details are read again and must match the approved version exactly, so SAP gets what was approved. |
| Protecting sensitive fields | Bank details and credit terms are saved to **SensitiveDetails**, separate from the request. Item-level permissions let requestors read only their own rows; Finance and MDM have Design access to read all. Approval cards for roles allowed to see them (from **RequiredFields → VisibleToRoles**) carry a **link** to the row, never the values, so nothing sensitive goes into Teams or email. |
| Changing rules, fields and approvers without IT | The app's **Rules** screen (MDM only) shows each request type's whole process in plain words: what the form asks for (*always*, or *only when Product family is A*) and who approves it (step 1 in parallel, then the MDM final check), with *Show for* to see one business's approvers by name. Every change is made in a short panel with dropdowns and tick-boxes that reads the rule back as a sentence before saving: **Add an approval step** (*Quality/Regulatory approves item requests for all businesses, only when Product family is D*), **Change** a field (always asked, or only for some values; label and help text), **Turn off** a step. **Businesses and people** lists each business and who approves for it, flags missing approvers, and has **Add a business unit** (code, name, product lines, BU Head) and **Add a person** (an existing or new role, for one business or all). **Product lines** lists each line with who sells it, its extra fields and approvals, and has **Add a product line** (code, name, seller, which optional fields it needs, an optional extra approver) in one form. **Advanced** keeps the raw list editor for anything else (format checks, known names, dropdown options). A *Needs attention* banner shows any business with nobody set up for a step and any step that can never apply. Under the hood these are rows in **RoutingRules**, **RequiredFields**, **Roles**, **BusinessUnits** and **ChoiceOptions**; the flow and the form read them on the next request. If a business has no approver for a step (Marcus's story), the request goes to the MDM Analyst instead of stalling, MDM is told in Teams, and the gap is logged and shown on the request. |
| Getting the record into SAP B1 | After MDM approval, the flow writes a **SAP Data Transfer Workbench** file (tab-delimited `.txt` with DTW's two header rows) to `SAP_Imports`, which only Owners can open. The file is one per request and per object: BusinessPartners, Items or ProfitCenters. The flow proposes the SAP code (e.g. `C20007`) and **adds the record to its master list straight away** (`SAPStatus` = *Pending SAP import*), so the next request's duplicate check already sees it. The request becomes **Ready for SAP import** and MDM gets a Teams message. After importing the file, MDM presses **Mark as created in SAP** in *My requests* (correcting the code if SAP gave another); only then does the status say *Created in SAP*, the master list row switch to *In SAP*, and the requestor hear that it's live. |
| Cleaning up duplicates already in SAP | Done in the dashboard, not in M365: the **MDM ops** page lists the duplicate groups the bulk matcher found (plus borderline pairs, unticked, for review). MDM confirms them and downloads DTW files that **freeze** the extra business partners and items, with a note naming the code to use, plus an old-to-new code list for reporting. Freezing keeps past orders in place; nothing is deleted. |

## Demo script (Amy's story)

1. As **Amy**, open the app from the Teams channel tab and start a *New request* for an Item. Set *Is this regulated?*
   to **Not sure** (Quality/Regulatory joins the *Who will approve* card), try *N/A* as the HS code to see it
   blocked, and type *Dengue NS1 rapid test 25T* to get the *Possible match* warning (item A-1001).
2. As the **BU Head**, **Finance (Wei Jie)** and **Quality/Regulatory**, approve the cards in Teams. The three checks
   run at the same time; *My requests* shows who it is still waiting on.
3. Run the flow *OneRecord - Reminders (send now)* to fire reminders without waiting for 9 AM.
4. As **Priya**, approve the MDM card. The SAP file appears in `SAP_Imports`; press **Mark as created in SAP** in
   *My requests*, and Amy gets a Teams message that the record is live.
5. As **Priya**, open *Rules* → *Add a business unit* and onboard Marcus's new BU. Then as **Marcus**, a *New request*
   for that BU routes to its own BU Head, with no IT change.

## Rebuild it in another Microsoft 365 tenant

The app and flows are generated from code in this repo. Rebuilding takes about an hour of clicking and needs no premium licences.

### 1. Team and lists

Create a Teams team (this also creates its SharePoint site). For each CSV in `sharepoint/`, use
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

### 2. People and permissions

- **Roles:** put real email addresses in `PersonEmail` and `EscalateTo`.
- **SensitiveDetails:** in Advanced settings, set *Read items that were created by the user* and *Create items and edit items
  that were created by the user*. Then stop inheriting permissions and give Finance and MDM **Design**.
- **ApprovalLog:** stop inheriting permissions and set Members to **Read**.
- Create a `SAP_Imports` folder in Documents, stop inheriting permissions, and remove Members and Visitors.

### 3. Power App

1. Create a blank tablet canvas app and add these SharePoint lists as data: Requests, SensitiveDetails,
   RequiredFields, BusinessUnits, CustomerMaster, ItemMaster, Aliases, VendorMaster, CostCentres, Roles, RoutingRules, ApprovalLog and ChoiceOptions.
2. Add two blank screens named `MyRequestsScreen` and `AdminScreen`.
3. Run `python3 powerapps/gen_form.py powerapps/NewRequestForm/Src`, then paste the four files in `powerapps/paste/`:
   `1-App-Formulas.txt` into **App → Formulas**, `2-ScreenContainer1.yaml` onto **NewRequestScreen → Paste code**,
   `3-MyRequestsScreen-ScreenContainer2.yaml` onto **MyRequestsScreen → Paste code**, and
   `4-AdminScreen-ScreenContainer3.yaml` onto **AdminScreen → Paste code**.
4. Set **App → StartScreen** to `If(IsBlank(Param("requestId")), NewRequestScreen, MyRequestsScreen)`, so the links in Teams messages open *My requests*.
5. Save and publish.
6. **Pin it in Teams:** in the team's channel, press **+** (Add a tab) → **Power Apps** → choose the app → **Save**. Requestors then open it from the channel instead of hunting for a link.

### 4. Flows

1. In `powerautomate/pkg.py`, set `SITE` to your site URL and `LISTS` to your list IDs. The ID is the `List=` value in each list's settings URL.
2. Also set `APP_URL` (the app's web link) and `INTERNAL_DOMAIN` (staff email domain) in `pkg.py`. Run
   `python3 powerautomate/build_route_approve.py`, `python3 powerautomate/build_reminders.py` and
   `python3 powerautomate/build_email_autoreply.py`.
3. In Power Automate, go to **Import → Import Package (Legacy)** and import each zip, choosing your SharePoint, Approvals and Teams connections (Office 365 Outlook for the auto-reply, signed in as the mailbox it should watch).
4. Turn the flows on. If you re-import a flow later, the import creates a second copy: switch the old one off, so requests don't get two sets of approvals.

### 5. Test

Submit one request of each type, approve them in Teams, and run *OneRecord - Reminders (send now)* to see reminders.

## Limits we know about

**Approvals and escalation**

- Escalation time is fixed in the flow (`ESCALATE_AFTER` in `pkg.py`, 4 days): an approval card's timeout can't be read from a list, so `RoutingRules.EscalateAfterDays` is a note that should match it. To demo escalation, build a copy with `ESCALATE_AFTER=PT10M python3 powerautomate/build_route_approve.py`. The approver's original card stays in their Approvals list after it's re-sent, but answering it no longer changes anything (the new card says so). If the re-sent card is not answered within 20 days, the request is cancelled and the requestor told. MDM's own card is not escalated.
- While a request is sent back, the other approvers' cards stay open on the values they saw. Their decision still counts; the MDM final check shows what changed afterwards (ChangeNote). The approval steps are fixed at submission, so switching *regulated* from No to Yes during an edit doesn't add Quality/Regulatory; MDM sees that change.
- *Cancel request* on an approval card (only the flow's owner sees it) withdraws the request: status *Cancelled*, the requestor is told, and it's logged. Any result other than Approve / Reject / Request changes counts as cancelled, so nothing slips through as approved. As with a rejection, the flow still waits for the other parallel cards before it finishes, but their answers no longer change the request and they are not reminded.
- *Reassign* works, and Teams tells the new approver. The standard connectors don't report a reassignment until the card is answered, so the log records *Reassigned (from → to)* at that point, and reminders still go to the original approver (worded so they can ignore it). Following the card live would need the premium Dataverse connector.

**Timing**

- Requests are picked up within a minute, because the SharePoint trigger polls the list.
- The flow checks for a resubmit every 5 minutes, so a resubmitted request reaches the approver within about 5 minutes.
- The flow waits for *Mark as created in SAP* by checking every 5 minutes for up to about 17 days; after that it reminds MDM and stops waiting.

**Form and rules**

- Format checks are deliberately simple patterns (no checksum). The MY check also accepts 14 digits, because the synthetic data uses 14-digit SSM numbers; real SSM numbers have 12.
- An approval step can depend on seven fields (Country, ProductFamily, IsRegulated, SuppliesRegulatedGoods, Segment, UnitOfMeasure, Department), compared with *equals one of*. Vendor country is free text, so a vendor rule needs the country as typed (e.g. `Indonesia`). Another field, or a test such as *not equal* or *credit limit above*, needs a flow and app change.
- Payment terms stay a fixed list in the app (Finance owns them); the other dropdowns come from **ChoiceOptions**. A new country has no registration-no. format check until one is added to the app.
- The Rules screen is hidden from everyone but the MDM Analyst in **Roles**, but that is display only. To stop others editing the rule lists directly in SharePoint, give Members **Read** on them.
- RequiredFields can show, hide or require fields the app already has. A brand-new field is a planned app release (about half a day): a SharePoint column, an entry in `gen_form.py` (control, label, check, save), its SAP file column in the flow, then regenerate, paste and re-import.

**Duplicate check**

- The form's name check compares letter pairs; it doesn't use address or city like the bulk matcher, so two branches of one chain in the same country (e.g. *Mercy Medical Clinic Bandung* vs *Medical Clinic Bandung*) can get a warning. That's why it only warns and asks for a reason.
- The 82% threshold was tuned on our synthetic duplicates. Re-check it on real SAP data in the pilot (`onerecord/livecheck.py` measures it).
- Vendors are compared across all countries, because the vendor country is free text. With thousands of vendors this list would need a country or first-letter filter.

**SAP file**

- The SAP file carries segment and payment terms as text ("Clinic", "45 days"). Real SAP uses numeric codes, so MDM would map them once.
