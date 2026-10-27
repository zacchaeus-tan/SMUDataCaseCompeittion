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
# Dropdowns whose options come from the ChoiceOptions list (MDM edits them on the Rules screen; "Country" is the
# customer country). Payment terms stay fixed here: Finance owns them. The values above seed sharepoint/ChoiceOptions.csv.
EDITABLE_CHOICES = {"ProductFamily": CHOICES["ProductFamily"], "Country": COUNTRIES, "Segment": CHOICES["Segment"],
                    "UnitOfMeasure": CHOICES["UnitOfMeasure"], "Department": CHOICES["Department"]}
# Request fields an approval step can depend on. Must match ROUTE_FIELDS in powerautomate/build_route_approve.py.
ROUTE_FIELDS = ["Country", "ProductFamily", "IsRegulated", "SuppliesRegulatedGoods", "Segment", "UnitOfMeasure",
                "Department"]

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
      Check: Check, Title: Title}}
);
TypeRules = Filter(FieldRules, RequestType = SelectedType);

// Dropdown options (ChoiceOptions list, edited on the Rules screen), loaded once like the field rules
ChoiceRows = ForAll(ChoiceOptions, {{List: ListName, Value: Title, Order: SortOrder, Active: Active, Details: Details}});

// What the requestor has entered so far, keyed by the FieldName used in the RequiredFields list.
FieldValues = Table(
{field_value_rows()}
);

// A field shows (and is required) when its rule is "Always", or when its condition is met: the other field has one
// of the listed values ("A;D" = A or D; case and spaces ignored, as for approval steps).
VisibleFields = Filter(
    TypeRules,
    Required <> "Conditional" ||
    Lower(Substitute(Coalesce(LookUp(FieldValues, F = ConditionField).V, "-"), " ", "")) in
        Split(Lower(Substitute(Substitute(Coalesce(ConditionValue, ""), " ", ""), ",", ";")), ";")
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
RolesRows = ForAll(Roles, {{ID: ID, Role: Role, Entity: Entity, Name: PersonName, Email: Lower(PersonEmail),
                             EscalateTo: EscalateTo, TimeZone: TimeZone}});
IsMDM = !IsBlank(LookUp(RolesRows, Role = "MDM Analyst" && Email = Lower(User().Email)));
// For judging: anyone can open the Rules screen to look; only MDM can change anything. false after judging.
RulesViewForAll = true;
CanSeeRules = IsMDM || RulesViewForAll;
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
DecisionActions = ["Approve", "Reject", "Request changes", "Cancelled"];
// Once a request is rejected, cancelled or closed, its other open cards no longer count.
WaitingOn = Filter(
    SelectedLog As a,
    SelectedRequest.Status in ["Pending approval", "Changes requested", "Resubmitted"] &&
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
        ) & " (waiting " & DateDiff(w.At, Now(), TimeUnit.Days) & " days)" &
        // The flow re-sends an unanswered stage-1 card to the approver's manager and logs "Escalated" with the
        // same "Stage N, round R" as the Assigned row
        If(!IsBlank(LookUp(SelectedLog As x, x.Action = "Escalated" && x.Role = w.Role && StartsWith(x.Detail, w.Detail & ":"))),
           ", escalated: " & Coalesce(
               LookUp(RolesRows, Email = LookUp(SelectedLog As x, x.Action = "Escalated" && x.Role = w.Role &&
                                                StartsWith(x.Detail, w.Detail & ":")).Actor).Name,
               "their manager") & " can answer too", ""),
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
CONDITIONS = ROUTE_FIELDS  # the "Only if" fields the Route and approve flow understands

# Plain string (not an f-string), so Power Fx braces stay single.
FORMULAS += """

// ---- Who will approve: the same rules the Route and approve flow reads (RoutingRules + Roles)
RuleRows = ForAll(
    RoutingRules,
    {Rule: Title, RequestType: RequestType, Entity: Entity, ConditionField: ConditionField,
     ConditionValue: ConditionValue, Role: ApproverRole, Stage: Stage, SLADays: SLADays, Active: Active}
);
// The request's values for the "Only if" conditions, matched like the flow does: lower case, no spaces, blank = "-",
// regulated "Not sure" counts as Yes (it is saved as Yes and goes to Quality/Regulatory). A field that isn't on this
// request type isn't saved, so it counts as blank (a Yes/No field as No), even if its hidden control still holds a value.
RouteFields = ROUTE_FIELDS_FX;
RouteFacts = ForAll(
    Filter(FieldValues, F in RouteFields) As fv,
    {F: fv.F,
     V: With({yn: fv.F in ["IsRegulated", "SuppliesRegulatedGoods"], onType: fv.F in TypeRules.FieldName},
         With({v: If(!onType, If(yn, "No", ""), fv.F = "IsRegulated", If(fv.V in ["Yes", "Not sure"], "Yes", "No"), fv.V)},
              If(IsBlank(Trim(v)), "-", Lower(Substitute(v, " ", "")))))}
);
// Like the flow: the first Roles row for the role and entity (or Any); no "@" in its email = nobody set up.
ApproverPreview = ForAll(
    Filter(RuleRows As x,
        x.Active && (x.RequestType = SelectedType || x.RequestType = "Any") &&
        (x.Entity = SelectedEntity || x.Entity = "Any") &&
        (IsBlank(x.ConditionField) ||
         (!IsBlank(x.ConditionValue) &&
          Coalesce(LookUp(RouteFacts, F = x.ConditionField).V, "-") in
              Split(Lower(Substitute(Substitute(x.ConditionValue, " ", ""), ",", ";")), ";")))
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
);
// Active approval steps whose "Only if" can never match: an unknown field, or no value to compare with
RuleProblemText = Concat(
    Filter(RuleRows, Active && !IsBlank(ConditionField) && (!(ConditionField in RouteFields) || IsBlank(ConditionValue))),
    "Approval step " & Rule & ": " &
    If(ConditionField in RouteFields, "'Only if " & ConditionField & "' has no value after 'is', so it never applies",
       "'" & ConditionField & "' isn't a field approval steps can depend on, so it never applies") & Char(10)
);"""
FORMULAS = FORMULAS.replace("ROUTE_FIELDS_FX", fx_list(ROUTE_FIELDS))

# Fields a step or a form field can depend on, per request type (dropdowns or Yes/No only; vendor country is free
# text and payment terms belong to Finance, so neither is offered)
TYPE_FIELDS = [("Customer", "Country"), ("Customer", "Segment"), ("Item", "ProductFamily"), ("Item", "IsRegulated"),
               ("Item", "UnitOfMeasure"), ("Vendor", "SuppliesRegulatedGoods"), ("Cost Center", "Department")]
PLAIN = dict(LABELS, IsRegulated="Regulated", ProductFamily="Product family")
FORMULAS += f"""

// ---- Rules screen: plain names for fields, the fields a rule can depend on, and the business choices
FieldLabels = Table(
{",\n".join(f'    {{F: "{k}", L: "{v}"}}' for k, v in PLAIN.items())}
);
TypeFields = Table(
{",\n".join(f'    {{Type: "{t}", F: "{f}", L: "{PLAIN[f]}"}}' for t, f in TYPE_FIELDS)}
);
BusinessChoices = With(
    {{bus: ForAll(Sort(Filter(BusinessUnits, Active = true), Title), {{Value: BusinessUnitName, Code: Title}})}},
    ForAll(Sequence(CountRows(bus) + 1),
        If(Value = 1, {{Value: "All businesses", Code: "Any"}},
           {{Value: Index(bus, Value - 1).Value, Code: Index(bus, Value - 1).Code}}))
);
ApproverRoles = Sort(Distinct(Filter(RolesRows, Role <> "Requestor" && Role <> "MDM Analyst"), Role), Value);"""


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
    build = lambda indent: emit(name, control, props, children, variant, indent)
    build.name = name  # so a parent can add up its children's heights
    return build


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
        items = (f'ForAll(Sort(Filter(ChoiceRows, List = "{name}" && Active), Order), {{Value: Value}})'
                 if name in EDITABLE_CHOICES else fx_list(COUNTRIES if kind == "country" else CHOICES[name]))
        p = dict(DROPDOWN, **base, Items=items, AllowEmptySelection="true", Default=default, Size="12")
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

# A Teams link (?requestId=) opens My requests; the Streamlit pages that embed the app pick a screen with ?screen=
START_SCREEN = ('If(!IsBlank(Param("requestId")), MyRequestsScreen, Param("screen") = "mine", MyRequestsScreen, '
                'Param("screen") = "rules", AdminScreen, NewRequestScreen)')
app_yaml = HEADER + "App:\n  Properties:\n    Formulas: |-\n" + indent("=" + FORMULAS, 6) + \
    "\n    StartScreen: =" + START_SCREEN + \
    "\n    Theme: =PowerAppsTheme\n"

# ---------------------------------------------------------------------------- My requests screen
STATUS_COLOR = ('Switch({s}, "Rejected", RGBA(164, 38, 44, 1), "On hold", RGBA(164, 38, 44, 1), '
                '"Cancelled", RGBA(96, 94, 92, 1), '
                '"Created in SAP", RGBA(16, 124, 16, 1), '
                '"Changes requested", RGBA(157, 93, 0, 1), "Ready for SAP import", RGBA(92, 46, 145, 1), '
                'RGBA(0, 90, 158, 1))')
row_name = ("Coalesce(ThisItem.CustomerName, ThisItem.ItemDescription, ThisItem.VendorName, "
            "ThisItem.CostCenterName)")
# Three fixed lines per row (ID and type, name, entity and status): wrapped text in one short label got clipped.
# Selecting a request re-reads the log, so the timeline isn't a cached, empty answer from an earlier look.
gallery = ctl("galRequests", "Gallery@2.15.0", {
    "Items": "MyRequestList", "TemplateSize": "104",
    # Opened from a Teams link (...&requestId=REQ-0004): select that request
    "Default": 'If(!IsBlank(Param("requestId")), LookUp(MyRequestList, Title = Param("requestId")))', "TemplatePadding": "0", "FillPortions": "1",
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
                                     "Cancelled", "On hold", "Ready for SAP import", "Created in SAP"]),
            Default='"All"',
            FillPortions="0", Width="220", Height="36", Size="11")),
        ctl("tglShowAll", "Classic/Toggle@2.1.0", dict(
            TOGGLE, Default='IsMDM && !IsBlank(Param("requestId"))', Visible="IsMDM", FillPortions="1", Height="36", Size="11",
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
     "'Only if' + 'is' limits a step to requests with that value, e.g. Product family is D, or Country is ID;VN "
     "(any of them). Vendor country is typed in full, e.g. Indonesia. New steps start switched off.",
     '{r}.Title & "  |  " & {r}.RequestType & "  |  " & {r}.Entity & "  |  " & {r}.ApproverRole & '
     'If(IsBlank({r}.ConditionField), "", "  |  only if " & {r}.ConditionField & " is " & {r}.ConditionValue) & '
     '"  |  stage " & {r}.Stage & '
     'If({r}.Active, "", "  |  OFF")',
     [("Title", "Rule", "text"), ("Active", "Active", "bool"), ("RequestType", "Request type", "choice"),
      ("Entity", "Entity (code or Any)", "text"), ("ApproverRole", "Approver role", "text"),
      ("ConditionField", "Only if", "choice"), ("ConditionValue", "is (several: separate with ;)", "text"),
      ("Stage", "Stage (1 or 2)", "num"),
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
    ("CO", "Dropdown options", "ChoiceOptions", 'Sort(ChoiceOptions, ListName & Text(SortOrder, "000"))',
     "The choices in the request form's dropdowns (Country = customer country). A new product line: add it here, "
     "then its fields under Form fields (Only when field ProductFamily equals D) and any extra approval under "
     "Approval steps. Switch Active off to retire an option; earlier requests keep their value.",
     '{r}.ListName & "  |  " & {r}.Title & "  |  order " & {r}.SortOrder & If({r}.Active, "", "  |  OFF")',
     [("ListName", "Dropdown", "choice"), ("Title", "Option", "text"), ("SortOrder", "Order", "num"),
      ("Active", "Active", "bool")],
     [], '{Title: "New option", ListName: "ProductFamily", SortOrder: 99, Active: false}'),
]
CHOICE_ITEMS = {("RR", "RequestType"): TYPES + ["Any"], ("RR", "ConditionField"): CONDITIONS,
                ("RF", "RequestType"): TYPES, ("RF", "Required"): ["Always", "Conditional"],
                ("RF", "Sensitive"): ["Yes", "No"], ("RF", "Check"): CHECKS, ("RO", "TimeZone"): TIME_ZONES,
                ("CO", "ListName"): list(EDITABLE_CHOICES)}
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
                BUTTON, Text='"Add a row"', FillPortions="0", Width="120", Height="34", Size="11", OnSelect=add,
                DisplayMode="If(IsMDM, DisplayMode.Edit, DisplayMode.Disabled)"))),
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
            DisplayMode=f"If(IsBlank({gal}.Selected) || !IsMDM, DisplayMode.Disabled, DisplayMode.Edit)")),
    ], variant="AutoLayout")


# ---- Rules screen, redesigned: one tab per request type showing its whole process in plain words (form fields, then
# approval chain), plus Businesses and people, Product lines and Advanced (the raw list editor). Every change is made
# in a panel with dropdowns and tick-chips, which replaces the view while it's open and reads the rule back as a
# sentence. Screen state lives in context variables: locTab (tab), locPanel ("" or step / field / person / bu /
# line), locStep / locField / locPerson (the row being changed; blank = adding), and the chip collections colPick,
# colPickF, colPickBU, colLineFields.

TAB = 'Coalesce(locTab, "Customer")'
TYPE_TABS = [("Customer", "Customer"), ("Item", "Item"), ("Vendor", "Vendor"), ("Cost Center", "Cost centre")]
OTHER_TABS = [("People", "Businesses and people"), ("Lines", "Product lines"), ("Advanced", "Advanced")]
ON_TYPE_TAB = f"{TAB} in {fx_list(TYPES)}"
BLUE, WHITE, AMBER = "RGBA(0, 120, 212, 1)", "RGBA(255, 255, 255, 1)", "RGBA(157, 93, 0, 1)"
NEXT_RULE = '"R" & Text(Coalesce(First(Sort(RoutingRules, ID, SortOrder.Descending)).ID, 0) + 1, "00")'


def mdm_only(extra):
    """Rules-screen buttons change rules, so they're disabled for anyone else viewing the screen."""
    extra["DisplayMode"] = f'If(IsMDM, {extra.get("DisplayMode", "DisplayMode.Edit")}, DisplayMode.Disabled)'
    return extra


def btn(name, text, onselect, primary=False, width=150, height=36, **extra):
    mdm_only(extra)
    style = dict(BUTTON, Text=text, FillPortions="0", Width=str(width), Height=str(height), Size="11",
                 OnSelect=onselect, **extra)
    return ctl(name, "Classic/Button@2.2.0", style if primary else outline(style))


def vbox(name, children, visible="true", gap="8", **extra):
    """A white card stacking its children; height follows the children (inside a scrolling body)."""
    height = (f"24 + " + " + ".join(f"If({c.name}.Visible, {c.name}.Height + {gap}, 0)" for c in children)
              + f" - {gap}")
    props = dict(CARD, FillPortions="0", LayoutDirection="LayoutDirection.Vertical",
                 LayoutAlignItems="LayoutAlignItems.Stretch", LayoutGap=gap, PaddingLeft="16", PaddingRight="16",
                 PaddingTop="12", PaddingBottom="12", Visible=visible, Height=height)
    props.update(extra)
    return ctl(name, "GroupContainer@1.5.0", props, children, variant="AutoLayout")


def head(name, text, size="13", **extra):
    p = dict(Size=size, FontWeight="FontWeight.Semibold", FillPortions="0", Height="28", PaddingLeft="0")
    p.update(extra)
    return label(name, text, **p)


def note(name, text, height="36", color=GREY, **extra):
    p = dict(Size="10", Wrap="true", FillPortions="0", Height=height, PaddingLeft="0", Color=color)
    p.update(extra)
    return label(name, text, **p)


def field(name, title, input_ctl, visible="true"):
    """Label on the left, input on the right (one line)."""
    return ctl(name, "GroupContainer@1.5.0", {
        "Fill": WHITE, "FillPortions": "0", "Height": "44", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
        "LayoutDirection": "LayoutDirection.Horizontal", "LayoutAlignItems": "LayoutAlignItems.Center",
        "LayoutGap": "12", "DropShadow": "DropShadow.None", "Visible": visible}, [
        label(name.replace("fld", "lblF"), title, FillPortions="0", Width="140", Height="36", Size="11",
              PaddingLeft="0", Color=GREY),
        input_ctl], variant="AutoLayout")


def dd(name, items, default='""', empty=True, **extra):
    return ctl(name, "Classic/DropDown@2.3.1", dict(DROPDOWN, Items=items, Default=default, FillPortions="1",
                                                    Height="36", Size="11",
                                                    AllowEmptySelection="true" if empty else "false", **extra))


def tin(name, default='""', hint="", **extra):
    return ctl(name, "Classic/TextInput@2.3.2", dict(TEXTINPUT, Default=default, HintText=f'"{hint}"',
                                                     FillPortions="1", Height="36", Size="11", **extra))


def options(f, not_sure=False):
    """The values a field can take: Yes/No (Not sure too for the form's regulated question) or its dropdown options."""
    yes_no = 'Table({Value: "Yes"}, {Value: "No"})'
    reg = 'Table({Value: "Yes"}, {Value: "No"}, {Value: "Not sure"})' if not_sure else yes_no
    return (f'Switch({f}, "IsRegulated", {reg}, "SuppliesRegulatedGoods", {yes_no}, '
            f'ForAll(Sort(Filter(ChoiceRows, List = {f} && Active), Order), {{Value: Value}}))')


def chips(name, items, coll, key="Value", text="ThisItem.Value", per_row=5, visible="true", record=None):
    """Tick-chips: a wrapping gallery of buttons that add or remove their value in a collection."""
    picked = f"!IsBlank(LookUp({coll}, Lower({key}) = Lower(ThisItem.{key})))"
    toggle = (f"If({picked}, RemoveIf({coll}, Lower({key}) = Lower(ThisItem.{key})), "
              f"Collect({coll}, {record or '{' + key + ': ThisItem.' + key + '}'}))")
    return ctl(name, "Gallery@2.15.0", {
        "Items": items, "WrapCount": str(per_row), "TemplateSize": "40", "TemplatePadding": "0",
        "FillPortions": "0", "Height": f"40 * RoundUp(CountRows({items}) / {per_row}, 0) + 4",
        "BorderThickness": "0", "ShowScrollbar": "false", "LayoutMinHeight": "16", "LayoutMinWidth": "16",
        "Visible": visible}, [
        ctl(name.replace("gal", "btn"), "Classic/Button@2.2.0", dict(
            BUTTON, Text=text, X="2", Y="4", Width="Parent.TemplateWidth - 8", Height="32", Size="11",
            Fill=f"If({picked}, {BLUE}, {WHITE})", Color=f"If({picked}, {WHITE}, {BLUE})",
            HoverFill=f"If({picked}, RGBA(16, 110, 190, 1), RGBA(243, 242, 241, 1))",
            HoverColor=f"If({picked}, {WHITE}, {BLUE})", BorderColor=BLUE, BorderStyle="BorderStyle.Solid",
            BorderThickness="1", OnSelect=toggle)),
    ], variant="BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")


def list_gallery(name, items, size, children):
    """A plain list that shows every row (no inner scrolling)."""
    return ctl(name, "Gallery@2.15.0", {
        "Items": items, "TemplateSize": str(size), "TemplatePadding": "0", "FillPortions": "0",
        "Height": f"{size} * CountRows({items}) + 2", "BorderColor": "RGBA(237, 235, 233, 1)",
        "BorderThickness": "1", "ShowScrollbar": "false", "LayoutMinHeight": "16", "LayoutMinWidth": "16"},
        children + [ctl(f"rect{name[3:]}", "Rectangle@2.3.0", {
            "Fill": "RGBA(237, 235, 233, 1)", "BorderColor": "RGBA(0, 0, 0, 0)", "X": "0",
            "Y": "Parent.TemplateHeight - 1", "Width": "Parent.TemplateWidth", "Height": "1"})],
        variant="BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")


def cell(name, text, x, width, y="0", height="Parent.TemplateHeight - 1", **extra):
    p = dict(X=x, Y=y, Width=width, Height=height, Size="11", Wrap="true", VerticalAlign="VerticalAlign.Middle")
    p.update(extra)
    return label(name, text, **p)


def row_btn(name, text, onselect, right, width=76, **extra):
    mdm_only(extra)
    return ctl(name, "Classic/Button@2.2.0", outline(dict(
        BUTTON, Text=text, X=f"Parent.TemplateWidth - {right}", Y="(Parent.TemplateHeight - 30) / 2",
        Width=str(width), Height="30", Size="10", OnSelect=onselect, **extra)))


def picked(coll, opts):
    """The ticked values that the chosen field still offers (ticks left over from another field don't count)."""
    return f"Filter({coll}, Lower(Value) in ForAll({opts}, {{V: Lower(Value)}}).V)"


def readback(cond_field, coll, word="is"):
    return (f'"only when " & Coalesce(LookUp(FieldLabels, F = {cond_field}).L, {cond_field}) & " {word} " & '
            f'Concat({coll}, Value, " or ")')


def when_text(cf, cv, always='"always"'):
    return (f'If(IsBlank({cf}), {always}, "only when " & Coalesce(LookUp(FieldLabels, F = {cf}).L, {cf}) & '
            f'" is " & Substitute({cv}, ";", " or "))')


def buttons(name, cancel, save, save_text='"Save"'):
    return row(name, [
        label(f"lbl{name}Gap", '""', FillPortions="1", Height="36"),
        btn(f"btn{name}Cancel", '"Cancel"', cancel, width=110),
        btn(f"btn{name}Save", save_text, save, primary=True, width=150),
    ], 44, align="LayoutAlignItems.Center")


CLOSE = 'UpdateContext({locPanel: ""})'

# ---- tab bar
def tab_btn(key, text, width):
    on = f'{TAB} = "{key}"'
    style = dict(BUTTON, Text=f'"{text}"', FillPortions="0", Width=str(width), Height="34", Size="11",
                 OnSelect=f'UpdateContext({{locTab: "{key}", locPanel: ""}})',
                 Fill=f"If({on}, {BLUE}, {WHITE})", Color=f"If({on}, {WHITE}, {BLUE})",
                 HoverFill=f"If({on}, RGBA(16, 110, 190, 1), RGBA(243, 242, 241, 1))",
                 HoverColor=f"If({on}, {WHITE}, {BLUE})", BorderColor=BLUE, BorderStyle="BorderStyle.Solid",
                 BorderThickness="1")
    return ctl(f"btnTab{key.replace(' ', '')}", "Classic/Button@2.2.0", style)


tab_bar = vbox("RulesTabs", [
    row("rowTabs1", [label("lblTabs1", '"Request types"', FillPortions="0", Width="110", Height="34", Size="10",
                           Color=GREY, PaddingLeft="0")]
        + [tab_btn(k, t, 110) for k, t in TYPE_TABS], 40, gap="8", align="LayoutAlignItems.Center"),
    row("rowTabs2", [label("lblTabs2", '"Set-up"', FillPortions="0", Width="110", Height="34", Size="10",
                           Color=GREY, PaddingLeft="0")]
        + [tab_btn(k, t, w) for (k, t), w in zip(OTHER_TABS, (190, 140, 110))], 40, gap="8",
        align="LayoutAlignItems.Center"),
], gap="4")

check_banner = vbox("RulesCheck", [
    head("lblCheckHead", '"Needs attention"'),
    label("lblCheckBody", 'RuleGapText & RuleProblemText & "Until a missing person is added, their steps go to the '
                          'MDM team (Businesses and people)."',
          Size="11", Wrap="true", AutoHeight="true", FillPortions="0", Height="30", PaddingLeft="0",
          VerticalAlign="VerticalAlign.Top", Color="RGBA(164, 38, 44, 1)"),
], visible="!IsBlank(RuleGapText & RuleProblemText)", Fill="RGBA(253, 231, 233, 1)", gap="2")

# ---- process view (one request type)
FIELD_ROWS = f"Filter(FieldRules, RequestType = {TAB})"
OPEN_FIELD = ("UpdateContext({locPanel: \"field\", locField: LookUp(RequiredFields, Title = ThisItem.Title)});\n"
              + ";\n".join(f"Reset({c})" for c in ["txtFieldLabel", "txtFieldHelp", "ddFieldWhen", "ddFieldCond"])
              + ";\nClearCollect(colPickF, ForAll(Filter(Split(Coalesce(ThisItem.ConditionValue, \"\"), \";\"), "
              "!IsBlank(Trim(Value))), {Value: Trim(Value)}))")
fields_card = vbox("FormCard", [
    head("lblFormHead", f'"The " & Lower(Substitute({TAB}, "Cost Center", "cost centre")) & " request form asks for"'),
    list_gallery("galPFields", FIELD_ROWS, 40, [
        cell("lblPFName", 'ThisItem.DisplayLabel & If(ThisItem.Sensitive = "Yes", "  (restricted)", "")', "8",
             "Parent.TemplateWidth - 340", OnSelect="Select(Parent)"),
        cell("lblPFWhen", when_text('If(ThisItem.Required = "Conditional", ThisItem.ConditionField, "")',
                                    "ThisItem.ConditionValue"),
             "Parent.TemplateWidth - 330", "240", Size="10", Align="Align.Right",
             Color=f'If(ThisItem.Required = "Conditional", {AMBER}, {GREY})'),
        row_btn("btnPFEdit", '"Change"', OPEN_FIELD, 84),
    ]),
    note("lblFormNote", '"Change makes a field always asked or only asked for some requests, and edits its label '
                        'and help text. A field the form doesn\'t have yet needs an app change."'),
], visible=f'{ON_TYPE_TAB} && IsBlank(locPanel)')

STEP_ROWS = (f'Filter(RuleRows, Stage < 1.5 && (RequestType = {TAB} || RequestType = "Any") && '
             f'(ddPreviewBU.Selected.Code = "Any" || Entity = "Any" || Entity = ddPreviewBU.Selected.Code))')
PERSON = ('With({code: ddPreviewBU.Selected.Code, role: ThisItem.Role}, If(code = "Any", '
          'With({ps: Filter(RolesRows, Role = role)}, If(CountRows(ps) = 0, "nobody set up", CountRows(ps) = 1, '
          'First(ps).Name, "set per business")), Coalesce(LookUp(RolesRows, Role = role && Entity = code).Name, '
          'LookUp(RolesRows, Role = role && Entity = "Any").Name, "nobody set up, so MDM")))')
OPEN_STEP_ADD = ("UpdateContext({locPanel: \"step\", locStep: Blank()});\nClear(colPick);\n"
                 + ";\n".join(f"Reset({c})" for c in ["ddStepRole", "ddStepFor", "ddStepWhen", "ddStepField",
                                                       "txtStepRemind"]))
OPEN_STEP_EDIT = ("UpdateContext({locPanel: \"step\", locStep: LookUp(RoutingRules, Title = ThisItem.Rule)});\n"
                  + ";\n".join(f"Reset({c})" for c in ["ddStepRole", "ddStepFor", "ddStepWhen", "ddStepField",
                                                        "txtStepRemind"])
                  + ";\nClearCollect(colPick, ForAll(Filter(Split(Coalesce(ThisItem.ConditionValue, \"\"), \";\"), "
                  "!IsBlank(Trim(Value))), {Value: Trim(Value)}))")
STAGE2 = (f'Concat(Filter(RuleRows, Active && Stage >= 1.5 && (RequestType = {TAB} || RequestType = "Any")) As s, '
          's.Role & " (" & Coalesce(LookUp(RolesRows, Role = s.Role).Name, "nobody set up") & ")", ", ")')
chain_card = vbox("ChainCard", [
    row("rowChainHead", [
        head("lblChainHead", '"Then it\'s approved by"', FillPortions="1"),
        label("lblPreview", '"Show for"', FillPortions="0", Width="70", Height="34", Size="10", Color=GREY),
        ctl("ddPreviewBU", "Classic/DropDown@2.3.1", dict(DROPDOWN, Items="BusinessChoices", Default='"All businesses"',
                                                          FillPortions="0", Width="230", Height="34", Size="11")),
    ], 40, align="LayoutAlignItems.Center"),
    note("lblStage1", '"Step 1: everyone below at the same time"', height="22"),
    list_gallery("galPSteps", STEP_ROWS, 48, [
        cell("lblPSRole", f'ThisItem.Role & " (" & {PERSON} & ")" & If(ThisItem.Entity = "Any", "", "  -  " & '
                          'ThisItem.Entity & " only")', "8", "Parent.TemplateWidth - 420",
             Color=f"If(ThisItem.Active, RGBA(50, 49, 48, 1), {GREY})", OnSelect="Select(Parent)"),
        cell("lblPSWhen", f'If(!ThisItem.Active, "turned off", {when_text("ThisItem.ConditionField", "ThisItem.ConditionValue")})',
             "Parent.TemplateWidth - 410", "220", Size="10", Align="Align.Right",
             Color=f'If(!ThisItem.Active || IsBlank(ThisItem.ConditionField), {GREY}, {AMBER})'),
        row_btn("btnPSEdit", '"Change"', OPEN_STEP_EDIT, 180),
        row_btn("btnPSToggle", 'If(ThisItem.Active, "Turn off", "Turn on")',
                "IfError(Patch(RoutingRules, LookUp(RoutingRules, Title = ThisItem.Rule), {Active: !ThisItem.Active}), "
                "Notify(\"Couldn't change it: \" & FirstError.Message, NotificationType.Error))", 96, width=88),
    ]),
    note("lblStage2", f'"Step 2: " & {STAGE2} & ", the final check. Then the SAP import file is made."', height="40"),
    row("rowAddStep", [label("lblAddStepGap", '""', FillPortions="1", Height="36"),
                       btn("btnAddStep", '"Add an approval step"', OPEN_STEP_ADD, primary=True, width=200)],
        44, align="LayoutAlignItems.Center"),
], visible=f'{ON_TYPE_TAB} && IsBlank(locPanel)')

# ---- panel: add or change an approval step
ONLY = 'ddStepWhen.Selected.Value <> "Every request"'
STEP_OPTS = options("ddStepField.Selected.F")
STEP_PICKED = picked("colPick", STEP_OPTS)
STEP_SENTENCE = (f'Coalesce(ddStepRole.Selected.Value, "(who?)") & " approves " & Lower(Substitute(Coalesce(locStep.RequestType, {TAB}), "Cost Center", "cost centre")) & '
                 f'" requests for " & If(Coalesce(ddStepFor.Selected.Code, "Any") = "Any", "all businesses", ddStepFor.Selected.Code) & ", " & If({ONLY}, '
                 f'{readback("ddStepField.Selected.F", STEP_PICKED)}, "every time") & "."')
SAVE_STEP = f"""With(
    {{only: {ONLY}, role: ddStepRole.Selected.Value, code: Coalesce(ddStepFor.Selected.Code, "Any"),
     days: Value(txtStepRemind.Text)}},
    If(
        IsBlank(role), Notify("Choose who approves.", NotificationType.Warning),
        only && IsBlank(ddStepField.Selected.F), Notify("Choose which field the step depends on.", NotificationType.Warning),
        only && CountRows({STEP_PICKED}) = 0, Notify("Tick at least one value.", NotificationType.Warning),
        IfError(
            Patch(RoutingRules, If(IsBlank(locStep), Defaults(RoutingRules), locStep), {{
                Title: If(IsBlank(locStep), {NEXT_RULE}, locStep.Title),
                RequestType: If(IsBlank(locStep), {TAB}, locStep.RequestType),
                Entity: code, ApproverRole: role,
                ConditionField: If(only, ddStepField.Selected.F, ""),
                ConditionValue: If(only, Concat({STEP_PICKED}, Value, ";"), ""),
                Stage: If(IsBlank(locStep), 1, locStep.Stage), SLADays: Coalesce(days, 2),
                EscalateAfterDays: If(IsBlank(locStep), 4, locStep.EscalateAfterDays),
                Active: If(IsBlank(locStep), true, locStep.Active)
            }});
            Notify("Saved. It applies from the next request.", NotificationType.Success);
            {CLOSE},
            Notify("Couldn't save: " & FirstError.Message, NotificationType.Error)
        )
    )
)"""
STEP_GAP = ('With({role: ddStepRole.Selected.Value, code: Coalesce(ddStepFor.Selected.Code, "Any")}, '
            'If(IsBlank(role), "", code = "Any", If(CountRows(Filter(RolesRows, Role = role)) = 0, '
            '"Nobody is set up as " & role & " yet, so these approvals go to the MDM team. Add the person under '
            'Businesses and people.", ""), IsBlank(LookUp(RolesRows, Role = role && (Entity = code || Entity = "Any"))), '
            '"Nobody is set up as " & role & " for " & code & " yet, so these approvals go to the MDM team.", ""))')
step_panel = vbox("StepPanel", [
    head("lblStepHead", f'If(IsBlank(locStep), "Add an approval step to " & Lower(Substitute({TAB}, "Cost Center", "cost centre")) & " requests", '
                        '"Change approval step " & locStep.Title)', size="14"),
    field("fldStepRole", '"Who approves"', dd("ddStepRole", "ApproverRoles",
                                                'If(IsBlank(locStep), "", locStep.ApproverRole)')),
    note("lblStepRoleHelp", '"Not in the list? Add the person under Businesses and people first."', height="22"),
    field("fldStepFor", '"For"', dd("ddStepFor", "BusinessChoices",
                                    'If(IsBlank(locStep) || locStep.Entity = "Any", "All businesses", '
                                    'LookUp(BusinessUnits, Title = locStep.Entity).BusinessUnitName)', empty=False)),
    field("fldStepWhen", '"When"', dd("ddStepWhen", fx_list(["Every request", "Only when a field has a value"]),
                                      'If(IsBlank(locStep.ConditionField), "Every request", "Only when a field has a value")',
                                      empty=False)),
    field("fldStepField", '"Field"', dd("ddStepField",
                                        f"ForAll(Filter(TypeFields, Type = Coalesce(locStep.RequestType, {TAB})), {{Value: L, F: F}})",
                                        "LookUp(TypeFields, F = locStep.ConditionField).L"),
          visible=ONLY),
    note("lblStepValsHelp", '"Tick every value it applies to:"', height="22", Visible=ONLY),
    chips("galStepVals", STEP_OPTS, "colPick", visible=ONLY),
    field("fldStepRemind", '"Remind after (days)"', tin("txtStepRemind", 'If(IsBlank(locStep), "2", Text(locStep.SLADays))',
                                                        Format="TextFormat.Number")),
    label("lblStepSentence", STEP_SENTENCE, Size="12", Wrap="true", AutoHeight="true", FillPortions="0",
          Height="30", PaddingLeft="8", Fill="RGBA(239, 246, 252, 1)", FontWeight="FontWeight.Semibold"),
    note("lblStepGap", STEP_GAP, color=AMBER, Visible=f"!IsBlank({STEP_GAP})"),
    buttons("StepBtns", CLOSE, SAVE_STEP, 'If(IsBlank(locStep), "Add step", "Save changes")'),
], visible='locPanel = "step"')

# ---- panel: change a form field
FONLY = 'ddFieldWhen.Selected.Value <> "Always asked"'
FIELD_OPTS = options("ddFieldCond.Selected.F", not_sure=True)
FIELD_PICKED = picked("colPickF", FIELD_OPTS)
FIELD_SENTENCE = (f'"The form asks for " & Coalesce(Trim(txtFieldLabel.Text), "this field") & " " & If({FONLY}, '
                  f'{readback("ddFieldCond.Selected.F", FIELD_PICKED)}, "on every " & Lower(Substitute(locField.RequestType, "Cost Center", "cost centre")) & " request") & "."')
SAVE_FIELD = f"""With(
    {{only: {FONLY}}},
    If(
        IsBlank(Trim(txtFieldLabel.Text)), Notify("Enter a label.", NotificationType.Warning),
        only && IsBlank(ddFieldCond.Selected.F), Notify("Choose which field it depends on.", NotificationType.Warning),
        only && CountRows({FIELD_PICKED}) = 0, Notify("Tick at least one value.", NotificationType.Warning),
        IfError(
            Patch(RequiredFields, locField, {{
                DisplayLabel: Trim(txtFieldLabel.Text), HelpText: Trim(txtFieldHelp.Text),
                Required: If(only, "Conditional", "Always"),
                ConditionField: If(only, ddFieldCond.Selected.F, ""),
                ConditionValue: If(only, Concat({FIELD_PICKED}, Value, ";"), "")
            }});
            Notify("Saved. The form shows it from now on.", NotificationType.Success);
            {CLOSE},
            Notify("Couldn't save: " & FirstError.Message, NotificationType.Error)
        )
    )
)"""
field_panel = vbox("FieldPanel", [
    head("lblFieldHead", '"Change the field: " & locField.DisplayLabel', size="14"),
    field("fldFieldLabel", '"Label"', tin("txtFieldLabel", "locField.DisplayLabel")),
    field("fldFieldHelp", '"Help text"', tin("txtFieldHelp", "locField.HelpText", "Shown under the field")),
    field("fldFieldWhen", '"Asked"', dd("ddFieldWhen", fx_list(["Always asked", "Only when another field has a value"]),
                                        'If(locField.Required = "Conditional", "Only when another field has a value", '
                                        '"Always asked")', empty=False)),
    field("fldFieldCond", '"Field"', dd("ddFieldCond",
                                        "ForAll(Filter(TypeFields, Type = locField.RequestType && F <> locField.FieldName), "
                                        "{Value: L, F: F})", "LookUp(TypeFields, F = locField.ConditionField).L",
                                        ), visible=FONLY),
    note("lblFieldValsHelp", '"Tick every value it applies to:"', height="22", Visible=FONLY),
    chips("galFieldVals", FIELD_OPTS, "colPickF", visible=FONLY),
    label("lblFieldSentence", FIELD_SENTENCE, Size="12", Wrap="true", AutoHeight="true", FillPortions="0",
          Height="30", PaddingLeft="8", Fill="RGBA(239, 246, 252, 1)", FontWeight="FontWeight.Semibold"),
    note("lblFieldNote", '"A field that is shown is always required. Format checks are under Advanced > Form fields."',
         height="22"),
    buttons("FieldBtns", CLOSE, SAVE_FIELD),
], visible='locPanel = "field"')

# ---- Businesses and people
BIZ = "galBiz.Selected.Title"
PEOPLE_ROWS = f'Sort(Filter(RolesRows, Role <> "Requestor" && (Entity = {BIZ} || Entity = "Any")), Role)'
MISSING = (f'Concat(Filter(Distinct(Filter(RuleRows As x, x.Active && (x.Entity = {BIZ} || x.Entity = "Any")), Role) As r, '
           f'!("@" in LookUp(RolesRows, Role = r.Value && (Entity = {BIZ} || Entity = "Any")).Email)), Value, ", ")')
PERSON_INPUTS = ["ddPersonRole", "txtPersonNewRole", "ddPersonScope", "txtPersonName", "txtPersonEmail",
                 "txtPersonEscalate", "ddPersonTZ"]
OPEN_PERSON_ADD = ('UpdateContext({locPanel: "person", locPerson: Blank()});\n'
                   + ";\n".join(f"Reset({c})" for c in PERSON_INPUTS))
OPEN_PERSON_EDIT = ('UpdateContext({locPanel: "person", locPerson: LookUp(Roles, ID = ThisItem.ID)});\n'
                    + ";\n".join(f"Reset({c})" for c in PERSON_INPUTS))
BU_INPUTS = ["txtNewBUCode", "txtNewBUName", "txtNewBUHeadName", "txtNewBUHeadEmail", "txtNewBUEscalate",
             "ddNewBUTimeZone"]
OPEN_BU = 'UpdateContext({locPanel: "bu"});\nClear(colPickBU);\n' + ";\n".join(f"Reset({c})" for c in BU_INPUTS)
people_card = vbox("PeopleCard", [
    row("rowBizHead", [head("lblBizHead", '"Businesses"', FillPortions="1"),
                       btn("btnAddBU", '"Add a business unit"', OPEN_BU, primary=True, width=190)],
        40, align="LayoutAlignItems.Center"),
    list_gallery("galBiz", "Sort(BusinessUnits, Title)", 44, [
        cell("lblBizName", 'ThisItem.Title & "  -  " & ThisItem.BusinessUnitName', "8", "Parent.TemplateWidth - 330",
             FontWeight="If(ThisItem.IsSelected, FontWeight.Semibold, FontWeight.Normal)",
             Color=f"If(ThisItem.Active, RGBA(50, 49, 48, 1), {GREY})", OnSelect="Select(Parent)"),
        cell("lblBizProducts", 'If(ThisItem.Active, "Product lines " & Coalesce(ThisItem.Products, "none"), "turned off")',
             "Parent.TemplateWidth - 320", "210", Size="10", Align="Align.Right", Color=GREY, OnSelect="Select(Parent)"),
        row_btn("btnBizToggle", 'If(ThisItem.Active, "Turn off", "Turn on")',
                "IfError(Patch(BusinessUnits, ThisItem, {Active: !ThisItem.Active}), "
                "Notify(\"Couldn't change it: \" & FirstError.Message, NotificationType.Error))", 96, width=88),
    ]),
    note("lblBizHelp", '"Select a business to see who approves for it. A business that is turned off disappears '
                       'from the request form; its past requests are kept."', height="30"),
    row("rowPeopleHead", [head("lblPeopleHead", '"Who approves for " & ' + BIZ, FillPortions="1"),
                          btn("btnAddPerson", '"Add a person"', OPEN_PERSON_ADD, width=150)],
        40, align="LayoutAlignItems.Center"),
    list_gallery("galPeople", PEOPLE_ROWS, 48, [
        cell("lblPersonRole", 'ThisItem.Role & ": " & ThisItem.Name', "8", "Parent.TemplateWidth - 300",
             FontWeight="FontWeight.Semibold", Height="24", Y="4"),
        cell("lblPersonEmail", 'ThisItem.Email & If(IsBlank(ThisItem.EscalateTo), "", "  |  escalates to " & ThisItem.EscalateTo)',
             "8", "Parent.TemplateWidth - 300", Height="20", Y="26", Size="10", Color=GREY, Wrap="false"),
        cell("lblPersonScope", 'If(ThisItem.Entity = "Any", "all businesses", "this business only")',
             "Parent.TemplateWidth - 280", "180", Size="10", Align="Align.Right", Color=GREY),
        row_btn("btnPersonEdit", '"Change"', OPEN_PERSON_EDIT, 92),
    ]),
    note("lblMissing", f'"Nobody set up for " & {BIZ} & " as: " & {MISSING} & ". Those approvals go to the MDM team '
                       f'until you add someone."', color="RGBA(164, 38, 44, 1)", Visible=f"!IsBlank({MISSING})"),
], visible=f'{TAB} = "People" && IsBlank(locPanel)')

PERSON_ROLE = 'Coalesce(Trim(txtPersonNewRole.Text), ddPersonRole.Selected.Value)'
PERSON_ENTITY = f'If(!IsBlank(locPerson), locPerson.Entity, ddPersonScope.Selected.Value = "All businesses", "Any", {BIZ})'
SAVE_PERSON = f"""With(
    {{role: If(IsBlank(locPerson), {PERSON_ROLE}, locPerson.Role), entity: {PERSON_ENTITY},
     email: Lower(Trim(txtPersonEmail.Text)), esc: Lower(Trim(txtPersonEscalate.Text))}},
    If(
        IsBlank(role), Notify("Choose or type the role.", NotificationType.Warning),
        IsBlank(Trim(txtPersonName.Text)), Notify("Enter the person's name.", NotificationType.Warning),
        !IsMatch(email, Match.Email) || (!IsBlank(esc) && !IsMatch(esc, Match.Email)),
            Notify("Check the email addresses.", NotificationType.Warning),
        IsBlank(locPerson) && !IsBlank(LookUp(RolesRows, Role = role && Entity = entity)),
            Notify("Someone is already set up as " & role & " for " & If(entity = "Any", "all businesses", entity) &
                   ". Change that person instead.", NotificationType.Warning),
        IfError(
            Patch(Roles, If(IsBlank(locPerson), Defaults(Roles), locPerson), {{
                Title: role & " - " & entity, Role: role, Entity: entity, PersonName: Trim(txtPersonName.Text),
                PersonEmail: email, EscalateTo: esc, TimeZone: ddPersonTZ.Selected.Value
            }});
            Notify("Saved. New approvals go to " & Trim(txtPersonName.Text) & ".", NotificationType.Success);
            {CLOSE},
            Notify("Couldn't save: " & FirstError.Message, NotificationType.Error)
        )
    )
)"""
person_panel = vbox("PersonPanel", [
    head("lblPersonHead", f'If(IsBlank(locPerson), "Add a person for " & {BIZ}, "Change " & locPerson.Role & '
                          '" (" & If(locPerson.Entity = "Any", "all businesses", locPerson.Entity) & ")")', size="14"),
    field("fldPersonRole", '"Role"', dd("ddPersonRole", "Sort(Distinct(RuleRows, Role), Value)"),
          visible="IsBlank(locPerson)"),
    field("fldPersonNewRole", '"or a new role"', tin("txtPersonNewRole", hint="e.g. BPOM Specialist"),
          visible="IsBlank(locPerson)"),
    field("fldPersonScope", '"Approves for"', dd("ddPersonScope",
                                                 f'["This business only (" & {BIZ} & ")", "All businesses"]',
                                                 f'"This business only (" & {BIZ} & ")"', empty=False),
          visible="IsBlank(locPerson)"),
    field("fldPersonName", '"Name"', tin("txtPersonName", "locPerson.PersonName")),
    field("fldPersonEmail", '"Email"', tin("txtPersonEmail", "locPerson.PersonEmail", "their Lives Group email")),
    field("fldPersonEscalate", '"Escalate to"', tin("txtPersonEscalate", "locPerson.EscalateTo",
                                                    "their manager's email (optional)")),
    field("fldPersonTZ", '"Time zone"', dd("ddPersonTZ", fx_list(TIME_ZONES),
                                          'Coalesce(locPerson.TimeZone, "Asia/Singapore")', empty=False)),
    note("lblPersonNote", 'If(!IsBlank(locPerson) && locPerson.Entity = "Any", "This person approves for every '
                          'business. To use someone else for one business, add a person for that business instead.", '
                          '"Reminders go out at 9 AM in their time zone. Escalations go to the escalation contact.")'),
    buttons("PersonBtns", CLOSE, SAVE_PERSON),
], visible='locPanel = "person"')

SAVE_BU = """With(
    {code: Upper(Trim(txtNewBUCode.Text)), email: Lower(Trim(txtNewBUHeadEmail.Text)),
     esc: Lower(Trim(txtNewBUEscalate.Text)), head: Trim(txtNewBUHeadName.Text)},
    If(
        !IsMatch(code, "^[A-Z0-9]{2,6}$"), Notify("Enter a code of 2 to 6 letters or digits, e.g. LGD.", NotificationType.Warning),
        IsBlank(Trim(txtNewBUName.Text)) || IsBlank(head), Notify("Fill in the name and the BU Head.", NotificationType.Warning),
        !IsMatch(email, Match.Email) || (!IsBlank(esc) && !IsMatch(esc, Match.Email)),
            Notify("Check the email addresses.", NotificationType.Warning),
        !IsBlank(LookUp(BusinessUnits, Title = code)), Notify(code & " already exists.", NotificationType.Warning),
        IfError(
            Patch(BusinessUnits, Defaults(BusinessUnits),
                {Title: code, BusinessUnitName: Trim(txtNewBUName.Text), Products: Concat(colPickBU, Value, ", "),
                 Active: true});
            Patch(Roles, Defaults(Roles),
                {Title: "BU Head - " & code, Role: "BU Head", Entity: code, PersonName: head, PersonEmail: email,
                 EscalateTo: esc, TimeZone: ddNewBUTimeZone.Selected.Value});
            Notify(code & " added. It's on the request form now, and its BU Head approvals go to " & head & ".",
                   NotificationType.Success);
            UpdateContext({locPanel: ""}),
            Notify("Couldn't add the business unit: " & FirstError.Message, NotificationType.Error)
        )
    )
)"""
SHARED_STEPS = ('Concat(Distinct(Filter(RuleRows, Active && Entity = "Any" && Role <> "BU Head"), Role) As r, '
                'r.Value & " (" & Coalesce(LookUp(RolesRows, Role = r.Value && Entity = "Any").Name, "nobody set up") & ")", ", ")')
bu_panel = vbox("BUPanel", [
    head("lblBUHead", '"Add a business unit"', size="14"),
    field("fldNewBUCode", '"Code"', tin("txtNewBUCode", hint="e.g. LGD")),
    field("fldNewBUName", '"Name"', tin("txtNewBUName", hint="e.g. LGD (molecular diagnostics)")),
    note("lblNewBUProd", '"Product lines it sells:"', height="22"),
    chips("galNewBUProd", 'ForAll(Sort(Filter(ChoiceRows, List = "ProductFamily" && Active), Order), {Value: Value})',
          "colPickBU"),
    field("fldNewBUHeadName", '"BU Head"', tin("txtNewBUHeadName", hint="Full name")),
    field("fldNewBUHeadEmail", '"BU Head email"', tin("txtNewBUHeadEmail", hint="their Lives Group email")),
    field("fldNewBUEscalate", '"Escalate to"', tin("txtNewBUEscalate", hint="their manager's email (optional)")),
    field("fldNewBUTimeZone", '"Time zone"', dd("ddNewBUTimeZone", fx_list(TIME_ZONES), '"Asia/Singapore"', empty=False)),
    label("lblBUSentence", f'"Its requests go to its BU Head, plus the checks every business shares: " & {SHARED_STEPS} & '
                           '". It appears on the request form straight away."',
          Size="11", Wrap="true", AutoHeight="true", FillPortions="0", Height="30", PaddingLeft="8",
          Fill="RGBA(239, 246, 252, 1)"),
    buttons("BUBtns", CLOSE, SAVE_BU, '"Add business unit"'),
], visible='locPanel = "bu"')

# ---- Product lines
LINE_ROWS = 'Sort(Filter(ChoiceRows, List = "ProductFamily"), Order)'
IN_LIST = 'Lower(code) in Split(Lower(Substitute(Coalesce({v}, ""), " ", "")), ";")'
LINE_INFO = ('With({code: ThisItem.Value}, '
             '"Sold by " & Coalesce(Concat(Filter(BusinessUnits As b, Upper(code) in Split(Upper(Substitute(Coalesce(b.Products, ""), " ", "")), ",")), Title, ", "), "no business yet") & '
             '"  |  extra fields: " & Coalesce(Concat(Filter(FieldRules As r, r.RequestType = "Item" && r.ConditionField = "ProductFamily" && '
             + IN_LIST.format(v="r.ConditionValue") + '), DisplayLabel, ", "), "none") & '
             '"  |  extra approvals: " & Coalesce(Concat(Filter(RuleRows As s, s.Active && s.ConditionField = "ProductFamily" && '
             + IN_LIST.format(v="s.ConditionValue") + '), Role, ", "), "none"))')
LINE_INPUTS = ["txtLineCode", "txtLineName", "ddLineBU", "ddLineRole"]
OPEN_LINE = 'UpdateContext({locPanel: "line"});\nClear(colLineFields);\n' + ";\n".join(f"Reset({c})" for c in LINE_INPUTS)
lines_card = vbox("LinesCard", [
    row("rowLinesHead", [head("lblLinesHead", '"Product lines"', FillPortions="1"),
                         btn("btnAddLine", '"Add a product line"', OPEN_LINE, primary=True, width=180)],
        40, align="LayoutAlignItems.Center"),
    list_gallery("galLines", LINE_ROWS, 56, [
        cell("lblLineName", 'ThisItem.Value & "  -  " & Coalesce(ThisItem.Details, "(no name)") & If(ThisItem.Active, "", "  (turned off)")',
             "8", "Parent.TemplateWidth - 120", Height="24", Y="4", FontWeight="FontWeight.Semibold",
             Color=f"If(ThisItem.Active, RGBA(50, 49, 48, 1), {GREY})"),
        cell("lblLineInfo", LINE_INFO, "8", "Parent.TemplateWidth - 120", Height="24", Y="28", Size="10", Color=GREY,
             Wrap="false"),
        row_btn("btnLineToggle", 'If(ThisItem.Active, "Turn off", "Turn on")',
                'IfError(Patch(ChoiceOptions, LookUp(ChoiceOptions, ListName = "ProductFamily" && Title = ThisItem.Value), '
                '{Active: !ThisItem.Active}), Notify("Couldn\'t change it: " & FirstError.Message, NotificationType.Error))',
                100, width=88),
    ]),
    note("lblLinesNote", '"A product line that is turned off disappears from the item form; its items and requests are '
                         'kept. Countries, segments, units and departments are under Advanced > Dropdown options."'),
], visible=f'{TAB} = "Lines" && IsBlank(locPanel)')

LINE_FIELD_ROWS = 'Filter(FieldRules, RequestType = "Item" && Required = "Conditional" && ConditionField = "ProductFamily")'
LINE_SENTENCE = ('"Item requests can choose " & Coalesce(Upper(Trim(txtLineCode.Text)), "the new line") & '
                 'If(IsBlank(Trim(txtLineName.Text)), "", " (" & Trim(txtLineName.Text) & ")") & ". " & '
                 'If(CountRows(colLineFields) = 0, "No extra fields", "They also ask for " & Concat(colLineFields, DisplayLabel, ", ")) & '
                 'If(IsBlank(ddLineRole.Selected.Value), ", and the usual approvals.", ", and " & ddLineRole.Selected.Value & '
                 '" approves them too.")')
SAVE_LINE = f"""With(
    {{code: Upper(Trim(txtLineCode.Text)), name: Trim(txtLineName.Text)}},
    If(
        !IsMatch(code, "^[A-Z0-9]{{1,5}}$"), Notify("Enter a code of 1 to 5 letters or digits, e.g. D.", NotificationType.Warning),
        IsBlank(name), Notify("Enter a name for the product line.", NotificationType.Warning),
        !IsBlank(LookUp(ChoiceRows, List = "ProductFamily" && Upper(Value) = code)),
            Notify(code & " already exists. Turn it on under Product lines instead.", NotificationType.Warning),
        IfError(
            Patch(ChoiceOptions, Defaults(ChoiceOptions), {{Title: code, ListName: "ProductFamily", Details: name,
                SortOrder: Coalesce(Max(Filter(ChoiceRows, List = "ProductFamily"), Order), 0) + 10, Active: true}});
            ForAll(colLineFields As c,
                With({{r: LookUp(RequiredFields, Title = c.Title)}},
                    Patch(RequiredFields, r, {{ConditionValue: If(IsBlank(r.ConditionValue), code, r.ConditionValue & ";" & code)}})));
            If(!IsBlank(ddLineBU.Selected.Code),
                With({{b: LookUp(BusinessUnits, Title = ddLineBU.Selected.Code)}},
                    Patch(BusinessUnits, b, {{Products: If(IsBlank(Trim(b.Products)), code, b.Products & ", " & code)}})));
            If(!IsBlank(ddLineRole.Selected.Value),
                Patch(RoutingRules, Defaults(RoutingRules), {{Title: {NEXT_RULE}, RequestType: "Item", Entity: "Any",
                    ConditionField: "ProductFamily", ConditionValue: code, ApproverRole: ddLineRole.Selected.Value,
                    Stage: 1, SLADays: 2, EscalateAfterDays: 4, Active: true}}));
            Notify(code & " added. It's on the item form now.", NotificationType.Success);
            {CLOSE},
            Notify("Couldn't add the product line: " & FirstError.Message, NotificationType.Error)
        )
    )
)"""
line_panel = vbox("LinePanel", [
    head("lblLineHead", '"Add a product line"', size="14"),
    field("fldLineCode", '"Code"', tin("txtLineCode", hint="e.g. D (used in item codes, e.g. D-5012)")),
    field("fldLineName", '"Name"', tin("txtLineName", hint="e.g. Molecular reagents")),
    field("fldLineBU", '"Sold by"', dd("ddLineBU", 'ForAll(Sort(Filter(BusinessUnits, Active = true), Title), '
                                                  '{Value: BusinessUnitName, Code: Title})')),
    note("lblLineFieldsHelp", '"Every item already asks for " & Concat(Filter(FieldRules, RequestType = "Item" && '
                              'Required <> "Conditional"), DisplayLabel, ", ") & ". Tick any of these it also needs:"',
         height="44"),
    chips("galLineFields", LINE_FIELD_ROWS, "colLineFields", key="Title", text="ThisItem.DisplayLabel", per_row=3,
          record="{Title: ThisItem.Title, DisplayLabel: ThisItem.DisplayLabel}"),
    field("fldLineRole", '"Extra approver"', dd("ddLineRole", "ApproverRoles")),
    note("lblLineRoleHelp", '"Optional. Leave blank if it needs only the usual approvals. Not in the list? Add the '
                            'person under Businesses and people first."', height="30"),
    label("lblLineSentence", LINE_SENTENCE, Size="12", Wrap="true", AutoHeight="true", FillPortions="0",
          Height="30", PaddingLeft="8", Fill="RGBA(239, 246, 252, 1)", FontWeight="FontWeight.Semibold"),
    note("lblLineNewField", '"Needs a field the form doesn\'t have yet (e.g. calibration interval)? That\'s an app '
                            'change: ask the OneRecord team."', height="30"),
    buttons("LineBtns", CLOSE, SAVE_LINE, '"Add product line"'),
], visible='locPanel = "line"')

# ---- Advanced: the raw list editor (every column of every rule list)
advanced_card = vbox("AdvancedCard", [
    note("lblAdvHelp", '"Every rule list, column by column. Use the other tabs for everyday changes; this is for '
                       'anything they don\'t cover (format checks, known names, dropdown options)."', height="30"),
    row("rowPickList", [
        label("lblPickList", '"Show"', FillPortions="0", Width="50", Height="36", Size="11", PaddingLeft="0"),
        ctl("ddRuleList", "Classic/DropDown@2.3.1", dict(
            DROPDOWN, Items=fx_list([g[1] for g in GRIDS]), Default=f'"{GRIDS[0][1]}"', FillPortions="0",
            Width="260", Height="36", Size="11")),
        label("lblPickNote", '"Changes apply to the next request. SharePoint keeps every earlier version of '
                             'each row."', FillPortions="1", Height="36", Size="10", Color=GREY, Wrap="true"),
    ], 44, align="LayoutAlignItems.Center"),
] + [grid(*g) for g in GRIDS], visible=f'{TAB} = "Advanced" && IsBlank(locPanel)')

admin_body = ctl("AdminBody", "GroupContainer@1.5.0", {
    "Fill": "RGBA(245, 245, 245, 1)", "FillPortions": "1", "Visible": "CanSeeRules", "LayoutMinHeight": "16",
    "LayoutMinWidth": "16", "LayoutDirection": "LayoutDirection.Vertical",
    "LayoutAlignItems": "LayoutAlignItems.Stretch", "LayoutOverflowY": "LayoutOverflow.Scroll", "LayoutGap": "12",
    "DropShadow": "DropShadow.None"},
    [tab_bar, check_banner, fields_card, chain_card, people_card, lines_card, advanced_card,
     step_panel, field_panel, person_panel, bu_panel, line_panel], variant="AutoLayout")

admin_screen = ctl("ScreenContainer3", "GroupContainer@1.5.0", {
    "Fill": "RGBA(245, 245, 245, 1)", "Height": "Parent.Height", "Width": "Parent.Width",
    "LayoutAlignItems": "LayoutAlignItems.Stretch", "LayoutDirection": "LayoutDirection.Vertical",
    "LayoutGap": "16", "PaddingBottom": "16", "PaddingLeft": "16", "PaddingRight": "16", "PaddingTop": "16",
}, [
    header(3, "OneRecord | Rules", "Rules"),
    label("lblNotMDM", 'If(CanSeeRules, "View only: the MDM team changes the rules.", '
                       '"Only the MDM team can change the rules.")', Visible="!IsMDM", FillPortions="0", Height="40",
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
