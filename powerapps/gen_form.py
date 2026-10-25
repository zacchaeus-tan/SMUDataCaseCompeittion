"""Generate the OneRecord NewRequestForm canvas app source: App formulas, NewRequestScreen,
MyRequestsScreen and AdminScreen (rules, MDM only).

Usage: python3 powerapps/gen_form.py powerapps/NewRequestForm/Src
Then paste powerapps/paste/* into Studio (App > Formulas, and each screen > Paste code).
"""
import sys
from pathlib import Path

SRC = Path(sys.argv[1])

HEADER = """# ************************************************************************************************
# Warning: YAML source code for Canvas Apps should only be used to review changes made within Power Apps Studio and for minor edits (Preview).
# Use the maker portal to create and edit your Power Apps.
#
# The schema file for Canvas Apps is available at https://go.microsoft.com/fwlink/?linkid=2304907
#
# For more information, visit https://go.microsoft.com/fwlink/?linkid=2292623
# ************************************************************************************************
"""

# ---------------------------------------------------------------------------- styles (copied from Studio samples)
LABEL = {"BorderColor": "RGBA(0, 0, 0, 0)", "BorderStyle": "BorderStyle.None", "BorderThickness": "2",
         "Color": "RGBA(50, 49, 48, 1)", "DisabledBorderColor": "RGBA(0, 0, 0, 0)",
         "DisabledColor": "RGBA(161, 159, 157, 1)", "FocusedBorderThickness": "4", "Font": "Font.'Segoe UI'",
         "LayoutMinHeight": "16", "LayoutMinWidth": "16"}
TEXTINPUT = {"BorderColor": "RGBA(200, 198, 196, 1)", "Color": "RGBA(50, 49, 48, 1)",
             "DisabledBorderColor": "RGBA(0, 0, 0, 0)", "DisabledColor": "RGBA(161, 159, 157, 1)",
             "DisabledFill": "RGBA(242, 242, 241, 0)", "Fill": "RGBA(255, 255, 255, 1)", "Font": "Font.'Segoe UI'",
             "HoverBorderColor": "RGBA(16, 110, 190, 1)", "HoverColor": "RGBA(50, 49, 48, 1)",
             "HoverFill": "RGBA(255, 255, 255, 1)", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
             "PressedBorderColor": "RGBA(0, 120, 212, 1)", "PressedColor": "RGBA(50, 49, 48, 1)",
             "PressedFill": "RGBA(255, 255, 255, 1)", "RadiusBottomLeft": "4", "RadiusBottomRight": "4",
             "RadiusTopLeft": "4", "RadiusTopRight": "4"}
DROPDOWN = {"BorderColor": "RGBA(200, 198, 196, 1)", "ChevronBackground": "RGBA(255, 255, 255, 1)",
            "ChevronDisabledBackground": "RGBA(242, 242, 241, 0)", "ChevronDisabledFill": "RGBA(161, 159, 157, 1)",
            "ChevronFill": "RGBA(50, 49, 48, 1)", "ChevronHoverBackground": "RGBA(245, 245, 245, 1)",
            "ChevronHoverFill": "RGBA(50, 49, 48, 1)", "Color": "RGBA(50, 49, 48, 1)",
            "DisabledBorderColor": "RGBA(0, 0, 0, 0)", "DisabledColor": "RGBA(161, 159, 157, 1)",
            "DisabledFill": "RGBA(242, 242, 241, 0)", "Fill": "RGBA(255, 255, 255, 1)", "Font": "Font.'Segoe UI'",
            "HoverBorderColor": "RGBA(16, 110, 190, 1)", "HoverColor": "RGBA(50, 49, 48, 1)",
            "HoverFill": "RGBA(245, 245, 245, 1)", "Items.Value": "Value", "LayoutMinHeight": "16",
            "LayoutMinWidth": "16", "PaddingBottom": "5", "PaddingLeft": "12", "PaddingRight": "5",
            "PaddingTop": "5", "PressedBorderColor": "RGBA(16, 110, 190, 1)", "PressedColor": "RGBA(255, 255, 255, 1)",
            "PressedFill": "RGBA(0, 120, 212, 1)", "SelectionColor": "RGBA(50, 49, 48, 1)",
            "SelectionFill": "RGBA(0, 120, 212, 1)"}
TOGGLE = {"BorderColor": "RGBA(0, 0, 0, 0)", "BorderStyle": "BorderStyle.None", "Color": "RGBA(50, 49, 48, 1)",
          "DisabledBorderColor": "RGBA(0, 0, 0, 0)", "FalseFill": "RGBA(96, 94, 92, 1)",
          "FalseHoverFill": "RGBA(50, 49, 48, 1)", "FocusedBorderThickness": "4", "Font": "Font.'Segoe UI'",
          "HoverBorderColor": "RGBA(0, 0, 0, 0)", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
          "PressedBorderColor": "RGBA(0, 0, 0, 0)", "TrueFill": "RGBA(0, 120, 212, 1)",
          "TrueHoverFill": "RGBA(16, 110, 190, 1)"}
BUTTON = {"BorderColor": "RGBA(0, 0, 0, 0)", "BorderStyle": "BorderStyle.None", "Color": "RGBA(255, 255, 255, 1)",
          "DisabledBorderColor": "RGBA(0, 0, 0, 0)", "DisabledColor": "RGBA(161, 159, 157, 1)",
          "DisabledFill": "RGBA(237, 235, 233, 1)", "Fill": "RGBA(0, 120, 212, 1)", "Font": "Font.'Segoe UI'",
          "HoverBorderColor": "RGBA(0, 0, 0, 0)", "HoverColor": "RGBA(255, 255, 255, 1)",
          "HoverFill": "RGBA(16, 110, 190, 1)", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
          "PressedBorderColor": "RGBA(0, 69, 120, 1)", "PressedColor": "RGBA(255, 255, 255, 1)",
          "PressedFill": "RGBA(16, 110, 190, 1)", "RadiusBottomLeft": "4", "RadiusBottomRight": "4",
          "RadiusTopLeft": "4", "RadiusTopRight": "4"}
CARD = {"Fill": "RGBA(255, 255, 255, 1)", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
        "PaddingBottom": "8", "PaddingLeft": "8", "PaddingRight": "8", "PaddingTop": "8",
        "RadiusBottomLeft": "8", "RadiusBottomRight": "8", "RadiusTopLeft": "8", "RadiusTopRight": "8"}

GREY = "RGBA(96, 94, 92, 1)"

TYPES = ["Customer", "Item", "Vendor", "Cost Center"]
COUNTRIES = ["SG", "MY", "TH", "ID", "VN"]
CHOICES = {
    "Segment": ["Hospital", "Laboratory", "Clinic"],
    "PaymentTerms": ["30 days", "45 days", "60 days", "90 days", "Advance"],
    "ProductFamily": ["A", "B", "C"],
    "UnitOfMeasure": ["Kit", "Box", "Pack", "Unit", "Set"],
    "Department": ["Sales", "Marketing", "Regulatory Affairs", "Service", "Finance", "Warehouse"],
    # No default: the requestor has to answer. "Not sure" sends the item to Quality/Regulatory to decide.
    "IsRegulated": ["Yes", "No", "Not sure"],
}

# (request type, FieldName in RequiredFields, control name, kind, extra)
# kind: text | number | email | choice | country | toggle
FIELDS = [
    ("Customer", "CustomerName", "txtCustomerName", "text", {}),
    ("Customer", "Country", "ddCustomerCountry", "country", {}),
    ("Customer", "RegistrationNo", "txtRegistrationNo", "text", {}),
    ("Customer", "BillingAddress", "txtBillingAddress", "text", {}),
    ("Customer", "ContactEmail", "txtContactEmail", "email", {}),
    ("Customer", "Segment", "ddSegment", "choice", {}),
    ("Customer", "PaymentTerms", "ddCustomerPaymentTerms", "choice", {}),
    ("Customer", "CreditLimit", "txtCreditLimit", "number", {}),
    ("Item", "ItemDescription", "txtItemDescription", "text", {}),
    ("Item", "ManufacturerPartNo", "txtManufacturerPartNo", "text", {}),
    ("Item", "ProductFamily", "ddProductFamily", "choice", {}),
    ("Item", "UnitOfMeasure", "ddUnitOfMeasure", "choice", {}),
    ("Item", "HSCode", "txtHSCode", "text", {}),
    ("Item", "IsRegulated", "ddIsRegulated", "choice", {"help": "RegulatedHint"}),
    ("Item", "RegulatoryLicenceNo", "txtRegulatoryLicenceNo", "text", {}),
    ("Item", "ShelfLifeMonths", "txtShelfLifeMonths", "number", {}),
    ("Vendor", "VendorName", "txtVendorName", "text", {}),
    ("Vendor", "Country", "txtVendorCountry", "text", {}),
    ("Vendor", "TaxID", "txtTaxID", "text", {}),
    ("Vendor", "SuppliesRegulatedGoods", "tglSuppliesRegulatedGoods", "toggle", {}),
    ("Vendor", "ISO13485CertNo", "txtISO13485CertNo", "text", {}),
    ("Vendor", "BankName", "txtBankName", "text", {}),
    ("Vendor", "BankAccount", "txtBankAccount", "text", {}),
    ("Vendor", "PaymentTerms", "ddVendorPaymentTerms", "choice", {}),
    ("Cost Center", "CostCenterName", "txtCostCenterName", "text", {}),
    ("Cost Center", "Department", "ddDepartment", "choice", {}),
    ("Cost Center", "Owner", "txtOwner", "text", {}),
    ("Cost Center", "BudgetYear", "txtBudgetYear", "number", {}),
]


# Format check per field when the RequiredFields row leaves Check blank; MDM can override it on the Rules
# screen (or switch it off with "None"). Every free-text field is also checked for placeholders (N/A, TBC, -).
DEFAULT_CHECKS = {
    "CustomerName": "Text", "RegistrationNo": "RegNo", "BillingAddress": "Text", "ContactEmail": "Email",
    "ItemDescription": "Text", "ManufacturerPartNo": "PartNo", "HSCode": "HSCode",
    "RegulatoryLicenceNo": "LicenceNo", "ShelfLifeMonths": "Months", "VendorName": "Text",
    "TaxID": "TaxID", "ISO13485CertNo": "LicenceNo", "BankName": "Text", "BankAccount": "BankAccount",
    "CostCenterName": "Text", "Owner": "Text", "BudgetYear": "Year",
}
CHECKS = ["None", "Text", "RegNo", "HSCode", "TaxID", "LicenceNo", "PartNo", "BankAccount", "Email", "Months", "Year"]
PLACEHOLDERS = ["na", "nil", "none", "null", "tbc", "tba", "tbd", "x", "xx", "xxx", "xxxx", "unknown", "test",
                "dummy", "pending", "later", "asap", "idk", "same", "sameasabove", "asabove", "abc", "asdf",
                "qwerty", "123", "1234", "12345", "0", "00", "000"]
FREE_TEXT = [f[1] for f in FIELDS if f[3] in ("text", "email")]
NUMBERS = [f[1] for f in FIELDS if f[3] == "number"]
# Plain labels for the change note (Country / PaymentTerms appear on two request types; one row each)
LABELS = {"CustomerName": "Customer name", "Country": "Country", "RegistrationNo": "Registration no.",
          "BillingAddress": "Billing address", "ContactEmail": "Contact email", "Segment": "Segment",
          "PaymentTerms": "Payment terms", "CreditLimit": "Credit limit", "ItemDescription": "Item description",
          "ManufacturerPartNo": "Manufacturer part no.", "ProductFamily": "Product family",
          "UnitOfMeasure": "Unit of measure", "HSCode": "HS code", "IsRegulated": "Regulated",
          "RegulatoryLicenceNo": "Regulatory licence no.", "ShelfLifeMonths": "Shelf life (months)",
          "VendorName": "Vendor name", "TaxID": "Tax ID", "SuppliesRegulatedGoods": "Supplies regulated goods",
          "ISO13485CertNo": "ISO 13485 certificate no.", "BankName": "Bank name", "BankAccount": "Bank account",
          "CostCenterName": "Cost centre name", "Department": "Department", "Owner": "Owner",
          "BudgetYear": "Budget year"}
UNIQUE_FIELDS = list({f[1]: f for f in reversed(FIELDS)}.values())[::-1]
# Old value of each field on the request being edited (for the edit form's defaults and the change note)
SENSITIVE = {"PaymentTerms", "CreditLimit", "BankName", "BankAccount"}


def old_value(f):
    """Power Fx for the field's saved value as text, on the request being edited (EditRec / EditSens)."""
    _, name, _, kind, _ = f
    src = "EditSens" if name in SENSITIVE else "EditRec"
    if name == "IsRegulated":
        return 'Coalesce(EditRec.RegulatedAnswer, If(EditRec.IsRegulated, "Yes", "No"))'
    if kind == "toggle":
        return f'If({src}.{name}, "Yes", "No")'
    if kind == "number":
        return f"Text({src}.{name})"
    return f"{src}.{name}"


def text_of(f):
    """Power Fx expression for a field's current value as text (used by the rule engine)."""
    _, name, ctl, kind, _ = f
    if kind == "toggle":
        return f'If({ctl}.Value, "Yes", "No")'
    if kind in ("choice", "country"):
        return f"{ctl}.Selected.Value"
    return f"{ctl}.Text"


def field_value_rows():
    rows = []
    for name in dict.fromkeys(f[1] for f in FIELDS):
        owners = [f for f in FIELDS if f[1] == name]
        if len(owners) == 1:
            expr = text_of(owners[0])
        else:  # same FieldName on several request types (Country, PaymentTerms)
            expr = "Switch(SelectedType, " + ", ".join(f'"{o[0]}", {text_of(o)}' for o in owners) + ")"
        rows.append(f'    {{F: "{name}", V: {expr}}}')
    return ",\n".join(rows)


def fx_list(items):
    return "[" + ", ".join(f'"{i}"' for i in items) + "]"


LEGAL = ["pte", "ltd", "sdn", "bhd", "co", "jsc", "pt", "inc", "gmbh", "ag", "sa", "the"]
EXPAND = {"hosp": "hospital", "ctr": "centre", "center": "centre", "univ": "university", "med": "medical",
          "lab": "laboratory", "spec": "specialist", "diag": "diagnostic", "gen": "general", "comm": "community"}
PUNCT = [".", ",", "(", ")", "-", "/", "'", '"', "&", ":", ";", "#", "+"]


def strip_punct(expr):
    for ch in PUNCT:
        lit = '""""' if ch == '"' else f'"{ch}"'
        expr = f"Substitute({expr}, {lit}, \" \")"
    return expr


def alnum(expr, upper=False):
    """Power Fx: the text's letters and digits only (expr must already be lower or upper case)."""
    rng = "A-Z0-9" if upper else "a-z0-9"
    return (f'Concat(Filter(ForAll(Sequence(Len({expr})), Mid({expr}, Value, 1)) As ch, '
            f'IsMatch(ch.Value, "[{rng}]")), Value)')


def pairs_of(key):
    """Power Fx: the distinct letter pairs of a match key, as a one-column table (Value)."""
    return f"Distinct(ForAll(Sequence(Max(Len({key}) - 1, 0)), Mid({key}, Value, 2)), Value)"


def similarity(key):
    """Power Fx: share of letter pairs `key` has in common with the typed name (onerecord/livecheck.similarity)."""
    return (f"With({{b: {pairs_of(key)}}}, If(CountRows(InputPairs) = 0 || CountRows(b) = 0, 0, "
            f"2 * CountRows(Filter(InputPairs As g, g.Value in b.Value)) / (CountRows(InputPairs) + CountRows(b))))")


ID_LABEL = 'Switch(SelectedType, "Customer", "registration no.", "Item", "manufacturer part no.", "Vendor", "tax ID", "")'
PENDING = '"Pending approval", "Changes requested", "Resubmitted"'
# Plain string (not an f-string), so Power Fx braces stay single; {LEGAL} etc. are filled in below.
DUP_FX = """// ---- Live duplicate checks (mirrored in onerecord/livecheck.py; change both together)
// Names: cleaned up (lower case, no punctuation or legal words, abbreviations expanded, letters and digits only)
// and compared by the share of letter pairs they have in common, so typos still match. Customers are compared
// within the same country, items within the same product family; both filters run in SharePoint, so the check
// works however long the lists get. IDs are compared without punctuation through the lists' IDKey column.
MatchThreshold = 0.82;
Noun = Switch(SelectedType, "Cost Center", "cost centre", Lower(SelectedType));
NameInput = Switch(SelectedType, "Customer", txtCustomerName.Text, "Item", txtItemDescription.Text,
                   "Vendor", txtVendorName.Text, "");
LegalWords = {LEGAL};
NameBasic = Concat(
    Filter(Split(Trim({BASIC}), " ") As w, !IsBlank(w.Value) && !(w.Value in LegalWords)),
    Value, " "
);
NameKey = Concat(
    ForAll(Split(NameBasic, " ") As w, Switch(w.Value, {EXPAND}, w.Value)),
    Value, ""
);
InputKey = {INPUT_KEY};
InputPairs = {INPUT_PAIRS};
IDInput = Switch(SelectedType, "Customer", txtRegistrationNo.Text, "Item", txtManufacturerPartNo.Text,
                 "Vendor", txtTaxID.Text, "");
InputIDKey = {ID_KEY};

// Existing records with the same ID (direct lookups on IDKey)
IDMatch = If(
    !IsBlank(InputIDKey),
    Switch(
        SelectedType,
        "Customer", With({m: LookUp(CustomerMaster, IDKey = InputIDKey)},
            If(!IsBlank(m), {RecordID: m.Title, Name: m.CustomerName, Status: m.SAPStatus, Regulated: false})),
        "Item", With({m: LookUp(ItemMaster, IDKey = InputIDKey)},
            If(!IsBlank(m), {RecordID: m.Title, Name: m.Description, Status: m.SAPStatus, Regulated: m.Regulated})),
        "Vendor", With({m: LookUp(VendorMaster, IDKey = InputIDKey)},
            If(!IsBlank(m), {RecordID: m.Title, Name: m.VendorName, Status: m.SAPStatus, Regulated: false}))
    )
);
AliasMatch = If(SelectedType = "Customer" && !IsBlank(NameBasic),
                LookUp(Aliases, Title = NameBasic || Title = Concat(ForAll(Split(NameBasic, " ") As w,
                    Switch(w.Value, {EXPAND}, w.Value)), Value, " ")));
// Existing records with a similar name
NameCandidates = Switch(
    SelectedType,
    "Customer", ForAll(Filter(CustomerMaster, Country = ddCustomerCountry.Selected.Value),
        {RecordID: Title, Name: CustomerName, Key: MatchKey, Status: SAPStatus, Regulated: false}),
    "Item", ForAll(If(IsBlank(ddProductFamily.Selected.Value), ItemMaster,
                      Filter(ItemMaster, ProductFamily = ddProductFamily.Selected.Value)),
        {RecordID: Title, Name: Description, Key: MatchKey, Status: SAPStatus, Regulated: Regulated}),
    "Vendor", ForAll(VendorMaster,
        {RecordID: Title, Name: VendorName, Key: MatchKey, Status: SAPStatus, Regulated: false})
);
NameMatch = If(
    Len(InputKey) >= 4,
    First(Sort(Filter(ForAll(NameCandidates As c,
        {RecordID: c.RecordID, Name: c.Name, Status: c.Status, Regulated: c.Regulated, Score: {SIM_C}}),
        Score >= MatchThreshold), Score, SortOrder.Descending))
);
// Requests for the same thing that are already on their way (not the one being edited)
PendingRows = With(
    {id: EditID},
    Filter(
        ForAll(Filter(Requests, RequestType = SelectedType &&
                      (Status = "Pending approval" || Status = "Changes requested" || Status = "Resubmitted")),
            {ID: Title, Name: Coalesce(CustomerName, ItemDescription, VendorName, CostCenterName), Country: Country,
             Entity: Entity, Dept: Department, Key: MatchKey, IDK: IDKey, By: Requestor}),
        ID <> id
    )
);
PendingID = If(!IsBlank(InputIDKey), LookUp(PendingRows, IDK = InputIDKey));
PendingName = If(
    Len(InputKey) >= 4,
    First(Sort(Filter(ForAll(Filter(PendingRows, SelectedType <> "Customer" || Country = ddCustomerCountry.Selected.Value) As p,
        {ID: p.ID, Name: p.Name, By: p.By, Score: {SIM_P}}),
        Score >= MatchThreshold), Score, SortOrder.Descending))
);
// Cost centres: one per entity and department (an assumption), so a second one is blocked unless explained
CostCentreMatch = If(
    SelectedType = "Cost Center" && !IsBlank(SelectedEntity) && !IsBlank(ddDepartment.Selected.Value),
    LookUp(CostCentres, Entity = SelectedEntity && Department = ddDepartment.Selected.Value)
);
PendingCC = If(
    SelectedType = "Cost Center" && !IsBlank(SelectedEntity) && !IsBlank(ddDepartment.Selected.Value),
    LookUp(PendingRows, Entity = SelectedEntity && Dept = ddDepartment.Selected.Value)
);
// Help under "Is this regulated?": what the closest existing item says, and what "Not sure" does
RegulatedHint = With(
    {m: If(SelectedType = "Item", Coalesce(IDMatch, NameMatch))},
    If(IsBlank(m), "",
       "Similar item " & m.RecordID & " (" & m.Name & ") is " & If(m.Regulated, "regulated. ", "not regulated. ")) &
    "Not sure? Choose Not sure and Quality/Regulatory will decide."
);

DupStatus = If(
    !IsBlank(IDMatch) || !IsBlank(AliasMatch) || !IsBlank(PendingID) || !IsBlank(CostCentreMatch) || !IsBlank(PendingCC),
        "Blocked",
    !IsBlank(NameMatch) || !IsBlank(PendingName), "Possible match",
    "Clear"
);
DupRecordID = If(
    DupStatus <> "Clear",
    Coalesce(IDMatch.RecordID, AliasMatch.RecordID, PendingID.ID, CostCentreMatch.Title, PendingCC.ID,
             NameMatch.RecordID, PendingName.ID)
);
SAPNote = " (approved, being set up in SAP)";
UseInstead = " Records in SAP B1 are shared by SPD, QTS and QTG, so use it instead of requesting a new one. " &
    "If it isn't the same " & Noun & ", switch on Not the same below and say why.";
FollowInstead = " Follow that request in My requests instead. If it's a different " & Noun &
    ", switch on Not the same below and say why.";
DupMessage = If(
    !IsBlank(IDMatch),
        "This " & Noun & " already exists: " & IDMatch.Name & " (" & IDMatch.RecordID &
        If(IDMatch.Status = "Pending SAP import", SAPNote, "") & ") has the same " & {ID_LABEL} & "." & UseInstead,
    !IsBlank(AliasMatch),
        "This customer already exists: " & Char(34) & txtCustomerName.Text & Char(34) & " is a known name for " &
        AliasMatch.CanonicalName & " (" & AliasMatch.RecordID & ")." & UseInstead,
    !IsBlank(PendingID),
        "Already requested: " & PendingID.ID & " (" & PendingID.Name & ", requested by " & PendingID.By &
        ") has the same " & {ID_LABEL} & " and is waiting for approval." & FollowInstead,
    !IsBlank(CostCentreMatch),
        "A cost centre already exists for " & SelectedEntity & " " & ddDepartment.Selected.Value & ": " &
        CostCentreMatch.CostCentreName & " (" & CostCentreMatch.Title & "). Use it, or switch on Not the same below " &
        "and say why a second one is needed.",
    !IsBlank(PendingCC),
        "Already requested: " & PendingCC.ID & " (" & PendingCC.Name & ") for " & SelectedEntity & " " &
        ddDepartment.Selected.Value & " is waiting for approval." & FollowInstead,
    !IsBlank(NameMatch),
        "Possible match: " & NameMatch.Name & " (" & NameMatch.RecordID &
        If(NameMatch.Status = "Pending SAP import", SAPNote, "") & ", " & Text(NameMatch.Score, "0%") &
        " similar name). If it's a different " & Noun & ", switch on This is a different " & Noun & " and say why.",
    !IsBlank(PendingName),
        "Possible match: " & PendingName.ID & " (" & PendingName.Name & ", requested by " & PendingName.By & ", " &
        Text(PendingName.Score, "0%") & " similar name) is waiting for approval. If it's a different " & Noun &
        ", switch on This is a different " & Noun & " and say why.",
    ""
);
// Overriding a warning or a block needs a reason; approvers and MDM see it on their cards
DupOverridden = DupStatus <> "Clear" && tglNotDuplicate.Value && Len(Trim(txtDupReason.Text)) >= 10;

CanSubmit = !IsBlank(SelectedEntity) && CountRows(MissingFields) = 0 && CountRows(FieldProblems) = 0 &&
    (DupStatus = "Clear" || DupOverridden) &&
    (!Editing || CountRows(EditChanges) > 0 || !IsBlank(Trim(txtReplyNote.Text)));
StatusText = If(
    CanSubmit, If(Editing, "Ready to resubmit. ", "Ready to submit. ") & If(Editing, ChangesText, ""),
    Trim(
        If(IsBlank(SelectedEntity), "Choose a business entity. ", "") &
        If(CountRows(MissingFields) > 0, "Still needed: " & Concat(MissingFields, DisplayLabel, ", ") & ". ", "") &
        If(CountRows(FieldProblems) > 0, "Check: " & Concat(FieldProblems, DisplayLabel & " " & Problem, "; ") & ". ", "") &
        If(Editing && CountRows(EditChanges) = 0 && IsBlank(Trim(txtReplyNote.Text)),
           "Make the changes asked for, or reply to the approver. ", "") &
        If(DupStatus <> "Clear" && !DupOverridden,
           If(tglNotDuplicate.Value, "Say why it's not the same " & Noun & " (at least 10 characters). ",
              If(DupStatus = "Blocked", "This " & Noun & " already exists or is already requested (see above). ",
                 "Check the possible match above. ")), "")
    )
);"""
DUP_FX = (DUP_FX.replace("{LEGAL}", fx_list(LEGAL))
          .replace("{BASIC}", strip_punct("Lower(NameInput)"))
          .replace("{EXPAND}", ", ".join(f'"{k}", "{v}"' for k, v in EXPAND.items()))
          .replace("{INPUT_KEY}", alnum("NameKey"))
          .replace("{INPUT_PAIRS}", pairs_of("InputKey"))
          .replace("{ID_KEY}", alnum("Upper(IDInput)", upper=True))
          .replace("{SIM_C}", similarity("c.Key"))
          .replace("{SIM_P}", similarity("p.Key"))
          .replace("{ID_LABEL}", ID_LABEL))


FORMULAS = f"""RequestTypes = {fx_list(TYPES)};
SelectedType = ddRequestType.Selected.Value;
SelectedEntity = ddEntity.Selected.Code;

// All field rules, loaded once (about 30 rows) and filtered in the app. Filtering in the SharePoint query
// left the form empty on first load: the query ran before the Request type dropdown had its default.
FieldRules = ForAll(
    RequiredFields,
    {{RequestType: RequestType, FieldName: FieldName, DisplayLabel: DisplayLabel, Required: Required,
      ConditionField: ConditionField, ConditionValue: ConditionValue, Sensitive: Sensitive, HelpText: HelpText,
      Check: Check}}
);
TypeRules = Filter(FieldRules, RequestType = SelectedType);

// What the requestor has entered so far, keyed by the FieldName used in the RequiredFields list.
FieldValues = Table(
{field_value_rows()}
);

// A field shows (and is required) when its rule is "Always", or when its condition is met.
VisibleFields = Filter(
    TypeRules,
    Required <> "Conditional" || LookUp(FieldValues, F = ConditionField).V = ConditionValue
);
MissingFields = Filter(VisibleFields, IsBlank(Trim(LookUp(FieldValues, F = FieldName).V)));

// ---- Filled in, but plausible? Placeholders (N/A, TBC, -) never pass; formats come from the field's Check
// (RequiredFields, editable on the Rules screen), else the default below. k = the value's letters and digits only.
DefaultChecks = Table(
{",\n".join(f'    {{F: "{k}", C: "{v}"}}' for k, v in DEFAULT_CHECKS.items())}
);
FreeTextFields = {fx_list(FREE_TEXT)};
NumberFields = {fx_list(NUMBERS)};
Placeholders = {fx_list(PLACEHOLDERS)};
FieldChecks = ForAll(
    Filter(VisibleFields, FieldName in FreeTextFields || FieldName in NumberFields) As r,
    With(
        {{v: Trim(LookUp(FieldValues, F = r.FieldName).V),
         c: Coalesce(r.Check, LookUp(DefaultChecks, F = r.FieldName).C, "None")}},
        With(
            {{k: Lower(Concat(Filter(ForAll(Sequence(Len(v)), Mid(v, Value, 1)) As ch, IsMatch(ch.Value, "[A-Za-z0-9]")), Value))}},
            {{FieldName: r.FieldName, DisplayLabel: r.DisplayLabel,
             Problem: If(
                IsBlank(v), "",
                !(r.FieldName in NumberFields) && (IsBlank(k) || k in Placeholders),
                    "looks like a placeholder. Enter the real value, or ask the MDM team if you don't have it",
                c = "Text", If(Len(k) >= 3, "", "is too short"),
                c = "Email", If(IsMatch(v, Match.Email), "", "isn't a valid email address"),
                c = "RegNo", With({{u: Upper(k)}}, Switch(ddCustomerCountry.Selected.Value,
                    "SG", If(IsMatch(u, "^(?:\\d{{8}}[A-Z]|\\d{{9}}[A-Z]|[TSR]\\d{{2}}[A-Z]{{2}}\\d{{4}}[A-Z])$"), "",
                        "doesn't look like a Singapore UEN (e.g. 200288778W)"),
                    "MY", If(IsMatch(u, "^(?:\\d{{12}}|\\d{{14}}|\\d{{6,7}}[A-Z])$"), "",
                        "doesn't look like an SSM registration no. (12 digits, e.g. 201901000005)"),
                    "TH", If(IsMatch(u, "^\\d{{13}}$"), "", "should be the 13-digit Thai tax ID"),
                    "ID", If(IsMatch(u, "^\\d{{15,16}}$"), "", "should be the 15 or 16 digit NPWP (e.g. 01.234.567.8-901.000)"),
                    "VN", If(IsMatch(u, "^(?:\\d{{10}}|\\d{{13}})$"), "", "should be the 10-digit tax code (MST), or 13 digits for a branch"),
                    "")),
                c = "HSCode", If(IsMatch(k, "^\\d{{6,10}}$"), "", "should be 6 to 10 digits (e.g. 3822.19.00)"),
                c = "TaxID", If(Len(k) >= 5 && Len(k) <= 20 && IsMatch(k, "\\d", MatchOptions.Contains), "",
                    "should be 5 to 20 letters and digits, including at least one digit"),
                c = "LicenceNo", If(Len(k) >= 5 && Len(k) <= 30 && IsMatch(k, "\\d", MatchOptions.Contains), "",
                    "should be 5 to 30 letters and digits, including at least one digit"),
                c = "PartNo", If(Len(k) >= 3, "", "is too short for a part no."),
                c = "BankAccount", If(Len(k) >= 6 && Len(k) <= 34 && IsMatch(k, "\\d{{4}}", MatchOptions.Contains), "",
                    "doesn't look like a bank account no. (6 to 34 characters, mostly digits)"),
                c = "Months", If(Value(v) >= 1 && Value(v) <= 120, "", "should be between 1 and 120 months"),
                c = "Year", If(Value(v) >= Year(Today()) - 1 && Value(v) <= Year(Today()) + 2, "",
                    "should be between " & (Year(Today()) - 1) & " and " & (Year(Today()) + 2)),
                "")}}
        )
    )
);
FieldProblems = Filter(FieldChecks, !IsBlank(Problem));
EmailInvalid = "ContactEmail" in FieldProblems.FieldName;

// ---- Editing a request an approver sent back (My requests > Edit and resubmit). The ID sits in a hidden
// label on this screen, so these formulas don't depend on a variable.
EditID = lblEditID.Text;
Editing = !IsBlank(EditID);
EditRec = With({{id: EditID}}, If(!IsBlank(id), LookUp(Requests, Title = id)));
EditSens = With({{id: EditID}}, If(!IsBlank(id), LookUp(SensitiveDetails, RequestID = id)));
EditAsk = With(
    {{id: EditID}},
    If(!IsBlank(id), First(Sort(Filter(ApprovalLog, RequestID = id && Action = "Request changes"), Timestamp, SortOrder.Descending)))
);
// What the requestor changed, compared with what was submitted. Sensitive values are named, never shown.
EditChanges = If(
    Editing,
    Filter(
        Table(
{",\n".join(f'            {{L: "{lbl}", Old: {old_value(f)}, New: LookUp(FieldValues, F = "{f[1]}").V, S: {"true" if f[1] in SENSITIVE else "false"}}}' for f, lbl in [(f, LABELS[f[1]]) for f in UNIQUE_FIELDS])}
        ),
        Coalesce(Old, "") <> Coalesce(New, "")
    )
);
ChangesText = If(
    CountRows(EditChanges) = 0, "No fields changed.",
    Concat(EditChanges, L & If(S, " changed", ": " & Char(34) & Old & Char(34) & " -> " & Char(34) & New & Char(34)), "; ") & "."
);

{DUP_FX}

// ---- My requests screen
RolesRows = ForAll(Roles, {{Role: Role, Entity: Entity, Name: PersonName, Email: Lower(PersonEmail)}});
IsMDM = !IsBlank(LookUp(RolesRows, Role = "MDM Analyst" && Email = Lower(User().Email)));
ShowAllRequests = IsMDM && tglShowAll.Value;
StatusFilter = ddStatusFilter.Selected.Value;
MyRequestList = Sort(
    Filter(Requests,
           (ShowAllRequests || 'Created By'.Email = User().Email) &&
           (StatusFilter = "All" || Status = StatusFilter)),
    ID, SortOrder.Descending
);
SelectedRequest = galRequests.Selected;
// The ID is read into a plain text value first: a field of the gallery's selected record didn't
// translate into the SharePoint query (it returned no rows), a plain value does.
SelectedRequestID = Text(galRequests.Selected.Title);
SelectedLog = With(
    {{id: SelectedRequestID}},
    ForAll(
        Filter(ApprovalLog, RequestID = id),
        {{Role: ActorRole, Action: Action, Actor: Lower(Actor), Who: Actor, Detail: Detail, At: Timestamp}}
    )
);
// Still waiting: an approver can be asked again after a resubmit, so each Assigned row says its round
// ("Stage 1, round 2"). A round is open while that role has made fewer decisions than its round number.
DecisionActions = ["Approve", "Reject", "Request changes"];
WaitingOn = Filter(
    SelectedLog As a,
    a.Action = "Assigned" &&
    CountRows(Filter(SelectedLog As d, d.Role = a.Role && d.Action in DecisionActions)) =
        If("round " in a.Detail, Value(Last(Split(a.Detail, "round ")).Value), 1) - 1
);
LastAsk = First(Sort(Filter(SelectedLog, Action = "Request changes"), At, SortOrder.Descending));
WaitingText = If(SelectedRequest.Status = "Changes requested",
    "You (" & SelectedRequest.Requestor & "): " & LastAsk.Role & " asked for changes: " & LastAsk.Detail &
    " Press Edit and resubmit." & If(CountRows(WaitingOn) > 0, Char(10), ""), "") &
If(
    SelectedRequest.Status = "Ready for SAP import" && CountRows(WaitingOn) = 0,
        "MDM team: import the file in SAP_Imports into SAP B1, then press Mark as created in SAP.",
    CountRows(WaitingOn) = 0, If(SelectedRequest.Status = "Changes requested", "", "No one. " & SelectedRequest.Status & "."),
    Concat(
        WaitingOn As w,
        w.Role & " - " &
        Coalesce(
            LookUp(RolesRows, Role = w.Role && Email = w.Actor && (Entity = SelectedRequest.Entity || Entity = "Any")).Name,
            LookUp(RolesRows, Email = w.Actor).Name,
            w.Actor
        ) & " (waiting " & DateDiff(w.At, Now(), TimeUnit.Days) & " days)",
        Char(10)
    )
);
// Everything logged for the request, oldest first. The log never holds sensitive values.
TimelineText = If(
    CountRows(SelectedLog) = 0, "Nothing logged yet.",
    Concat(
        Sort(SelectedLog, At, SortOrder.Ascending) As e,
        Text(e.At, "dd mmm yyyy hh:mm") & "  |  " & e.Action & "  |  " &
        If(IsBlank(e.Role) || e.Role = "System", "", e.Role & " - ") &
        Coalesce(
            LookUp(RolesRows, Email = e.Actor && Role = e.Role).Name,
            LookUp(RolesRows, Email = e.Actor).Name,
            e.Who
        ) &
        If(IsBlank(e.Detail), "", "  |  " & e.Detail),
        Char(10)
    )
);
SubmittedText = With(
    {{r: SelectedRequest}},
    Concat(
        Filter(
            Table(
                {{L: "Requestor", V: r.Requestor}},
                {{L: "Submitted", V: Text(r.SubmittedAt, "dd mmm yyyy hh:mm")}},
                {{L: "Customer name", V: r.CustomerName}},
                {{L: "Item description", V: r.ItemDescription}},
                {{L: "Vendor name", V: r.VendorName}},
                {{L: "Cost centre name", V: r.CostCenterName}},
                {{L: "Country", V: r.Country}},
                {{L: "Registration no.", V: r.RegistrationNo}},
                {{L: "Billing address", V: r.BillingAddress}},
                {{L: "Contact email", V: r.ContactEmail}},
                {{L: "Segment", V: r.Segment}},
                {{L: "Manufacturer part no.", V: r.ManufacturerPartNo}},
                {{L: "Product family", V: r.ProductFamily}},
                {{L: "Unit of measure", V: r.UnitOfMeasure}},
                {{L: "HS code", V: r.HSCode}},
                {{L: "Regulated", V: If(r.RequestType = "Item", Coalesce(r.RegulatedAnswer, If(r.IsRegulated, "Yes", "No")))}},
                {{L: "Regulatory licence no.", V: r.RegulatoryLicenceNo}},
                {{L: "Shelf life (months)", V: Text(r.ShelfLifeMonths)}},
                {{L: "Tax ID", V: r.TaxID}},
                {{L: "Supplies regulated goods", V: If(r.RequestType = "Vendor", If(r.SuppliesRegulatedGoods, "Yes", "No"))}},
                {{L: "ISO 13485 certificate no.", V: r.ISO13485CertNo}},
                {{L: "Department", V: r.Department}},
                {{L: "Owner", V: r.Owner}},
                {{L: "Budget year", V: Text(r.BudgetYear)}},
                {{L: "Duplicate check", V: r.DuplicateCheck & If(IsBlank(r.PossibleMatchID), "", " (" & r.PossibleMatchID & ")")}},
                {{L: "Why it's not a duplicate", V: r.DupReason}},
                {{L: "SAP code", V: r.SAPCode}}
            ),
            !IsBlank(V)
        ),
        L & ": " & V, Char(10)
    )
);
SensitiveRow = With({{id: SelectedRequestID}}, LookUp(SensitiveDetails, RequestID = id));
SensitiveText = If(
    !(SelectedRequest.RequestType in ["Customer", "Vendor"]), "None for this request type.",
    IsBlank(SensitiveRow), "Not visible to you.",
    Concat(
        Filter(
            Table(
                {{L: "Payment terms", V: SensitiveRow.PaymentTerms}},
                {{L: "Credit limit (SGD)", V: Text(SensitiveRow.CreditLimit, "#,##0")}},
                {{L: "Bank name", V: SensitiveRow.BankName}},
                {{L: "Bank account", V: SensitiveRow.BankAccount}}
            ),
            !IsBlank(V)
        ),
        L & ": " & V, Char(10)
    )
);"""

TIME_ZONES = ["Asia/Singapore", "Asia/Kuala_Lumpur", "Asia/Bangkok", "Asia/Jakarta", "Asia/Ho_Chi_Minh"]
CONDITIONS = ["IsRegulated", "SuppliesRegulatedGoods"]  # the conditions the Route and approve flow understands

# Plain string (not an f-string), so Power Fx braces stay single.
FORMULAS += """

// ---- Who will approve: the same rules the Route and approve flow reads (RoutingRules + Roles)
RuleRows = ForAll(
    RoutingRules,
    {RequestType: RequestType, Entity: Entity, ConditionField: ConditionField, Role: ApproverRole,
     Stage: Stage, Active: Active}
);
// Like the flow: the first Roles row for the role and entity (or Any); no "@" in its email = nobody set up.
ApproverPreview = ForAll(
    Filter(RuleRows As x,
        x.Active && (x.RequestType = SelectedType || x.RequestType = "Any") &&
        (x.Entity = SelectedEntity || x.Entity = "Any") &&
        (IsBlank(x.ConditionField) ||
         (x.ConditionField = "IsRegulated" && SelectedType = "Item" && ddIsRegulated.Selected.Value in ["Yes", "Not sure"]) ||
         (x.ConditionField = "SuppliesRegulatedGoods" && SelectedType = "Vendor" && tglSuppliesRegulatedGoods.Value))
    ) As r,
    With(
        {p:LookUp(RolesRows, Role = r.Role && (Entity = SelectedEntity || Entity = "Any"))},
        {Stage: r.Stage, Role: r.Role, Person: Coalesce(p.Name, p.Email), Ok: "@" in p.Email}
    )
);
ApproverGap = CountRows(Filter(ApproverPreview, !Ok)) > 0;
ApproverText = If(
    IsBlank(SelectedEntity), "Choose a business entity to see who will approve.",
    CountRows(ApproverPreview) = 0, "No approval steps are set up for this request type.",
    With(
        {s1: Filter(ApproverPreview, Stage < 1.5), s2: Filter(ApproverPreview, Stage >= 1.5),
         gaps: Filter(ApproverPreview, !Ok)},
        Concat(s1, Role & " (" & If(Ok, Person, "nobody set up") & ")", ", ") &
        If(CountRows(s1) > 1, ", all at the same time", "") &
        If(CountRows(s1) > 0 && CountRows(s2) > 0, "; then ", "") &
        Concat(s2, Role & " (" & If(Ok, Person, "nobody set up") & ")", ", ") & "." &
        If(CountRows(gaps) > 0,
            " No " & Concat(gaps, Role, " or ") & " is set up for " & SelectedEntity &
            ", so the MDM team approves in their place.",
            "")
    )
);

// ---- Rules screen (MDM): approval steps that some active business unit has nobody for
RuleGapText = Concat(
    Filter(BusinessUnits, Active = true) As b,
    Concat(
        Filter(
            Distinct(Filter(RuleRows As x, x.Active && (x.Entity = b.Title || x.Entity = "Any")), Role) As r,
            !("@" in LookUp(RolesRows, Role = r.Value && (Entity = b.Title || Entity = "Any")).Email)
        ) As g,
        b.Title & ": nobody set up as " & g.Value & Char(10)
    )
);"""


def q(v):
    """Emit a formula as a YAML scalar (block scalar when it isn't trivially safe)."""
    v = "=" + v
    if "\n" in v or any(s in v for s in (": ", " #", "\t")) or v.endswith(":"):
        return "|-\n" + "\n".join("  " + line for line in v.split("\n"))
    return v


def emit(name, control, props, children=None, variant=None, indent=0):
    pad = " " * indent
    out = [f"{pad}- {name}:", f"{pad}    Control: {control}"]
    if variant:
        out.append(f"{pad}    Variant: {variant}")
    out.append(f"{pad}    Properties:")
    for k in sorted(props):
        val = q(props[k])
        if val.startswith("|-"):
            lines = val.split("\n")
            out.append(f"{pad}      {k}: {lines[0]}")
            out += [f"{pad}      {l}" for l in lines[1:]]
        else:
            out.append(f"{pad}      {k}: {val}")
    if children:
        out.append(f"{pad}    Children:")
        for c in children:
            out += c(indent + 6)
    return out


def ctl(name, control, props, children=None, variant=None):
    return lambda indent: emit(name, control, props, children, variant, indent)


def label(name, text, **extra):
    p = dict(LABEL, Text=text, **extra)
    return ctl(name, "Label@2.5.1", p)


BLOCK_W = "Min(Parent.Width - 48, 720)"


def block(name, title_expr, input_ctl, help_expr, visible, help_color="RGBA(96, 94, 92, 1)"):
    """One field: title, input, help text, stacked in a small vertical container."""
    return ctl(name, "GroupContainer@1.5.0", {
        "Fill": "RGBA(255, 255, 255, 1)", "FillPortions": "0", "Height": "92", "Width": BLOCK_W,
        "LayoutDirection": "LayoutDirection.Vertical", "LayoutAlignItems": "LayoutAlignItems.Stretch",
        "LayoutGap": "4", "LayoutMinHeight": "16", "LayoutMinWidth": "16", "Visible": visible,
        "DropShadow": "DropShadow.None",
    }, [
        label(name.replace("blk", "lbl"), title_expr, FillPortions="0", Height="22", Size="12",
              FontWeight="FontWeight.Semibold", PaddingLeft="0"),
        input_ctl,
        label(name.replace("blk", "hlp"), help_expr, FillPortions="0", Height="20", Size="10",
              Color=help_color, PaddingLeft="0"),
    ], variant="AutoLayout")


def input_for(f):
    """The field's input. Its default is blank, or the saved value while a sent-back request is being edited."""
    _, name, c, kind, _ = f
    base = {"FillPortions": "0", "Height": "38"}
    default = f'If(Editing, {old_value(f)}, "")'
    if kind in ("text", "number", "email"):
        p = dict(TEXTINPUT, **base, Default=default, Size="12")
        if kind == "number":
            p["Format"] = "TextFormat.Number"
        if kind == "email":
            p["HintText"] = '"name@company.com"'
            p["BorderColor"] = "If(EmailInvalid, RGBA(209, 52, 56, 1), RGBA(200, 198, 196, 1))"
        return ctl(c, "Classic/TextInput@2.3.2", p)
    if kind in ("choice", "country"):
        items = COUNTRIES if kind == "country" else CHOICES[name]
        p = dict(DROPDOWN, **base, Items=fx_list(items), AllowEmptySelection="true", Default=default, Size="12")
        return ctl(c, "Classic/DropDown@2.3.1", p)
    if kind == "toggle":
        p = dict(TOGGLE, **base, Default=f"If(Editing, EditRec.{name}, false)", TrueText='"Yes"', FalseText='"No"', Size="12",
                 Width="160", AlignInContainer="AlignInContainer.Start")
        return ctl(c, "Classic/Toggle@2.1.0", p)
    raise ValueError(kind)


def field_block(f):
    rtype, name, c, kind, extra = f
    rule = f'LookUp(VisibleFields, FieldName = "{name}")'
    title = (f'With({{r: {rule}}}, r.DisplayLabel & If(r.Sensitive = "Yes", "  (restricted)", "") & " *")')
    problem = f'LookUp(FieldProblems, FieldName = "{name}").Problem'
    help_text = extra.get("help", f"{rule}.HelpText")
    return block("blk" + c[3:] if c.startswith("txt") or c.startswith("tgl") else "blk" + c[2:],
                 title, input_for(f),
                 f'If(IsBlank({problem}), {help_text}, {rule}.DisplayLabel & " " & {problem})',
                 f'SelectedType = "{rtype}" && "{name}" in VisibleFields.FieldName',
                 help_color=f"If(IsBlank({problem}), RGBA(96, 94, 92, 1), RGBA(164, 38, 44, 1))")


# ---------------------------------------------------------------------------- screen tree
top_blocks = [
    block("blkRequestType", '"Request type *"',
          ctl("ddRequestType", "Classic/DropDown@2.3.1",
              dict(DROPDOWN, FillPortions="0", Height="38", Items="RequestTypes", Size="12",
                   Default='If(Editing, EditRec.RequestType, "Customer")',
                   DisplayMode="If(Editing, DisplayMode.Disabled, DisplayMode.Edit)")),
          '"What are you asking MDM to create?"', "true"),
    block("blkEntity", '"Business entity *"',
          ctl("ddEntity", "Classic/DropDown@2.3.1",
              dict(DROPDOWN, FillPortions="0", Height="38", Size="12", AllowEmptySelection="true",
                   Default='If(Editing, LookUp(BusinessUnits, Title = EditRec.Entity).BusinessUnitName, "")',
                   DisplayMode="If(Editing, DisplayMode.Disabled, DisplayMode.Edit)",
                   Items="ForAll(Filter(BusinessUnits, Active = true), {Value: BusinessUnitName, Code: Title})")),
          '"Which Lives Group business this is for"', "true"),
]

reset_targets = ["ddEntity", "tglNotDuplicate", "txtDupReason", "txtReplyNote"] + [f[2] for f in FIELDS]

IDENT = ["Title: rid", "RequestType: SelectedType", "Entity: SelectedEntity", "Requestor: User().FullName",
         'Status: "Pending approval"', 'CurrentStage: "Submitted, waiting for approvers"', "SubmittedAt: Now()"]
DATA = [
    'Country: Switch(SelectedType, "Customer", ddCustomerCountry.Selected.Value, "Vendor", txtVendorCountry.Text)',
    'CustomerName: If(SelectedType = "Customer", txtCustomerName.Text)',
    'RegistrationNo: If(SelectedType = "Customer", txtRegistrationNo.Text)',
    'BillingAddress: If(SelectedType = "Customer", txtBillingAddress.Text)',
    'ContactEmail: If(SelectedType = "Customer", txtContactEmail.Text)',
    'Segment: If(SelectedType = "Customer", ddSegment.Selected.Value)',
    'ItemDescription: If(SelectedType = "Item", txtItemDescription.Text)',
    'ProductFamily: If(SelectedType = "Item", ddProductFamily.Selected.Value)',
    'UnitOfMeasure: If(SelectedType = "Item", ddUnitOfMeasure.Selected.Value)',
    'ManufacturerPartNo: If(SelectedType = "Item", txtManufacturerPartNo.Text)',
    'HSCode: If(SelectedType = "Item", txtHSCode.Text)',
    # "Not sure" counts as regulated for routing, so Quality/Regulatory sees it; RegulatedAnswer keeps the answer
    'IsRegulated: If(SelectedType = "Item", ddIsRegulated.Selected.Value in ["Yes", "Not sure"])',
    'RegulatedAnswer: If(SelectedType = "Item", ddIsRegulated.Selected.Value)',
    'RegulatoryLicenceNo: If(SelectedType = "Item" && ddIsRegulated.Selected.Value = "Yes", txtRegulatoryLicenceNo.Text)',
    'ShelfLifeMonths: If(SelectedType = "Item" && "ShelfLifeMonths" in VisibleFields.FieldName, Value(txtShelfLifeMonths.Text))',
    'VendorName: If(SelectedType = "Vendor", txtVendorName.Text)',
    'TaxID: If(SelectedType = "Vendor", txtTaxID.Text)',
    'SuppliesRegulatedGoods: If(SelectedType = "Vendor", tglSuppliesRegulatedGoods.Value)',
    'ISO13485CertNo: If(SelectedType = "Vendor" && tglSuppliesRegulatedGoods.Value, txtISO13485CertNo.Text)',
    'CostCenterName: If(SelectedType = "Cost Center", txtCostCenterName.Text)',
    'Department: If(SelectedType = "Cost Center", ddDepartment.Selected.Value)',
    'Owner: If(SelectedType = "Cost Center", txtOwner.Text)',
    'BudgetYear: If(SelectedType = "Cost Center", Value(txtBudgetYear.Text))',
    'DuplicateCheck: If(DupStatus = "Clear", "Clear", DupStatus & If(DupOverridden, " - requestor says different", ""))',
    "PossibleMatchID: DupRecordID",
    'DupReason: If(DupOverridden, Trim(txtDupReason.Text), "")',
    "MatchKey: InputKey", "IDKey: InputIDKey",
]
PATCH_REQ = ",\n".join(IDENT + DATA)
# Resubmit after "Request changes": same fields, plus a dated line in ChangeNote saying what changed
PATCH_RESUBMIT = ",\n".join(DATA + [
    'Status: "Resubmitted"', 'CurrentStage: "Resubmitted; back with the approver who asked for changes"',
    'ChangeNote: If(IsBlank(EditRec.ChangeNote), "", EditRec.ChangeNote & Char(10)) & Text(Now(), "dd mmm yyyy hh:mm") & '
    '" " & User().FullName & ": " & ChangesText & If(IsBlank(Trim(txtReplyNote.Text)), "", " Reply: " & Trim(txtReplyNote.Text))',
])
SENS_DATA = [
    'PaymentTerms: If(SelectedType = "Customer", ddCustomerPaymentTerms.Selected.Value, ddVendorPaymentTerms.Selected.Value)',
    'CreditLimit: If(SelectedType = "Customer", Value(txtCreditLimit.Text))',
    'BankName: If(SelectedType = "Vendor", txtBankName.Text)',
    'BankAccount: If(SelectedType = "Vendor", txtBankAccount.Text)',
]
PATCH_SENS = ",\n".join(["Title: rid", "RequestID: rid"] + SENS_DATA)


def indent(s, n):
    return "\n".join(" " * n + line for line in s.split("\n"))


RESUBMIT = f"""IfError(
    Patch(Requests, EditRec, {{
{indent(PATCH_RESUBMIT, 8)}
    }});
    If(!IsBlank(EditSens),
        Patch(SensitiveDetails, EditSens, {{
{indent(",\n".join(SENS_DATA), 12)}
        }})
    );
    Set(gLastRequestID, EditID);
    Notify(EditID & " resubmitted. It's back with the approver who asked for changes.", NotificationType.Success);
    Set(gEditID, "");
{indent(";\n".join(f"Reset({t})" for t in reset_targets), 4)},
    Notify("Couldn't resubmit: " & FirstError.Message, NotificationType.Error)
)"""

CREATE = f"""With(
    {{rid: "REQ-" & Text(Coalesce(First(Sort(Requests, ID, SortOrder.Descending)).ID, 0) + 1, "0000")}},
    IfError(
        Patch(Requests, Defaults(Requests), {{
{indent(PATCH_REQ, 12)}
        }});
        If(SelectedType in ["Customer", "Vendor"],
            Patch(SensitiveDetails, Defaults(SensitiveDetails), {{
{indent(PATCH_SENS, 16)}
            }})
        );
        Set(gLastRequestID, rid);
        Notify(rid & " submitted. It's now with the approvers.", NotificationType.Success);
{indent(";\n".join(f"Reset({t})" for t in reset_targets), 8)},
        Notify("Couldn't submit: " & FirstError.Message, NotificationType.Error)
    )
)"""
SUBMIT = f"If(\n    Editing,\n{indent(RESUBMIT, 4)},\n{indent(CREATE, 4)}\n)"

def outline(style):
    """White button with a blue outline (secondary action)."""
    style.update(Fill="RGBA(255, 255, 255, 1)", Color="RGBA(0, 120, 212, 1)", HoverFill="RGBA(243, 242, 241, 1)",
                 HoverColor="RGBA(0, 120, 212, 1)", BorderColor="RGBA(0, 120, 212, 1)",
                 BorderStyle="BorderStyle.Solid", BorderThickness="1")
    return style


NAV = (("New", "New request", "NewRequestScreen", "true"), ("Mine", "My requests", "MyRequestsScreen", "true"),
       ("Rules", "Rules (MDM)", "AdminScreen", "IsMDM"))


def nav_buttons(n, active):
    """Header buttons for each screen ('Rules' only for the MDM team); the current screen's button is filled."""
    out = []
    for key, text, target, visible in NAV:
        on = key == active
        style = dict(BUTTON, Text=f'"{text}"', FillPortions="0", Width="140", Height="36", Size="11",
                     OnSelect=f"Navigate({target}, ScreenTransition.None)", Visible=visible)
        if not on:
            style.update(Fill="RGBA(255, 255, 255, 1)", Color="RGBA(0, 120, 212, 1)", HoverFill="RGBA(243, 242, 241, 1)",
                         HoverColor="RGBA(0, 120, 212, 1)", BorderColor="RGBA(0, 120, 212, 1)",
                         BorderStyle="BorderStyle.Solid", BorderThickness="1")
        out.append(ctl(f"btnGo{key}_{n}", "Classic/Button@2.2.0", style))
    return out


def header(n, title, active):
    return ctl(f"HeaderContainer{n}", "GroupContainer@1.5.0", dict(
        CARD, FillPortions="0", Height="75", LayoutAlignItems="LayoutAlignItems.Center",
        LayoutDirection="LayoutDirection.Horizontal", PaddingLeft="16", PaddingRight="16", LayoutGap="12"),
        [
            label(f"lblAppTitle{'' if n == 1 else n}", f'"{title}"', Size="18", Wrap="false",
                  FontWeight="FontWeight.Semibold", FillPortions="1", Height="40"),
            label(f"lblRequestor{'' if n == 1 else n}", '"Lives Group" & Char(10) & "Signed in: " & User().FullName',
                  Size="11", Wrap="true", Color="RGBA(96, 94, 92, 1)", Align="Align.Right", FillPortions="0",
                  Width="260", Height="48"),
        ] + nav_buttons(n, active), variant="AutoLayout")


def row(name, children, height, gap="12", align="LayoutAlignItems.Stretch", pad_left="0"):
    """A fixed-height horizontal strip (no wrapping: wrapped containers ignored child heights)."""
    return ctl(name, "GroupContainer@1.5.0", {
        "Fill": "RGBA(255, 255, 255, 1)", "FillPortions": "0", "Height": str(height), "LayoutMinHeight": "16",
        "LayoutMinWidth": "16", "LayoutDirection": "LayoutDirection.Horizontal", "LayoutAlignItems": align,
        "LayoutGap": gap, "PaddingLeft": pad_left, "DropShadow": "DropShadow.None"}, children, variant="AutoLayout")


edit_banner = ctl("EditBanner", "GroupContainer@1.5.0", dict(
    CARD, FillPortions="0", Height="150", Visible="Editing", Fill="RGBA(255, 244, 206, 1)",
    LayoutDirection="LayoutDirection.Vertical", LayoutAlignItems="LayoutAlignItems.Stretch",
    LayoutGap="4", PaddingLeft="16", PaddingRight="16"),
    [
        label("lblEditMessage", '"Editing " & EditID & ". " & Coalesce(EditAsk.ActorRole, "An approver") & '
                                '" asked for changes: " & Coalesce(EditAsk.Detail, "(no comment)")',
              Size="12", FontWeight="FontWeight.Semibold", FillPortions="0", Height="44", Wrap="true", PaddingLeft="0"),
        ctl("txtReplyNote", "Classic/TextInput@2.3.2", dict(
            TEXTINPUT, FillPortions="0", Height="38", Size="11", Default='""',
            HintText='"Reply to the approver (optional), e.g. Licence no. added from the HSA certificate"')),
        row("rowEditButtons", [
            label("lblEditHelp", '"Change the fields below, then press Resubmit. Only the approver who asked sees '
                                 'it again; the MDM final check sees what changed."',
                  FillPortions="1", Size="10", Wrap="true", Color="RGBA(96, 94, 92, 1)", PaddingLeft="0"),
            ctl("btnCancelEdit", "Classic/Button@2.2.0", outline(dict(
                BUTTON, Text='"Cancel edit"', FillPortions="0", Width="120", Height="34", Size="11",
                OnSelect='Set(gEditID, "");\nReset(txtReplyNote);\nNavigate(MyRequestsScreen, ScreenTransition.None)'))),
        ], 40, align="LayoutAlignItems.Center"),
    ], variant="AutoLayout")

screen_children = [
    header(1, "OneRecord | New request", "New"),
    edit_banner,
    ctl("DupBanner", "GroupContainer@1.5.0", dict(
        CARD, FillPortions="0", Height="If(tglNotDuplicate.Value, 168, 124)", Visible='DupStatus <> "Clear"',
        Fill='If(DupStatus = "Blocked", RGBA(253, 231, 233, 1), RGBA(255, 244, 206, 1))',
        LayoutDirection="LayoutDirection.Vertical", LayoutAlignItems="LayoutAlignItems.Stretch",
        LayoutGap="4", PaddingLeft="16", PaddingRight="16"),
        [
            label("lblDupMessage", "DupMessage", Size="11", FontWeight="FontWeight.Semibold",
                  FillPortions="0", Height="66", Wrap="true", VerticalAlign="VerticalAlign.Top"),
            ctl("tglNotDuplicate", "Classic/Toggle@2.1.0", dict(
                TOGGLE, FillPortions="0", Height="36", Width="420", Size="12",
                Default="If(Editing, !IsBlank(EditRec.DupReason), false)",
                AlignInContainer="AlignInContainer.Start",
                TrueText='If(DupStatus = "Blocked", "Not the same " & Noun, "This is a different " & Noun)',
                FalseText='If(DupStatus = "Blocked", "Not the same " & Noun, "This is a different " & Noun)')),
            ctl("txtDupReason", "Classic/TextInput@2.3.2", dict(
                TEXTINPUT, FillPortions="0", Height="38", Size="11", Visible="tglNotDuplicate.Value",
                Default='If(Editing, EditRec.DupReason, "")',
                HintText='"Why is it different? e.g. separate legal entity with its own registration no. (approvers see this)"')),
        ], variant="AutoLayout"),
    ctl("MainContainer1", "GroupContainer@1.5.0", dict(
        CARD, LayoutDirection="LayoutDirection.Vertical",
        LayoutAlignItems="LayoutAlignItems.Center", LayoutJustifyContent="LayoutJustifyContent.Start",
        LayoutOverflowY="LayoutOverflow.Scroll", LayoutGap="16", PaddingLeft="16", PaddingRight="16",
        PaddingTop="16", PaddingBottom="16"),
        top_blocks + [field_block(f) for f in FIELDS], variant="AutoLayout"),
    ctl("ApproverCard", "GroupContainer@1.5.0", dict(
        CARD, FillPortions="0", Height="84", LayoutDirection="LayoutDirection.Vertical",
        LayoutAlignItems="LayoutAlignItems.Stretch", LayoutGap="2", PaddingLeft="16", PaddingRight="16",
        Fill="If(ApproverGap, RGBA(255, 244, 206, 1), RGBA(239, 246, 252, 1))"),
        [
            label("lblApproverHead", '"Who will approve"', Size="11", FontWeight="FontWeight.Semibold",
                  FillPortions="0", Height="24", PaddingLeft="0"),
            label("lblApproverText", "ApproverText", Size="11", Wrap="true", FillPortions="1", PaddingLeft="0",
                  VerticalAlign="VerticalAlign.Top"),
        ], variant="AutoLayout"),
    ctl("FooterContainer1", "GroupContainer@1.5.0", dict(
        CARD, FillPortions="0", Height="75", LayoutAlignItems="LayoutAlignItems.Center",
        LayoutDirection="LayoutDirection.Horizontal", PaddingLeft="16", PaddingRight="16", LayoutGap="12"),
        [
            # Holds the ID of a sent-back request being edited; App formulas read it (see EditID)
            label("lblEditID", 'Coalesce(gEditID, "")', Visible="false", FillPortions="0", Width="10", Height="10"),
            label("lblStatus",
                  'If(IsBlank(gLastRequestID), "", "Last submitted: " & gLastRequestID & ".  ") & StatusText',
                  Size="11", Wrap="true", FillPortions="1", Height="56",
                  Color="If(CanSubmit, RGBA(16, 124, 16, 1), RGBA(96, 94, 92, 1))"),
            ctl("btnClear", "Classic/Button@2.2.0", dict(
                BUTTON, Text='"Clear"', FillPortions="0", Width="110", Height="40", Size="12",
                Fill="RGBA(255, 255, 255, 1)", Color="RGBA(0, 120, 212, 1)", HoverFill="RGBA(243, 242, 241, 1)",
                HoverColor="RGBA(0, 120, 212, 1)", BorderColor="RGBA(0, 120, 212, 1)",
                BorderStyle="BorderStyle.Solid", BorderThickness="1",
                OnSelect=";\n".join(f"Reset({t})" for t in reset_targets))),
            ctl("btnSubmit", "Classic/Button@2.2.0", dict(
                BUTTON, Text='If(Editing, "Resubmit", "Submit request")', FillPortions="0", Width="180", Height="40", Size="12",
                DisplayMode="If(CanSubmit, DisplayMode.Edit, DisplayMode.Disabled)", OnSelect=SUBMIT)),
        ], variant="AutoLayout"),
]

screen = ctl("ScreenContainer1", "GroupContainer@1.5.0", {
    "Fill": "RGBA(245, 245, 245, 1)", "Height": "Parent.Height", "Width": "Parent.Width",
    "LayoutAlignItems": "LayoutAlignItems.Stretch", "LayoutDirection": "LayoutDirection.Vertical",
    "LayoutGap": "16", "PaddingBottom": "16", "PaddingLeft": "16", "PaddingRight": "16", "PaddingTop": "16",
}, screen_children, variant="AutoLayout")

screen_yaml = HEADER + "\n".join([
    "Screens:", "  NewRequestScreen:", "    Properties:",
    "      Fill: =RGBA(245, 245, 245, 1)", "      LoadingSpinnerColor: =RGBA(0, 120, 212, 1)",
    "    Children:",
] + screen(6)) + "\n"

app_yaml = HEADER + "App:\n  Properties:\n    Formulas: |-\n" + indent("=" + FORMULAS, 6) + \
    "\n    Theme: =PowerAppsTheme\n"

# ---------------------------------------------------------------------------- My requests screen
STATUS_COLOR = ('Switch({s}, "Rejected", RGBA(164, 38, 44, 1), "Created in SAP", RGBA(16, 124, 16, 1), '
                '"Changes requested", RGBA(157, 93, 0, 1), "Ready for SAP import", RGBA(92, 46, 145, 1), '
                'RGBA(0, 90, 158, 1))')
row_name = ("Coalesce(ThisItem.CustomerName, ThisItem.ItemDescription, ThisItem.VendorName, "
            "ThisItem.CostCenterName)")
# Three fixed lines per row (ID and type, name, entity and status): wrapped text in one short label got clipped.
# Selecting a request re-reads the log, so the timeline isn't a cached, empty answer from an earlier look.
gallery = ctl("galRequests", "Gallery@2.15.0", {
    "Items": "MyRequestList", "TemplateSize": "104", "TemplatePadding": "0", "FillPortions": "1",
    "BorderColor": "RGBA(237, 235, 233, 1)", "BorderThickness": "1", "ShowScrollbar": "true",
    "TemplateFill": "If(ThisItem.IsSelected, RGBA(222, 236, 249, 1), RGBA(255, 255, 255, 1))",
    "LayoutMinHeight": "16", "LayoutMinWidth": "16", "OnSelect": "Refresh(ApprovalLog);\nRefresh(SensitiveDetails)",
}, [
    label("lblRowTitle", 'ThisItem.Title & " | " & ThisItem.RequestType',
          X="12", Y="8", Width="Parent.TemplateWidth - 130", Height="26", Size="12", Wrap="false",
          FontWeight="FontWeight.Semibold", OnSelect="Select(Parent)"),
    label("lblRowName", row_name,
          X="12", Y="34", Width="Parent.TemplateWidth - 24", Height="24", Size="11", Wrap="false",
          OnSelect="Select(Parent)"),
    label("lblRowStatus", 'ThisItem.Entity & "  |  " & ThisItem.Status & " - " & ThisItem.CurrentStage',
          X="12", Y="60", Width="Parent.TemplateWidth - 24", Height="40", Size="10", Wrap="true",
          VerticalAlign="VerticalAlign.Top", Color=STATUS_COLOR.format(s="ThisItem.Status"),
          OnSelect="Select(Parent)"),
    label("lblRowDays", 'DateDiff(Coalesce(ThisItem.SubmittedAt, ThisItem.Created), '
                        'Coalesce(ThisItem.CompletedAt, Now()), TimeUnit.Days) & " days open"',
          X="Parent.TemplateWidth - 122", Y="8", Width="110", Height="26", Size="10", Align="Align.Right",
          Wrap="false", Color="RGBA(96, 94, 92, 1)", OnSelect="Select(Parent)"),
    ctl("rectRowLine", "Rectangle@2.3.0", {"Fill": "RGBA(237, 235, 233, 1)", "BorderColor": "RGBA(0, 0, 0, 0)",
                                           "X": "0", "Y": "Parent.TemplateHeight - 1",
                                           "Width": "Parent.TemplateWidth", "Height": "1"}),
], variant="BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")


def shown_with_selection(c):
    """Wrap a control builder so it only shows once a request is selected."""
    def build(indent):
        lines = c(indent)
        pad = " " * (indent + 6)
        i = lines.index(f"{pad}Properties:") if f"{pad}Properties:" in lines else lines.index(" " * (indent + 4) + "Properties:")
        lines.insert(i + 1, " " * (indent + 6) + "Visible: =!IsBlank(galRequests.Selected)")
        return lines
    return build


def section(name, title, body_expr):
    return [
        label(f"lblHead{name}", f'"{title}"', Size="12", FontWeight="FontWeight.Semibold", FillPortions="0",
              Height="28", PaddingLeft="0"),
        label(f"lblBody{name}", body_expr, Size="11", Wrap="true", AutoHeight="true", FillPortions="0",
              Height="40", PaddingLeft="0", VerticalAlign="VerticalAlign.Top"),
    ]


list_panel = ctl("ListPanel", "GroupContainer@1.5.0", dict(
    CARD, FillPortions="0", Width="Max(360, Parent.Width * 0.45)", LayoutDirection="LayoutDirection.Vertical",
    LayoutAlignItems="LayoutAlignItems.Stretch", LayoutGap="8", PaddingLeft="12", PaddingRight="12",
    PaddingTop="12", PaddingBottom="12"), [
    ctl("FilterRow", "GroupContainer@1.5.0", {
        "Fill": "RGBA(255, 255, 255, 1)", "FillPortions": "0", "Height": "40", "LayoutMinHeight": "16",
        "LayoutMinWidth": "16", "LayoutDirection": "LayoutDirection.Horizontal",
        "LayoutAlignItems": "LayoutAlignItems.Center", "LayoutGap": "12", "DropShadow": "DropShadow.None"}, [
        ctl("ddStatusFilter", "Classic/DropDown@2.3.1", dict(
            DROPDOWN, Items=fx_list(["All", "Pending approval", "Changes requested", "Resubmitted", "Rejected",
                                     "Ready for SAP import", "Created in SAP"]), Default='"All"',
            FillPortions="0", Width="220", Height="36", Size="11")),
        ctl("tglShowAll", "Classic/Toggle@2.1.0", dict(
            TOGGLE, Default="false", Visible="IsMDM", FillPortions="1", Height="36", Size="11",
            TrueText='"All requests"', FalseText='"Only mine"')),
        ctl("btnRefresh", "Classic/Button@2.2.0", outline(dict(
            BUTTON, Text='"Refresh"', FillPortions="0", Width="100", Height="36", Size="11",
            OnSelect="Refresh(Requests);\nRefresh(ApprovalLog);\nRefresh(SensitiveDetails)"))),
    ], variant="AutoLayout"),
    label("lblListEmpty", '"No requests to show."', Visible="CountRows(galRequests.AllItems) = 0", FillPortions="0",
          Height="32", Size="11", Color="RGBA(96, 94, 92, 1)"),
    gallery,
], variant="AutoLayout")

# MDM confirms the SAP import; the Route and approve flow (waiting for this) logs it, updates the master list
# and tells the requestor. The ID goes through a plain value first, as for the log lookups.
MARK_CREATED = """With(
    {id: SelectedRequestID, code: Upper(Trim(txtSAPCode.Text))},
    IfError(
        Patch(Requests, LookUp(Requests, Title = id), {Status: "Created in SAP", SAPCode: code});
        Notify(id & " marked as created in SAP as " & code & ". The requestor will be told.", NotificationType.Success);
        Refresh(Requests),
        Notify("Couldn't update: " & FirstError.Message, NotificationType.Error)
    )
)"""

detail_panel = ctl("DetailPanel", "GroupContainer@1.5.0", dict(
    CARD, FillPortions="1", LayoutDirection="LayoutDirection.Vertical", LayoutAlignItems="LayoutAlignItems.Stretch",
    LayoutOverflowY="LayoutOverflow.Scroll", LayoutGap="6", PaddingLeft="20", PaddingRight="20", PaddingTop="16",
    PaddingBottom="16"), [
    label("lblPickOne", '"Select a request on the left to see where it stands."',
          Visible="IsBlank(galRequests.Selected)", FillPortions="0", Height="32", Size="11",
          Color="RGBA(96, 94, 92, 1)"),
] + [shown_with_selection(c) for c in [
        label("lblDetailTitle", 'SelectedRequest.Title & " - " & SelectedRequest.RequestType & " for " & '
                                'SelectedRequest.Entity', Size="16", FontWeight="FontWeight.Semibold",
              FillPortions="0", Height="32", PaddingLeft="0"),
        label("lblDetailName", "Coalesce(SelectedRequest.CustomerName, SelectedRequest.ItemDescription, "
                               "SelectedRequest.VendorName, SelectedRequest.CostCenterName)",
              Size="12", FillPortions="0", Height="26", PaddingLeft="0", Wrap="true"),
        label("lblDetailStatus", 'SelectedRequest.Status & " - " & SelectedRequest.CurrentStage', Size="12",
              FontWeight="FontWeight.Semibold", Wrap="true", AutoHeight="true", FillPortions="0", Height="30",
              PaddingLeft="0", Color=STATUS_COLOR.format(s="SelectedRequest.Status")),
    ]] + [
        ctl("btnEditResubmit", "Classic/Button@2.2.0", dict(
            BUTTON, Text='"Edit and resubmit"', FillPortions="0", Width="200", Height="38", Size="12",
            AlignInContainer="AlignInContainer.Start",
            Visible='!IsBlank(galRequests.Selected) && SelectedRequest.Status = "Changes requested" && '
                    "Lower(SelectedRequest.'Created By'.Email) = Lower(User().Email)",
            OnSelect="Set(gEditID, SelectedRequestID);\nNavigate(NewRequestScreen, ScreenTransition.None)")),
        ctl("SAPImportPanel", "GroupContainer@1.5.0", dict(
            CARD, FillPortions="0", Height="132", Fill="RGBA(243, 238, 250, 1)",
            Visible='!IsBlank(galRequests.Selected) && IsMDM && SelectedRequest.Status = "Ready for SAP import"',
            LayoutDirection="LayoutDirection.Vertical", LayoutAlignItems="LayoutAlignItems.Stretch", LayoutGap="4",
            PaddingLeft="12", PaddingRight="12"), [
            label("lblSAPImportHelp", '"Imported into SAP B1? Enter the code SAP gave it (normally the proposed code) and '
                                      'confirm. The requestor is told it is live, and the master list is updated."',
                  Size="10", Wrap="true", FillPortions="0", Height="40", PaddingLeft="0", Color=GREY),
            row("rowSAPImport", [
                ctl("txtSAPCode", "Classic/TextInput@2.3.2", dict(
                    TEXTINPUT, FillPortions="1", Height="36", Size="11", Default="SelectedRequest.SAPCode",
                    HintText='"SAP code"')),
                ctl("btnMarkCreated", "Classic/Button@2.2.0", dict(
                    BUTTON, Text='"Mark as created in SAP"', FillPortions="0", Width="220", Height="36", Size="11",
                    DisplayMode="If(IsBlank(Trim(txtSAPCode.Text)), DisplayMode.Disabled, DisplayMode.Edit)",
                    OnSelect=MARK_CREATED)),
            ], 40, align="LayoutAlignItems.Center"),
        ], variant="AutoLayout"),
    ] + [shown_with_selection(c) for c in
        section("Waiting", "Waiting on", "WaitingText")
      + section("Timeline", "Timeline", "TimelineText")
      + section("Submitted", "Submitted details", "SubmittedText")
      + section("Changes", "Changes after approvers asked", 'Coalesce(SelectedRequest.ChangeNote, "None.")')
      + section("Sensitive", "Sensitive details (only shown to you if SharePoint allows it)", "SensitiveText")], variant="AutoLayout")

mine_screen = ctl("ScreenContainer2", "GroupContainer@1.5.0", {
    "Fill": "RGBA(245, 245, 245, 1)", "Height": "Parent.Height", "Width": "Parent.Width",
    "LayoutAlignItems": "LayoutAlignItems.Stretch", "LayoutDirection": "LayoutDirection.Vertical",
    "LayoutGap": "16", "PaddingBottom": "16", "PaddingLeft": "16", "PaddingRight": "16", "PaddingTop": "16",
}, [
    header(2, "OneRecord | My requests", "Mine"),
    ctl("BodyContainer2", "GroupContainer@1.5.0", {
        "Fill": "RGBA(245, 245, 245, 1)", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
        "LayoutDirection": "LayoutDirection.Horizontal", "LayoutAlignItems": "LayoutAlignItems.Stretch",
        "LayoutGap": "16", "DropShadow": "DropShadow.None"}, [list_panel, detail_panel], variant="AutoLayout"),
], variant="AutoLayout")

mine_yaml = HEADER + "\n".join([
    "Screens:", "  MyRequestsScreen:", "    Properties:",
    "      Fill: =RGBA(245, 245, 245, 1)", "      LoadingSpinnerColor: =RGBA(0, 120, 212, 1)",
    "    Children:",
] + mine_screen(6)) + "\n"

# ---------------------------------------------------------------------------- Rules screen (MDM only)




def small_block(name, title, input_ctl):
    return ctl(name, "GroupContainer@1.5.0", {
        "Fill": "RGBA(255, 255, 255, 1)", "FillPortions": "1", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
        "LayoutDirection": "LayoutDirection.Vertical", "LayoutAlignItems": "LayoutAlignItems.Stretch",
        "LayoutGap": "4", "DropShadow": "DropShadow.None"}, [
        label(name.replace("blk", "lbl"), f'"{title}"', FillPortions="0", Height="22", Size="11",
              FontWeight="FontWeight.Semibold", PaddingLeft="0"),
        input_ctl], variant="AutoLayout")


def text_in(name, hint=""):
    return ctl(name, "Classic/TextInput@2.3.2", dict(TEXTINPUT, FillPortions="0", Height="36", Size="11",
                                                     Default='""', HintText=f'"{hint}"'))


NEW_BU_INPUTS = ["txtNewBUCode", "txtNewBUName", "txtNewBUProducts", "txtNewBUHeadName", "txtNewBUHeadEmail",
                 "txtNewBUEscalate", "ddNewBUTimeZone"]
ADD_BU = """With(
    {code: Upper(Trim(txtNewBUCode.Text)), email: Lower(Trim(txtNewBUHeadEmail.Text)),
     esc: Lower(Trim(txtNewBUEscalate.Text)), head: Trim(txtNewBUHeadName.Text)},
    If(
        IsBlank(code) || IsBlank(Trim(txtNewBUName.Text)) || IsBlank(head),
            Notify("Fill in the code, the name and the BU Head.", NotificationType.Warning),
        !IsMatch(email, Match.Email) || (!IsBlank(esc) && !IsMatch(esc, Match.Email)),
            Notify("Check the email addresses.", NotificationType.Warning),
        !IsBlank(LookUp(BusinessUnits, Title = code)),
            Notify(code & " already exists. Change it under Business units below.", NotificationType.Warning),
        IfError(
            Patch(BusinessUnits, Defaults(BusinessUnits),
                {Title: code, BusinessUnitName: Trim(txtNewBUName.Text), Products: Trim(txtNewBUProducts.Text),
                 Active: true});
            Patch(Roles, Defaults(Roles),
                {Title: "BU Head - " & code, Role: "BU Head", Entity: code, PersonName: head, PersonEmail: email,
                 EscalateTo: esc, TimeZone: ddNewBUTimeZone.Selected.Value});
            Notify(code & " added. It is on the request form now, and its BU Head approvals go to " & head & ".",
                   NotificationType.Success);
""" + ";\n".join(f"            Reset({c})" for c in NEW_BU_INPUTS) + """,
            Notify("Couldn't add the business unit: " & FirstError.Message, NotificationType.Error)
        )
    )
)"""

# One list + edit panel per rule list. A wide table didn't fit: the Teams tab gives the app ~700 px, and
# Power Apps pushes controls that overflow a gallery row back inside it, so they piled on top of each other.
# (key, menu name, list, gallery items, help text, row summary ({r} = the row), fields, extra Patch fields,
#  new-row record); field = (column, label, kind); kind: text | lower | num | bool | choice
GRIDS = [
    ("BU", "Business units", "BusinessUnits", "BusinessUnits",
     "The Business entity list on the request form. Switch Active off to retire a business unit.",
     '{r}.Title & "  |  " & {r}.BusinessUnitName & "  |  products " & {r}.Products & If({r}.Active, "", "  |  OFF")',
     [("Title", "Code", "text"), ("Products", "Products", "text"), ("BusinessUnitName", "Name", "text"),
      ("Active", "Active", "bool")],
     [], '{Title: "NEW", BusinessUnitName: "New business unit", Active: false}'),
    ("RR", "Approval steps", "RoutingRules", "Sort(RoutingRules, Title)",
     "Who approves what. Stage 1 steps run at the same time, then stage 2 (the MDM final check). "
     "'Only if' limits a step to regulated items or vendors. New steps start switched off.",
     '{r}.Title & "  |  " & {r}.RequestType & "  |  " & {r}.Entity & "  |  " & {r}.ApproverRole & '
     'If(IsBlank({r}.ConditionField), "", "  |  only if " & {r}.ConditionField) & "  |  stage " & {r}.Stage & '
     'If({r}.Active, "", "  |  OFF")',
     [("Title", "Rule", "text"), ("Active", "Active", "bool"), ("RequestType", "Request type", "choice"),
      ("Entity", "Entity (code or Any)", "text"), ("ApproverRole", "Approver role", "text"),
      ("ConditionField", "Only if", "choice"), ("Stage", "Stage (1 or 2)", "num"),
      ("SLADays", "Remind after (days)", "num"), ("EscalateAfterDays", "Escalate after (days)", "num")],
     [], '{Title: "R" & Text(Coalesce(First(Sort(RoutingRules, ID, SortOrder.Descending)).ID, 0) + 1, "00"), '
         'RequestType: "Any", Entity: "Any", Stage: 1, SLADays: 2, EscalateAfterDays: 4, Active: false}'),
    ("RF", "Form fields", "RequiredFields", "Sort(RequiredFields, RequestType)",
     "Labels, help text and when a field is required. Field name must be one the form already has. "
     "A new row does nothing until its request type is set.",
     '{r}.RequestType & "  |  " & {r}.DisplayLabel & "  (" & {r}.FieldName & ")  |  " & {r}.Required & '
     'If({r}.Required = "Conditional", " when " & {r}.ConditionField & " = " & {r}.ConditionValue, "")',
     [("RequestType", "Request type", "choice"), ("FieldName", "Field name", "text"),
      ("DisplayLabel", "Label", "text"), ("Required", "Required", "choice"),
      ("Check", "Format check (blank = default)", "choice"),
      ("ConditionField", "Only when field", "text"), ("ConditionValue", "equals", "text"),
      ("Sensitive", "Sensitive", "choice"), ("VisibleToRoles", "Sensitive values visible to", "text"),
      ("HelpText", "Help text", "text")],
     ['Title: ddRF_RequestType.Selected.Value & "." & Trim(txtRF_FieldName.Text)'],
     '{Title: "New field", Required: "Always", Sensitive: "No", VisibleToRoles: "All"}'),
    ("RO", "People", "Roles", "Sort(Roles, Role)",
     "Who holds each approver role, per business unit (or Any). Reminders go out at 9 AM in their time zone; "
     "escalations go to Escalate to.",
     '{r}.Role & "  |  " & {r}.Entity & "  |  " & {r}.PersonName & "  |  " & {r}.PersonEmail',
     [("Role", "Role", "text"), ("Entity", "Entity (code or Any)", "text"), ("PersonName", "Name", "text"),
      ("PersonEmail", "Email", "lower"), ("EscalateTo", "Escalate to (email)", "lower"),
      ("TimeZone", "Time zone", "choice")],
     ['Title: Trim(txtRO_Role.Text) & " - " & Trim(txtRO_Entity.Text)'],
     '{Title: "New person", Entity: "Any", TimeZone: "Asia/Singapore"}'),
    ("AL", "Known names", "Aliases", "Sort(Aliases, CanonicalName)",
     "Short or old names that mean an existing customer. Typing one on the form blocks a duplicate.",
     '{r}.Title & "  ->  " & {r}.CanonicalName & "  (" & {r}.RecordID & ")"',
     [("Title", "Name people type (lower case)", "lower"), ("RecordID", "SAP record", "text"),
      ("CanonicalName", "Official name", "text")],
     [], '{Title: "(new)"}'),
]
CHOICE_ITEMS = {("RR", "RequestType"): TYPES + ["Any"], ("RR", "ConditionField"): CONDITIONS,
                ("RF", "RequestType"): TYPES, ("RF", "Required"): ["Always", "Conditional"],
                ("RF", "Sensitive"): ["Yes", "No"], ("RF", "Check"): CHECKS, ("RO", "TimeZone"): TIME_ZONES}
GAL_H, ROW_H = 240, 66


def cell_name(key, field, kind):
    return {"bool": "tgl", "choice": "dd"}.get(kind, "txt") + f"{key}_{field}"


def edit_input(key, field, kind):
    """Input for one column of the selected row; classic inputs follow their Default when the selection changes."""
    n, cur = cell_name(key, field, kind), f"gal{key}.Selected.{field}"
    base = {"FillPortions": "0", "Height": "36", "Size": "11"}
    if kind == "bool":
        return ctl(n, "Classic/Toggle@2.1.0", dict(TOGGLE, **base, Width="160", Default=cur,
                                                   AlignInContainer="AlignInContainer.Start",
                                                   TrueText='"On"', FalseText='"Off"'))
    if kind == "choice":
        return ctl(n, "Classic/DropDown@2.3.1", dict(DROPDOWN, **base, Items=fx_list(CHOICE_ITEMS[key, field]),
                                                     AllowEmptySelection="true", Default=cur))
    return ctl(n, "Classic/TextInput@2.3.2", dict(TEXTINPUT, **base,
                                                  Default=f"Text({cur})" if kind == "num" else cur))


def cell_value(key, field, kind):
    n = cell_name(key, field, kind)
    return {"bool": f"{n}.Value", "choice": f"{n}.Selected.Value",
            "num": f"If(IsBlank(Trim({n}.Text)), Blank(), Value({n}.Text))",
            "lower": f"Lower(Trim({n}.Text))"}.get(kind, f"Trim({n}.Text)")


def grid(key, menu, lst, items, help_text, summary, cols, extra, new_row):
    gal = f"gal{key}"
    fields = extra + [f"{f}: {cell_value(key, f, k)}" for f, _, k in cols]
    save = (f"IfError(\n    Patch({lst}, {gal}.Selected, {{\n        " + ",\n        ".join(fields) + "\n    });\n"
            f'    Notify("Saved.", NotificationType.Success),\n'
            f'    Notify("Couldn\'t save: " & FirstError.Message, NotificationType.Error)\n)')
    add = (f"IfError(\n    Set(gNewRow{key}, Patch({lst}, Defaults({lst}), {new_row}));\n"
           f'    Notify("New row added and selected. Fill it in below and press Save.", NotificationType.Success),\n'
           f'    Notify("Couldn\'t add a row: " & FirstError.Message, NotificationType.Error)\n)')
    rows = [row(f"rowEdit{key}{i // 2 + 1}",
                [small_block(f"blk{key}_{f}", h, edit_input(key, f, k)) for f, h, k in cols[i:i + 2]], ROW_H)
            for i in range(0, len(cols), 2)]
    gallery = ctl(gal, "Gallery@2.15.0", {
        "Items": items, "Default": f"gNewRow{key}", "TemplateSize": "40", "TemplatePadding": "0",
        "FillPortions": "0", "Height": str(GAL_H), "BorderColor": "RGBA(237, 235, 233, 1)", "BorderThickness": "1",
        "ShowScrollbar": "true", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
        "TemplateFill": "If(ThisItem.IsSelected, RGBA(222, 236, 249, 1), RGBA(255, 255, 255, 1))"}, [
        label(f"lblRow{key}", summary.format(r="ThisItem"), X="10", Y="0", Width="Parent.TemplateWidth - 20",
              Height="Parent.TemplateHeight", Size="11", Wrap="false", OnSelect="Select(Parent)"),
        ctl(f"rectLine{key}", "Rectangle@2.3.0", {
            "Fill": "RGBA(237, 235, 233, 1)", "BorderColor": "RGBA(0, 0, 0, 0)", "X": "0",
            "Y": "Parent.TemplateHeight - 1", "Width": "Parent.TemplateWidth", "Height": "1"}),
    ], variant="BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")
    height = 44 + GAL_H + 28 + len(rows) * ROW_H + 44 + 6 * (len(rows) + 3)
    return ctl(f"Grid{key}", "GroupContainer@1.5.0", {
        "Fill": "RGBA(255, 255, 255, 1)", "FillPortions": "0", "Height": str(height), "LayoutMinHeight": "16",
        "LayoutMinWidth": "16", "LayoutDirection": "LayoutDirection.Vertical",
        "LayoutAlignItems": "LayoutAlignItems.Stretch", "LayoutGap": "6", "DropShadow": "DropShadow.None",
        "Visible": f'ddRuleList.Selected.Value = "{menu}"'}, [
        row(f"rowHelp{key}", [
            label(f"lblHelp{key}", f'"{help_text}"', FillPortions="1", Size="10", Wrap="true", Color=GREY,
                  PaddingLeft="0"),
            ctl(f"btnNewRow{key}", "Classic/Button@2.2.0", outline(dict(
                BUTTON, Text='"Add a row"', FillPortions="0", Width="120", Height="34", Size="11", OnSelect=add))),
        ], 44, align="LayoutAlignItems.Center"),
        gallery,
        label(f"lblEdit{key}", f'If(IsBlank({gal}.Selected), "Select a row to change it.", '
                               f'"Selected: " & {summary.format(r=gal + ".Selected")})',
              Size="11", FontWeight="FontWeight.Semibold", FillPortions="0", Height="28", PaddingLeft="0",
              Wrap="false"),
    ] + rows + [
        ctl(f"btnSave{key}", "Classic/Button@2.2.0", dict(
            BUTTON, Text='"Save changes"', FillPortions="0", Width="160", Height="40", Size="12",
            AlignInContainer="AlignInContainer.Start", OnSelect=save,
            DisplayMode=f"If(IsBlank({gal}.Selected), DisplayMode.Disabled, DisplayMode.Edit)")),
    ], variant="AutoLayout")


admin_body = ctl("AdminBody", "GroupContainer@1.5.0", dict(
    CARD, FillPortions="1", Visible="IsMDM", LayoutDirection="LayoutDirection.Vertical",
    LayoutAlignItems="LayoutAlignItems.Stretch", LayoutOverflowY="LayoutOverflow.Scroll", LayoutGap="10",
    PaddingLeft="20", PaddingRight="20", PaddingTop="16", PaddingBottom="16"), [
    label("lblCheckHead", '"Rules check"', Size="14", FontWeight="FontWeight.Semibold", FillPortions="0",
          Height="30", PaddingLeft="0"),
    label("lblCheckBody",
          'If(IsBlank(RuleGapText), "Every active business unit has someone set up for every approval step.", '
          'RuleGapText & "Until this is fixed, those steps go to the MDM team. Add the person under People, '
          'or use Add a business unit.")',
          Size="11", Wrap="true", AutoHeight="true", FillPortions="0", Height="30", PaddingLeft="0",
          VerticalAlign="VerticalAlign.Top",
          Color="If(IsBlank(RuleGapText), RGBA(16, 124, 16, 1), RGBA(164, 38, 44, 1))"),
    label("lblAddHead", '"Add a business unit"', Size="14", FontWeight="FontWeight.Semibold", FillPortions="0",
          Height="30", PaddingLeft="0"),
    label("lblAddHelp", '"Creates the business unit and its BU Head in one step. The request form and the approval '
                        'flow use them on the next request. The rules check above shows anything else it needs."',
          Size="10", Wrap="true", FillPortions="0", Height="36", PaddingLeft="0", Color=GREY),
    row("rowNewBU1", [
        small_block("blkNewBUCode", "Code", text_in("txtNewBUCode", "e.g. LGD")),
        small_block("blkNewBUProducts", "Products", text_in("txtNewBUProducts", "e.g. A")),
    ], ROW_H),
    row("rowNewBU2", [
        small_block("blkNewBUName", "Name", text_in("txtNewBUName", "e.g. LGD (molecular diagnostics)")),
    ], ROW_H),
    row("rowNewBU3", [
        small_block("blkNewBUHeadName", "BU Head name", text_in("txtNewBUHeadName")),
        small_block("blkNewBUTimeZone", "BU Head time zone", ctl("ddNewBUTimeZone", "Classic/DropDown@2.3.1", dict(
            DROPDOWN, Items=fx_list(TIME_ZONES), Default='"Asia/Singapore"', FillPortions="0", Height="36",
            Size="11"))),
    ], ROW_H),
    row("rowNewBU4", [
        small_block("blkNewBUHeadEmail", "BU Head email", text_in("txtNewBUHeadEmail", "their Lives Group email")),
        small_block("blkNewBUEscalate", "Escalate to (optional)", text_in("txtNewBUEscalate", "email")),
    ], ROW_H),
    ctl("btnAddBU", "Classic/Button@2.2.0", dict(
        BUTTON, Text='"Add business unit"', FillPortions="0", Width="200", Height="40", Size="12",
        AlignInContainer="AlignInContainer.Start", OnSelect=ADD_BU)),
    label("lblListsHead", '"Rule lists"', Size="14", FontWeight="FontWeight.Semibold", FillPortions="0",
          Height="30", PaddingLeft="0"),
    row("rowPickList", [
        label("lblPickList", '"Show"', FillPortions="0", Width="50", Height="36", Size="11", PaddingLeft="0"),
        ctl("ddRuleList", "Classic/DropDown@2.3.1", dict(
            DROPDOWN, Items=fx_list([g[1] for g in GRIDS]), Default=f'"{GRIDS[0][1]}"', FillPortions="0",
            Width="260", Height="36", Size="11")),
        label("lblPickNote", '"Changes apply to the next request. SharePoint keeps every earlier version of '
                             'each row."', FillPortions="1", Height="36", Size="10", Color=GREY, Wrap="true"),
    ], 44, align="LayoutAlignItems.Center"),
] + [grid(*g) for g in GRIDS], variant="AutoLayout")

admin_screen = ctl("ScreenContainer3", "GroupContainer@1.5.0", {
    "Fill": "RGBA(245, 245, 245, 1)", "Height": "Parent.Height", "Width": "Parent.Width",
    "LayoutAlignItems": "LayoutAlignItems.Stretch", "LayoutDirection": "LayoutDirection.Vertical",
    "LayoutGap": "16", "PaddingBottom": "16", "PaddingLeft": "16", "PaddingRight": "16", "PaddingTop": "16",
}, [
    header(3, "OneRecord | Rules", "Rules"),
    label("lblNotMDM", '"Only the MDM team can change the rules."', Visible="!IsMDM", FillPortions="0", Height="40",
          Size="12", Color=GREY),
    admin_body,
], variant="AutoLayout")

admin_yaml = HEADER + "\n".join([
    "Screens:", "  AdminScreen:", "    Properties:",
    "      Fill: =RGBA(245, 245, 245, 1)", "      LoadingSpinnerColor: =RGBA(0, 120, 212, 1)",
    "    Children:",
] + admin_screen(6)) + "\n"

(SRC / "NewRequestScreen.pa.yaml").write_text(screen_yaml)
(SRC / "MyRequestsScreen.pa.yaml").write_text(mine_yaml)
(SRC / "AdminScreen.pa.yaml").write_text(admin_yaml)
(SRC / "App.pa.yaml").write_text(app_yaml)
(SRC / "_EditorState.pa.yaml").write_text(HEADER + "EditorState:\n  ScreensOrder:\n    - NewRequestScreen\n    - MyRequestsScreen\n    - AdminScreen\n")

# Paste-ready pieces for Studio: App > Formulas, and each screen's top container (Paste code)
PASTE = SRC.parent.parent / "paste"
PASTE.mkdir(exist_ok=True)
(PASTE / "1-App-Formulas.txt").write_text(FORMULAS + "\n")
(PASTE / "2-ScreenContainer1.yaml").write_text("\n".join(screen(0)) + "\n")
(PASTE / "3-MyRequestsScreen-ScreenContainer2.yaml").write_text("\n".join(mine_screen(0)) + "\n")
(PASTE / "4-AdminScreen-ScreenContainer3.yaml").write_text("\n".join(admin_screen(0)) + "\n")
print("NewRequestScreen controls:", screen_yaml.count("Control:"), "| MyRequestsScreen controls:", mine_yaml.count("Control:"),
      "| AdminScreen controls:", admin_yaml.count("Control:"))
