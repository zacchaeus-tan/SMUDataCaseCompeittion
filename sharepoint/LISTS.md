# SharePoint lists for the Lives Group prototype

Each CSV in this folder becomes one SharePoint list, which Power Apps and Power Automate read and write.
All of them use **standard connectors only** (no Premium licence needed).

## Setup

1. In Teams, create a team (e.g. *Lives Group MDM Prototype*) and add your teammates. This also creates a SharePoint site.
2. Open the site → **New → List → From CSV**, choose a file and check the column types (table below).
   Create the empty lists (`Requests`, `SensitiveDetails`, `ApprovalLog`) the same way. Their CSVs contain only headers.
3. Replace the `<teammate-n SMU email>` placeholders in **Roles** with real teammate emails. Approval cards are
   real messages, so **only use your own team's addresses**.
4. Lock down **SensitiveDetails**: List settings → Permissions → *Stop inheriting permissions*, then grant access
   only to whoever plays Finance and MDM. This is what actually protects bank details; hiding fields in the app is just for display.

## Lists

| List | Purpose | Who edits | Key columns (type) |
|---|---|---|---|
| **Requests** | One row per master data request | Power App (requestor), flow | `Title` = request ID, `RequestType` (Choice: Customer/Item/Vendor/Cost Center), `Entity` (Choice), `Status` (Text: Pending approval / Changes requested / Resubmitted / Rejected / Created in SAP), `CurrentStage` (Text), `SubmittedAt`/`CompletedAt` (Date & time), `IsRegulated`/`SuppliesRegulatedGoods` (Yes/No), `DuplicateCheck` (Choice: Clear/Possible match/Blocked), `PossibleMatchID`, `SAPCode` (Text), `RegulatedAnswer` (Text: Yes / No / Not sure; *Not sure* also sets `IsRegulated` so Quality/Regulatory is asked), `ChangeNote` (Multiple lines: one dated line per resubmit saying what changed); other fields Text |
| **SensitiveDetails** | Bank details, credit terms and limits, kept **separate** from Requests | Power App, flow | `RequestID` (Text), `PaymentTerms` (Choice), `CreditLimit` (Number), `BankName`, `BankAccount` (Text) |
| **ApprovalLog** | Log of every action; rows are only ever added | **Flow only** (give users Read access) | `RequestID`, `Timestamp` (Date & time), `Actor` (Person or Text), `ActorRole`, `Action`, `Detail`, `FieldChanged`, `OldValue`, `NewValue`. Log *that* a sensitive field changed, never its value. |
| **BusinessUnits** | The form's *Business entity* dropdown. A new BU = one row here + its BU Head in Roles | MDM team | `Title` = BU code, `BusinessUnitName`, `Products` (Text), `Active` (Yes/No) |
| **RoutingRules** | Who approves what; the MDM team edits rows instead of calling IT | MDM team | `RequestType`, `Entity`, `ConditionField`, `ConditionValue`, `ApproverRole` (Text), `Stage` (Number: 1 = parallel checks, 2 = MDM final), `SLADays`, `EscalateAfterDays` (Number), `Active` (Yes/No) |
| **RequiredFields** | Which fields the form shows and requires, per request type | MDM team | `RequestType`, `FieldName`, `DisplayLabel`, `FieldType`, `Required` (Always/Conditional), `ConditionField`, `ConditionValue`, `Sensitive` (Yes/No), `VisibleToRoles`, `HelpText`, `Check` (Text: the format check, one of None / Text / RegNo / HSCode / TaxID / LicenceNo / PartNo / BankAccount / Email / Months / Year; blank = the app's default) |
| **Roles** | Role → person, escalation contact and time zone | MDM team | `Role`, `Entity`, `PersonName`, `PersonEmail`, `EscalateTo` (Text), `TimeZone` (Text, e.g. `Asia/Bangkok`) |
| **CustomerMaster** | Copy of SAP customer records **without sensitive fields**, used for the duplicate search | Loaded from SAP (here: the CSV) | `Title` = record ID, `CustomerName`, `NormalizedName`, `Country`, `City`, `Address`, `RegistrationNo`, `Segment`, `CreatedByEntity` |
| **ItemMaster** | Same idea, for items | Loaded from SAP | `Title` = item code, `Description`, `NormalizedName`, `ProductFamily`, `Regulated` |
| **Aliases** | Known abbreviations → official record (e.g. `nuh`) | MDM team | `Title` = alias, `CanonicalName`, `RecordID` |

## Live duplicate check in Power Apps (no Premium needed)

`NormalizedName` is pre-computed as follows: lowercase, punctuation removed, legal suffixes removed
(pte, ltd, sdn, bhd, co, jsc, pt, inc, gmbh, ag, sa), and abbreviations expanded (hosp→hospital, ctr/center→centre,
univ→university, med→medical, lab→laboratory, diag→diagnostic, gen→general). Apply the same steps to what the
requestor types, then check:

1. **Registration number matches exactly** → block (*"This customer already exists: C10007"*).
2. **Alias hit**: the cleaned-up input is listed in `Aliases` → block, showing the official record.
3. **Name contains all the main words**: in the same country, `NormalizedName` contains each word of 4+ letters
   from the input (`Search`/`in` in Power Fx) → mark as *Possible match* and let the requestor confirm.

This is deliberately simpler than the Python fuzzy matching, which catches typos and runs in bulk across all
entities. **Pitch line:** *"In production, the form calls the same matching engine through one Premium connector."*

## Flows to build in Power Automate

1. **Route & approve**, triggered when an item is created in Requests:
   - Look up the active `RoutingRules` for this RequestType, including rows whose `ConditionField` matches the request's value.
   - For **Stage 1**, look up each approver in `Roles`, then run "Start and wait for an approval" for each one
     **in parallel** (an Apply to each loop with *Concurrency control* turned on, or parallel branches).
   - Write an ApprovalLog row for every outcome. Any rejection → set Status = Rejected, notify the requestor, stop.
   - Once all approve → **Stage 2** MDM approval → *Create CSV table* (SAP import file) → save to a
     `SAP_Imports` folder → Status = Created in SAP → notify the requestor in Teams.
2. **Reminders & escalation**, a scheduled daily flow:
   - Find Requests still Pending beyond `SLADays`.
   - Remind the approver in Teams; after `EscalateAfterDays`, message the `EscalateTo` person.
   - Count calendar days and send reminders at about 9 AM in the approver's own `TimeZone`, using the
     *Convert time zone* action. Approvers sit in UTC+7 (TH/VN/western ID) and UTC+8 (SG/MY).
3. **Status updates**: update `CurrentStage` at every step so the requestor's "My requests" screen is always current.
