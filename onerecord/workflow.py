"""
The request workflow: the Power App's form logic and the Power Automate flows, ported to Python and backed by one
shared SQLite file. It reads the same rule lists the Microsoft 365 build uses (sharepoint/*.csv), so a rule change
behaves the same way in both. Change both together (powerapps/gen_form.py, powerautomate/build_route_approve.py).

  check_form()     = the form: visible fields, format checks, duplicate check, who will approve, can submit
  submit()         = Submit + flow "Route and approve": stage-1 approvals in parallel, routing gaps to MDM
  resubmit()       = Edit and resubmit after "Request changes": only the approver who asked sees it again
  decide()         = an approval card's Approve / Request changes / Reject
  mark_created()   = MDM imported the DTW file into SAP B1
  run_reminders()  = flow "Reminders and escalation" (a demo clock fast-forwards the days)
"""
import json
import re
import sqlite3
from datetime import datetime, timedelta

import pandas as pd

from .config import ROOT, SHAREPOINT
from .livecheck import EXPAND, LEGAL, PUNCT, THRESHOLD, id_key, match_key, similarity

DB = ROOT / ".state" / "workflow.sqlite"
RULE_TABLES = ["BusinessUnits", "RoutingRules", "RequiredFields", "Roles", "Aliases", "ChoiceOptions"]
MASTER_TABLES = ["CustomerMaster", "ItemMaster", "VendorMaster", "CostCentres"]
TYPES = ["Customer", "Item", "Vendor", "Cost Center"]
OPEN = ["Pending approval", "Changes requested", "Resubmitted"]
PAYMENT_TERMS = ["30 days", "45 days", "60 days", "90 days", "Advance"]  # fixed: Finance owns them
ROUTE_FIELDS = ["Country", "ProductFamily", "IsRegulated", "SuppliesRegulatedGoods", "Segment", "UnitOfMeasure",
                "Department"]
NAME_FIELD = {"Customer": "CustomerName", "Item": "ItemDescription", "Vendor": "VendorName",
              "Cost Center": "CostCenterName"}
ID_FIELD = {"Customer": ("RegistrationNo", "registration no."), "Item": ("ManufacturerPartNo", "manufacturer part no."),
            "Vendor": ("TaxID", "tax ID")}
ESCALATE_AFTER_DAYS = 4
CLOSE_AFTER_DAYS = 14  # a request sent back for changes and not resubmitted is closed

# ---- format checks (the form's FieldChecks)
FREE_TEXT = ["CustomerName", "RegistrationNo", "BillingAddress", "ContactEmail", "ItemDescription",
             "ManufacturerPartNo", "HSCode", "RegulatoryLicenceNo", "VendorName", "Country", "TaxID", "ISO13485CertNo",
             "BankName", "BankAccount", "CostCenterName", "Owner"]
NUMBERS = ["CreditLimit", "ShelfLifeMonths", "BudgetYear"]
DEFAULT_CHECKS = {"CustomerName": "Text", "RegistrationNo": "RegNo", "BillingAddress": "Text", "ContactEmail": "Email",
                  "ItemDescription": "Text", "ManufacturerPartNo": "PartNo", "HSCode": "HSCode",
                  "RegulatoryLicenceNo": "LicenceNo", "ShelfLifeMonths": "Months", "VendorName": "Text",
                  "TaxID": "TaxID", "ISO13485CertNo": "LicenceNo", "BankName": "Text", "BankAccount": "BankAccount",
                  "CostCenterName": "Text", "Owner": "Text", "BudgetYear": "Year"}
PLACEHOLDERS = {"na", "nil", "none", "null", "tbc", "tba", "tbd", "x", "xx", "xxx", "xxxx", "unknown", "test", "dummy",
                "pending", "later", "asap", "idk", "same", "sameasabove", "asabove", "abc", "asdf", "qwerty", "123",
                "1234", "12345", "0", "00", "000"}
REG_NO = {
    "SG": (r"^(?:\d{8}[A-Z]|\d{9}[A-Z]|[TSR]\d{2}[A-Z]{2}\d{4}[A-Z])$", "doesn't look like a Singapore UEN (e.g. 200288778W)"),
    "MY": (r"^(?:\d{12}|\d{14}|\d{6,7}[A-Z])$", "doesn't look like an SSM registration no. (12 digits, e.g. 201901000005)"),
    "TH": (r"^\d{13}$", "should be the 13-digit Thai tax ID"),
    "ID": (r"^\d{15,16}$", "should be the 15 or 16 digit NPWP (e.g. 01.234.567.8-901.000)"),
    "VN": (r"^(?:\d{10}|\d{13})$", "should be the 10-digit tax code (MST), or 13 digits for a branch"),
}


# --------------------------------------------------------------------------- storage
def connect():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB, timeout=15, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def reset(seed_demo=True):
    """Fresh state: rule and master lists from the SharePoint CSVs, no requests, then the demo requests."""
    con = connect()
    # dropped in place, not deleted, so other sessions' open connections see the fresh data
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name<>'sqlite_sequence'").fetchall():
        con.execute(f'DROP TABLE "{name}"')
    con.commit()
    con.executescript("""
    CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE requests (id TEXT PRIMARY KEY, type TEXT, entity TEXT, requestor TEXT, status TEXT, stage TEXT,
        submitted_at TEXT, completed_at TEXT, data TEXT, dup_status TEXT, dup_record TEXT, dup_reason TEXT,
        sap_code TEXT, change_note TEXT);
    CREATE TABLE sensitive (request_id TEXT PRIMARY KEY, data TEXT);
    CREATE TABLE approvals (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, role TEXT, person TEXT,
        queue TEXT, stage INTEGER, round INTEGER, status TEXT, assigned_at TEXT, decided_at TEXT, decided_by TEXT,
        comment TEXT, reminded_at TEXT, escalated_at TEXT, escalated_queue TEXT, escalated_person TEXT);
    CREATE TABLE log (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, ts TEXT, actor TEXT, role TEXT,
        action TEXT, detail TEXT);
    CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, to_role TEXT, to_name TEXT,
        request_id TEXT, text TEXT);
    CREATE TABLE sap_files (request_id TEXT PRIMARY KEY, filename TEXT, content TEXT, created_at TEXT);
    """)
    con.execute("INSERT INTO settings VALUES ('clock_offset_days', '0')")
    for t in RULE_TABLES + MASTER_TABLES:
        pd.read_csv(SHAREPOINT / f"{t}.csv", dtype=str).fillna("").to_sql(t, con, index=False)
    con.commit()
    if seed_demo:
        _seed(con)
    return con


def ensure():
    if not DB.exists():
        reset().close()
    con = connect()
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='messages'").fetchone():  # older demo file
        con.close()
        reset().close()
        con = connect()
    return con


def now(con) -> datetime:
    off = float(con.execute("SELECT value FROM settings WHERE key='clock_offset_days'").fetchone()[0])
    return datetime.now().replace(second=0, microsecond=0) + timedelta(days=off)


def advance_clock(con, days: float) -> list:
    off = float(con.execute("SELECT value FROM settings WHERE key='clock_offset_days'").fetchone()[0]) + days
    con.execute("UPDATE settings SET value=? WHERE key='clock_offset_days'", (str(off),))
    con.commit()
    return run_reminders(con)


def query(con, sql, params=()) -> pd.DataFrame:
    df = pd.read_sql(sql, con, params=params)
    obj = df.select_dtypes(exclude="number").columns
    df[obj] = df[obj].fillna("")
    return df


def table(con, name) -> pd.DataFrame:
    return query(con, f"SELECT * FROM {name}")


def save_table(con, name, df: pd.DataFrame, actor):
    """MDM edits a rule list (the Rules screen's Advanced tab). Logged like any change."""
    df.fillna("").astype(str).to_sql(name, con, index=False, if_exists="replace")
    _log(con, "", actor, "MDM Analyst", "Rule list edited", f"{name} saved ({len(df)} rows)")
    con.commit()


def _append(con, name, row: dict):
    df = table(con, name)
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).fillna("").astype(str).to_sql(
        name, con, index=False, if_exists="replace")


def _ts(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


def _log(con, rid, actor, role, action, detail="", ts=None):
    con.execute("INSERT INTO log (request_id, ts, actor, role, action, detail) VALUES (?,?,?,?,?,?)",
                (rid, ts or _ts(now(con)), actor, role, action, detail))


def _message(con, to_role, to_name, rid, text, ts=None):
    """A Teams message from the flow bot."""
    con.execute("INSERT INTO messages (ts, to_role, to_name, request_id, text) VALUES (?,?,?,?,?)",
                (ts or _ts(now(con)), to_role, to_name, rid, text))


# --------------------------------------------------------------------------- rules
def business_units(con) -> pd.DataFrame:
    return query(con, "SELECT * FROM BusinessUnits WHERE Active='Yes' ORDER BY Title")


def fields(con, rtype) -> pd.DataFrame:
    return query(con, "SELECT * FROM RequiredFields WHERE RequestType=?", (rtype,))


def choices(con, field) -> list:
    if field == "PaymentTerms":
        return PAYMENT_TERMS
    if field == "IsRegulated":
        return ["Yes", "No", "Not sure"]
    rows = query(con, "SELECT Title, SortOrder FROM ChoiceOptions WHERE ListName=? AND Active='Yes'", (field,))
    return list(rows.assign(o=pd.to_numeric(rows.SortOrder, errors="coerce")).sort_values("o").Title)


def _norm(v) -> str:
    return re.sub(r"\s", "", str(v or "")).lower()


def _one_of(value, listed) -> bool:
    """"A;D" = A or D; case and spaces ignored."""
    return _norm(value or "-") in _norm(listed).replace(",", ";").split(";")


def visible_fields(con, rtype, values) -> pd.DataFrame:
    f = fields(con, rtype)
    keep = [r.Required != "Conditional" or _one_of(values.get(r.ConditionField), r.ConditionValue)
            for r in f.itertuples()]
    return f[keep]


def person_for(con, role, entity):
    """The first Roles row for the role and the business (or Any), as the flow picks it; None = nobody set up."""
    r = query(con, "SELECT * FROM Roles WHERE Role=? AND Entity IN (?, 'Any') AND PersonName<>''", (role, entity))
    return r.iloc[0] if len(r) else None


def route_facts(con, rtype, values) -> dict:
    """The request's values for 'Only if' conditions, as the flow sees them: a field not on this request type is blank
    (a Yes/No field is No), and a regulated 'Not sure' counts as Yes (Quality/Regulatory decides)."""
    on_type = set(fields(con, rtype).FieldName)
    out = {}
    for f in ROUTE_FIELDS:
        v = values.get(f, "")
        if f not in on_type:
            v = "No" if f in ("IsRegulated", "SuppliesRegulatedGoods") else ""
        elif f == "IsRegulated":
            v = "Yes" if v in ("Yes", "Not sure") else "No"
        out[f] = v
    return out


def approval_steps(con, rtype, entity, values) -> list:
    """Who will approve: [(stage, role, person name or None)], from RoutingRules + Roles."""
    rules = query(con, "SELECT * FROM RoutingRules WHERE Active='Yes'")
    facts = route_facts(con, rtype, values)
    out, seen = [], set()
    for r in rules.itertuples():
        if r.RequestType not in (rtype, "Any") or r.Entity not in (entity, "Any"):
            continue
        if r.ConditionField and not (r.ConditionValue and _one_of(facts.get(r.ConditionField), r.ConditionValue)):
            continue
        stage = 2 if float(r.Stage or 1) >= 1.5 else 1
        if (stage, r.ApproverRole) in seen:  # a business-specific rule may repeat a general one
            continue
        seen.add((stage, r.ApproverRole))
        p = person_for(con, r.ApproverRole, entity)
        out.append((stage, r.ApproverRole, p.PersonName if p is not None else None))
    return sorted(out, key=lambda s: s[0])


def routing_gaps(con) -> list:
    """Rules health check: steps some active business has nobody for."""
    rules = query(con, "SELECT * FROM RoutingRules WHERE Active='Yes'")
    gaps = []
    for bu in business_units(con).Title:
        for role in sorted(set(rules[rules.Entity.isin([bu, "Any"])].ApproverRole)):
            if person_for(con, role, bu) is None:
                gaps.append(f"{bu}: nobody set up as {role}")
    return gaps


def add_business_unit(con, code, name, products, head, tz, actor):
    """Add a business unit and its BU Head (Rules > Businesses and people)."""
    _append(con, "BusinessUnits", dict(Title=code, BusinessUnitName=name, Products=products, Active="Yes"))
    if head:
        _append(con, "Roles", dict(Title=f"BU Head - {code}", Role="BU Head", Entity=code, PersonName=head,
                                   PersonEmail="", EscalateTo="", TimeZone=tz))
    _log(con, "", actor, "MDM Analyst", "Business unit added", f"{code} ({name})" + (f", BU Head {head}" if head else ""))
    con.commit()


# --------------------------------------------------------------------------- the form's checks
def field_problem(field, check, value, country) -> str:
    v = str(value or "").strip()
    if not v:
        return ""
    k = re.sub(r"[^A-Za-z0-9]", "", v).lower()
    if field not in NUMBERS and (not k or k in PLACEHOLDERS):
        return "looks like a placeholder. Enter the real value, or ask the MDM team if you don't have it"
    if field in NUMBERS:
        try:
            num = float(v.replace(",", ""))
        except ValueError:
            return "should be a number"
    c = check or DEFAULT_CHECKS.get(field, "None")
    if c == "Text":
        return "" if len(k) >= 3 else "is too short"
    if c == "Email":
        return "" if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v) else "isn't a valid email address"
    if c == "RegNo" and country in REG_NO:
        pattern, msg = REG_NO[country]
        return "" if re.match(pattern, k.upper()) else msg
    if c == "HSCode":
        return "" if re.match(r"^\d{6,10}$", k) else "should be 6 to 10 digits (e.g. 3822.19.00)"
    if c == "TaxID":
        return "" if 5 <= len(k) <= 20 and re.search(r"\d", k) else \
            "should be 5 to 20 letters and digits, including at least one digit"
    if c == "LicenceNo":
        return "" if 5 <= len(k) <= 30 and re.search(r"\d", k) else \
            "should be 5 to 30 letters and digits, including at least one digit"
    if c == "PartNo":
        return "" if len(k) >= 3 else "is too short for a part no."
    if c == "BankAccount":
        return "" if 6 <= len(k) <= 34 and re.search(r"\d{4}", k) else \
            "doesn't look like a bank account no. (6 to 34 characters, mostly digits)"
    if c == "Months":
        return "" if 1 <= num <= 120 else "should be between 1 and 120 months"
    if c == "Year":
        y = datetime.now().year
        return "" if y - 1 <= num <= y + 2 else f"should be between {y - 1} and {y + 2}"
    return ""


def _basic(name) -> str:
    s = (name or "").lower()
    for ch in PUNCT:
        s = s.replace(ch, " ")
    return " ".join(w for w in s.split() if w not in LEGAL)


def _best(key, rows):
    """rows: [(record id, name, match key, extra)] -> best (score, row) at or above the threshold, else None."""
    if len(key) < 4:
        return None
    scored = [(similarity(key, r[2]), r) for r in rows]
    best = max(scored, default=(0, None), key=lambda s: s[0])
    return best if best[0] >= THRESHOLD else None


def duplicate_check(con, rtype, entity, values, editing=None) -> dict:
    """The form's live duplicate check: same IDs are blocked, similar names (typos included) are warned.
    Against the master lists and against requests already waiting for approval."""
    noun = "cost centre" if rtype == "Cost Center" else rtype.lower()
    name = values.get(NAME_FIELD[rtype], "")
    key = match_key(name)
    country = values.get("Country", "")
    pending = query(con, f"SELECT * FROM requests WHERE type=? AND status IN ({','.join('?' * len(OPEN))}) AND id<>?",
                    (rtype, *OPEN, editing or ""))
    pending["v"] = pending.data.map(json.loads)
    if rtype == "Customer":
        pending = pending[pending.v.map(lambda d: d.get("Country")) == country]
    use = " Records in SAP B1 are shared by SPD, QTS and QTG, so use it instead of requesting a new one."
    follow = " Follow that request in My requests instead."
    sap_note = lambda s: " (approved, being set up in SAP)" if s == "Pending SAP import" else ""
    out = lambda status, rec, msg: dict(status=status, record=rec, message=msg)

    if rtype == "Cost Center":
        dept = values.get("Department", "")
        if entity and dept:
            cc = query(con, "SELECT * FROM CostCentres WHERE Entity=? AND Department=?", (entity, dept))
            if len(cc):
                return out("Blocked", cc.Title.iloc[0], f"A cost centre already exists for {entity} {dept}: "
                           f"{cc.CostCentreName.iloc[0]} ({cc.Title.iloc[0]}). Use it, or say why a second one is needed.")
            p = pending[pending.entity.eq(entity) & pending.v.map(lambda d: d.get("Department") == dept)]
            if len(p):
                return out("Blocked", p.id.iloc[0], f"Already requested: {p.id.iloc[0]} for {entity} {dept} is "
                           f"waiting for approval.{follow}")
        return out("Clear", "", "")

    id_field, id_label = ID_FIELD[rtype]
    ik = id_key(values.get(id_field, ""))
    master = {"Customer": ("CustomerMaster", "CustomerName"), "Item": ("ItemMaster", "Description"),
              "Vendor": ("VendorMaster", "VendorName")}[rtype]
    m = table(con, master[0])
    if ik:
        hit = m[m.IDKey == ik]
        if len(hit):
            h = hit.iloc[0]
            return out("Blocked", h.Title, f"This {noun} already exists: {h[master[1]]} ({h.Title}{sap_note(h.SAPStatus)}) "
                       f"has the same {id_label}{'' if id_label.endswith('.') else '.'}{use}")
    if rtype == "Customer" and name:
        al = table(con, "Aliases")
        basic = _basic(name)
        expanded = " ".join(EXPAND.get(w, w) for w in basic.split())
        hit = al[al.Title.isin([basic, expanded])]
        if len(hit):
            return out("Blocked", hit.RecordID.iloc[0], f"This customer already exists: \"{name}\" is a known name for "
                       f"{hit.CanonicalName.iloc[0]} ({hit.RecordID.iloc[0]}).{use}")
    if ik:
        p = pending[pending.v.map(lambda d: id_key(d.get(id_field, "")) == ik)]
        if len(p):
            r = p.iloc[0]
            return out("Blocked", r.id, f"Already requested: {r.id} ({r.v.get(NAME_FIELD[rtype], '')}, requested by "
                       f"{r.requestor}) has the same {id_label} and is waiting for approval.{follow}")
    if rtype == "Customer":
        m = m[m.Country == country]
    elif rtype == "Item" and values.get("ProductFamily"):
        m = m[m.ProductFamily == values["ProductFamily"]]
    best = _best(key, [(r.Title, r[master[1]], r.MatchKey, r.SAPStatus) for _, r in m.iterrows()])
    if best:
        s, r = best
        return out("Possible match", r[0], f"Possible match: {r[1]} ({r[0]}{sap_note(r[3])}, {s:.0%} similar name).")
    best = _best(key, [(r.id, r.v.get(NAME_FIELD[rtype], ""), match_key(r.v.get(NAME_FIELD[rtype], "")), r.requestor)
                       for r in pending.itertuples()])
    if best:
        s, r = best
        return out("Possible match", r[0], f"Possible match: {r[0]} ({r[1]}, requested by {r[3]}, {s:.0%} similar "
                   f"name) is waiting for approval.")
    return out("Clear", "", "")


def check_form(con, rtype, entity, values, not_same=False, reason="", editing=None) -> dict:
    """Everything the form shows: which fields, what's missing, format problems, duplicates, approvers, Submit."""
    vis = visible_fields(con, rtype, values)
    country = values.get("Country", "") if rtype == "Customer" else ""
    missing = [r.DisplayLabel for r in vis.itertuples() if not str(values.get(r.FieldName, "")).strip()]
    problems = {r.FieldName: p for r in vis.itertuples() if r.FieldName in FREE_TEXT + NUMBERS
                and (p := field_problem(r.FieldName, r.Check, values.get(r.FieldName), country))}
    dup = duplicate_check(con, rtype, entity, values, editing)
    overridden = dup["status"] != "Clear" and not_same and len(reason.strip()) >= 10
    labels = dict(zip(vis.FieldName, vis.DisplayLabel))
    todo = []
    if not entity:
        todo.append("Choose a business entity.")
    if missing:
        todo.append("Still needed: " + ", ".join(missing) + ".")
    if problems:
        todo.append("Check: " + "; ".join(f"{labels[f]} {p}" for f, p in problems.items()) + ".")
    if dup["status"] != "Clear" and not overridden:
        todo.append("Say why it's not the same (at least 10 characters)." if not_same else
                    "This already exists or is already requested (see above)." if dup["status"] == "Blocked" else
                    "Check the possible match above.")
    return dict(fields=vis, missing=missing, problems=problems, dup=dup, overridden=overridden,
                steps=approval_steps(con, rtype, entity, values) if entity else [], todo=todo, ok=not todo)


# --------------------------------------------------------------------------- flow: submit and route
def _next_id(con):
    n = con.execute("SELECT COUNT(*) FROM requests").fetchone()[0] + 1
    return f"REQ-{n:04d}"


def _split(con, rtype, values):
    sens = set(fields(con, rtype).query("Sensitive == 'Yes'").FieldName)
    return ({k: v for k, v in values.items() if k not in sens}, {k: v for k, v in values.items() if k in sens})


def submit(con, rtype, entity, requestor, values, dup, reason="", ts=None) -> str:
    """Submit: sensitive fields go to their own restricted list, then Route and approve runs."""
    t = ts or now(con)
    rid = _next_id(con)
    values = {f: values.get(f, "") for f in visible_fields(con, rtype, values).FieldName}  # hidden fields aren't saved
    public, secret = _split(con, rtype, values)
    con.execute("INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rid, rtype, entity, requestor, "Pending approval", "", _ts(t), "", json.dumps(public),
                 dup["status"], dup["record"], reason, "", ""))
    con.execute("INSERT INTO sensitive VALUES (?,?)", (rid, json.dumps(secret)))
    _log(con, rid, requestor, "Requestor", "Submitted", f"{rtype} request for {entity}", ts=_ts(t))
    if dup["status"] != "Clear":
        _log(con, rid, requestor, "Requestor", "Duplicate warning overridden",
             f"{dup['status']} ({dup['record']}). Reason: {reason}", ts=_ts(t))
    _route(con, rid, rtype, entity, values, 1, t)
    con.commit()
    return rid


def _assign(con, rid, role, entity, stage, rnd, t):
    p = person_for(con, role, entity)
    if p is None:  # nobody set up: MDM approves in their place instead of the request stalling
        mdm = person_for(con, "MDM Analyst", entity)
        person, queue = (mdm.PersonName if mdm is not None else "MDM team"), "MDM Analyst"
        _log(con, rid, "Flow", "System", "Routing gap", f"No {role} set up for {entity} in Roles; sent to MDM", ts=_ts(t))
        _message(con, "MDM Analyst", person, rid, f"{rid}: no {role} is set up for {entity}, so you approve "
                 f"in their place. Add one on the Rules screen.", ts=_ts(t))
    else:
        person, queue = p.PersonName, role
    con.execute("INSERT INTO approvals (request_id, role, person, queue, stage, round, status, assigned_at) "
                "VALUES (?,?,?,?,?,?,?,?)", (rid, role, person, queue, stage, rnd, "Pending", _ts(t)))
    _log(con, rid, person, role, "Assigned", f"Stage {stage}, round {rnd}", ts=_ts(t))
    _message(con, queue, person, rid, f"Approval needed: {rid} ({role}, stage {stage}).", ts=_ts(t))


def _route(con, rid, rtype, entity, values, stage, t):
    steps = [s for s in approval_steps(con, rtype, entity, values) if s[0] == stage]
    for _, role, _ in steps:
        _assign(con, rid, role, entity, stage, 1, t)
    con.execute("UPDATE requests SET stage=? WHERE id=?",
                ("Stage 1: checks in parallel" if stage == 1 else "Stage 2: MDM final check", rid))
    if stage == 1 and len(steps) > 1:
        _log(con, rid, "Flow", "System", "Sent in parallel", ", ".join(s[1] for s in steps), ts=_ts(t))
    if not steps and stage == 1:
        _route(con, rid, rtype, entity, values, 2, t)


def request(con, rid) -> dict:
    r = dict(con.execute("SELECT * FROM requests WHERE id=?", (rid,)).fetchone())
    r["values"] = json.loads(r["data"])
    sens = con.execute("SELECT data FROM sensitive WHERE request_id=?", (rid,)).fetchone()
    r["sensitive"] = json.loads(sens[0]) if sens else {}
    return r


def _latest(con, rid, stage):
    """Each role's latest round at a stage."""
    rows = query(con, "SELECT * FROM approvals WHERE request_id=? AND stage=? ORDER BY round", (rid, stage))
    return rows.groupby("role").tail(1)


def decide(con, approval_id, decision, actor, comment="", ts=None):
    """An approval card's answer: 'Approve', 'Request changes' or 'Reject'. Only open requests change status."""
    t = ts or now(con)
    approval_id = int(approval_id)  # a pandas integer doesn't bind as an SQLite parameter
    a = con.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    if a is None or a["status"] != "Pending":
        return
    rid = a["request_id"]
    req = request(con, rid)
    status = {"Approve": "Approved", "Reject": "Rejected", "Request changes": "Changes requested"}[decision]
    con.execute("UPDATE approvals SET status=?, decided_at=?, decided_by=?, comment=? WHERE id=?",
                (status, _ts(t), actor, comment, approval_id))
    _log(con, rid, actor, a["role"], decision, comment, ts=_ts(t))
    if req["status"] not in OPEN:
        con.commit()
        return
    if decision == "Reject":
        con.execute("UPDATE approvals SET status='Withdrawn' WHERE request_id=? AND status='Pending'", (rid,))
        con.execute("UPDATE requests SET status='Rejected', stage='Closed', completed_at=? WHERE id=?", (_ts(t), rid))
        _message(con, "Requestor", req["requestor"], rid, f"{rid} was rejected by {a['role']}: {comment}", ts=_ts(t))
    elif decision == "Request changes":
        con.execute("UPDATE requests SET status='Changes requested' WHERE id=?", (rid,))
        _message(con, "Requestor", req["requestor"], rid, f"{a['role']} asked for changes on {rid}: {comment} "
                 f"Open My requests and press Edit and resubmit.", ts=_ts(t))
    else:
        _advance(con, rid, a["stage"], t)
    con.commit()


def _advance(con, rid, stage, t):
    """After an approval: stage 1 all approved -> MDM final check; MDM approved -> SAP file."""
    req = request(con, rid)
    if req["status"] == "Changes requested":
        return
    latest = _latest(con, rid, stage)
    if not (latest.status == "Approved").all():
        return
    if stage == 1:
        _log(con, rid, "Flow", "System", "Stage 1 approved", "Sent to MDM for the final check", ts=_ts(t))
        _route(con, rid, req["type"], req["entity"], {**req["values"], **req["sensitive"]}, 2, t)
    else:
        _ready_for_sap(con, rid, t)


def change_note(con, rtype, old, new) -> str:
    """What the requestor changed. Sensitive values are named, never shown."""
    f = fields(con, rtype)
    labels, sens = dict(zip(f.FieldName, f.DisplayLabel)), set(f.query("Sensitive == 'Yes'").FieldName)
    changed = [k for k in f.FieldName if str(old.get(k, "")) != str(new.get(k, ""))]
    return "; ".join(f"{labels[k]} changed" if k in sens else f'{labels[k]}: "{old.get(k, "")}" -> "{new.get(k, "")}"'
                     for k in changed) or "No fields changed."


def resubmit(con, rid, values, actor, reply="", ts=None):
    """Edit and resubmit: the request is updated, and only the approvers who asked for changes see it again."""
    t = ts or now(con)
    req = request(con, rid)
    old = {**req["values"], **req["sensitive"]}
    values = {f: values.get(f, "") for f in visible_fields(con, req["type"], values).FieldName}
    public, secret = _split(con, req["type"], values)
    note = change_note(con, req["type"], old, values)
    con.execute("UPDATE requests SET data=?, status='Resubmitted', change_note=? WHERE id=?",
                (json.dumps(public), note, rid))
    con.execute("UPDATE sensitive SET data=? WHERE request_id=?", (json.dumps(secret), rid))
    _log(con, rid, actor, "Requestor", "Resubmitted", note + (f" Reply: {reply}" if reply else ""), ts=_ts(t))
    for stage in (1, 2):
        for a in _latest(con, rid, stage).itertuples():
            if a.status == "Changes requested":
                _assign(con, rid, a.role, req["entity"], stage, a.round + 1, t)
    con.commit()


# --------------------------------------------------------------------------- SAP B1
DTW = {  # (file object, [(DTW property, database column, value key)]); "~" keys come from the request itself
    "Customer": ("BusinessPartners", [("RecordKey", "RecordKey", "~1"), ("CardCode", "CardCode", "~code"),
        ("CardName", "CardName", "CustomerName"), ("CardType", "CardType", "~cCustomer"),
        ("GroupCode", "GroupCode", "Segment"), ("FederalTaxID", "LicTradNum", "RegistrationNo"),
        ("Address", "Address", "BillingAddress"), ("Country", "Country", "Country"),
        ("EmailAddress", "E_Mail", "ContactEmail"), ("PayTermsGrpCode", "GroupNum", "PaymentTerms"),
        ("CreditLimit", "CreditLine", "CreditLimit"), ("U_Entity", "U_Entity", "~entity"),
        ("U_OneRecordID", "U_OneRecordID", "~id")]),
    "Vendor": ("BusinessPartners", [("RecordKey", "RecordKey", "~1"), ("CardCode", "CardCode", "~code"),
        ("CardName", "CardName", "VendorName"), ("CardType", "CardType", "~cSupplier"),
        ("FederalTaxID", "LicTradNum", "TaxID"), ("Country", "Country", "Country"),
        ("PayTermsGrpCode", "GroupNum", "PaymentTerms"), ("DefaultBankCode", "BankCode", "BankName"),
        ("DefaultAccount", "DflAccount", "BankAccount"), ("U_Regulated", "U_Regulated", "SuppliesRegulatedGoods"),
        ("U_ISO13485", "U_ISO13485", "ISO13485CertNo"), ("U_Entity", "U_Entity", "~entity"),
        ("U_OneRecordID", "U_OneRecordID", "~id")]),
    "Item": ("Items", [("RecordKey", "RecordKey", "~1"), ("ItemCode", "ItemCode", "~code"),
        ("ItemName", "ItemName", "ItemDescription"), ("ItemsGroupCode", "ItmsGrpCod", "ProductFamily"),
        ("InventoryUOM", "InvntryUom", "UnitOfMeasure"), ("SupplierCatalogNo", "SuppCatNum", "ManufacturerPartNo"),
        ("U_HSCode", "U_HSCode", "HSCode"), ("U_Regulated", "U_Regulated", "IsRegulated"),
        ("U_LicenceNo", "U_LicenceNo", "RegulatoryLicenceNo"), ("U_ShelfLifeMonths", "U_ShelfLifeMonths", "ShelfLifeMonths"),
        ("U_Entity", "U_Entity", "~entity"), ("U_OneRecordID", "U_OneRecordID", "~id")]),
    "Cost Center": ("ProfitCenters", [("RecordKey", "RecordKey", "~1"), ("CenterCode", "PrcCode", "~code"),
        ("CenterName", "PrcName", "CostCenterName"), ("InWhichDimension", "DimCode", "~1"),
        ("U_Department", "U_Department", "Department"), ("U_Owner", "U_Owner", "Owner"),
        ("U_BudgetYear", "U_BudgetYear", "BudgetYear"), ("U_Entity", "U_Entity", "~entity"),
        ("U_OneRecordID", "U_OneRecordID", "~id")]),
}


def sap_code(req) -> str:
    """Proposed from the request number, so it never clashes with existing codes (as the flow does)."""
    n, v = int(req["id"].split("-")[1]), req["values"]
    return {"Customer": f"C2{n:04d}", "Vendor": f"V3{n:03d}", "Item": f"{v.get('ProductFamily', 'X')}-{5000 + n}"}.get(
        req["type"], f"{req['entity']}-{(v.get('Department', '') + 'XXX')[:3].upper()}{n}")


def _ready_for_sap(con, rid, t):
    """MDM approved: write the DTW file, add the record to its master list as Pending SAP import, tell MDM."""
    req = request(con, rid)
    code = sap_code(req)
    v = {**req["values"], **req["sensitive"]}
    obj, cols = DTW[req["type"]]
    special = {"~1": "1", "~code": code, "~entity": req["entity"], "~id": rid, "~cCustomer": "cCustomer",
               "~cSupplier": "cSupplier"}
    yes_no = {"Yes": "tYES", "No": "tNO", "Not sure": "tYES"}
    val = lambda k: special[k] if k.startswith("~") else (
        yes_no.get(v.get(k, ""), v.get(k, "")) if k in ("IsRegulated", "SuppliesRegulatedGoods") else str(v.get(k, "")))
    content = "\r\n".join("\t".join(row) for row in (
        [c[0] for c in cols], [c[1] for c in cols], [val(c[2]).replace("\t", " ").replace("\n", " ") for c in cols]))
    con.execute("INSERT OR REPLACE INTO sap_files VALUES (?,?,?,?)",
                (rid, f"{rid}_{obj}_DTW.txt", content + "\r\n", _ts(t)))
    row = {"Customer": ("CustomerMaster", dict(Title=code, CustomerName=v.get("CustomerName"), Country=v.get("Country"),
                                               RegistrationNo=v.get("RegistrationNo"), Segment=v.get("Segment"),
                                               CreatedByEntity=req["entity"])),
           "Item": ("ItemMaster", dict(Title=code, Description=v.get("ItemDescription"),
                                       ProductFamily=v.get("ProductFamily"), OwningEntity=req["entity"],
                                       UOM=v.get("UnitOfMeasure"), Regulated="No" if v.get("IsRegulated") == "No" else "Yes",
                                       ManufacturerPartNo=v.get("ManufacturerPartNo"))),
           "Vendor": ("VendorMaster", dict(Title=code, VendorName=v.get("VendorName"), Country=v.get("Country"),
                                           TaxID=v.get("TaxID"), CreatedByEntity=req["entity"])),
           "Cost Center": ("CostCentres", dict(Title=code, CostCentreName=v.get("CostCenterName"), Entity=req["entity"],
                                               Department=v.get("Department"), Owner=v.get("Owner")))}[req["type"]]
    extra = {} if req["type"] == "Cost Center" else dict(
        MatchKey=match_key(v.get(NAME_FIELD[req["type"]], "")), IDKey=id_key(v.get(ID_FIELD[req["type"]][0], "")))
    _append(con, row[0], {**row[1], **extra, "SAPStatus": "Pending SAP import"})
    con.execute("UPDATE requests SET status='Ready for SAP import', stage='MDM: import into SAP B1', sap_code=? "
                "WHERE id=?", (code, rid))
    _log(con, rid, "Flow", "System", "SAP file created", f"{rid}_{obj}_DTW.txt, proposed code {code}", ts=_ts(t))
    _message(con, "MDM Analyst", "", rid, f"{rid} is approved. Import {rid}_{obj}_DTW.txt into SAP B1, then press "
             f"Mark as created in SAP.", ts=_ts(t))
    _message(con, "Requestor", req["requestor"], rid, f"{rid} is approved and being set up in SAP as {code}.", ts=_ts(t))


def mark_created(con, rid, code, actor, ts=None):
    """MDM imported the file: the request is done and the master list row is In SAP."""
    t = ts or now(con)
    req = request(con, rid)
    master = {"Customer": "CustomerMaster", "Item": "ItemMaster", "Vendor": "VendorMaster",
              "Cost Center": "CostCentres"}[req["type"]]
    con.execute(f"UPDATE {master} SET Title=?, SAPStatus='In SAP' WHERE Title=?", (code, req["sap_code"]))
    con.execute("UPDATE requests SET status='Created in SAP', stage='Done', sap_code=?, completed_at=? WHERE id=?",
                (code, _ts(t), rid))
    _log(con, rid, actor, "MDM Analyst", "Created in SAP", f"SAP code {code}", ts=_ts(t))
    _message(con, "Requestor", req["requestor"], rid, f"{rid} is live in SAP B1 as {code}. You can use it now.", ts=_ts(t))
    con.commit()


# --------------------------------------------------------------------------- flow: reminders and escalation
def run_reminders(con) -> list:
    """9 AM reminders once SLADays pass, escalation after 4 days (the card goes to the approver's EscalateTo too),
    a nudge to MDM for files waiting a day, and closing requests left in Changes requested for 14 days."""
    t = now(con)
    rules = table(con, "RoutingRules")
    roles = table(con, "Roles")
    events = []
    for a in query(con, "SELECT a.*, r.type, r.entity, r.status AS req_status FROM approvals a "
                        "JOIN requests r ON r.id = a.request_id WHERE a.status='Pending'").itertuples():
        if a.req_status not in OPEN:
            continue
        rule = rules[(rules.ApproverRole == a.role) & rules.RequestType.isin([a.type, "Any"])]
        sla = float(rule.SLADays.iloc[0] or 2) if len(rule) else 2
        waited = (t - datetime.strptime(a.assigned_at, "%Y-%m-%d %H:%M")).days
        if waited >= sla and (not a.reminded_at or a.reminded_at[:10] < _ts(t)[:10]):
            con.execute("UPDATE approvals SET reminded_at=? WHERE id=?", (_ts(t), a.id))
            msg = f"Reminder: {a.request_id} has waited {waited} days for {a.person} ({a.role})"
            _log(con, a.request_id, "Flow", "System", "Reminder", f"{a.person}, {waited} days")
            _message(con, a.queue, a.person, a.request_id, msg + ".")
            events.append(msg)
        if a.stage == 1 and waited >= ESCALATE_AFTER_DAYS and not a.escalated_at:
            me = roles[(roles.Role == a.role) & roles.Entity.isin([a.entity, "Any"])]
            boss = roles[roles.PersonEmail == me.EscalateTo.iloc[0]] if len(me) and me.EscalateTo.iloc[0] else me.iloc[:0]
            queue, person = (boss.Role.iloc[0], boss.PersonName.iloc[0]) if len(boss) else ("MDM Analyst", "MDM team")
            con.execute("UPDATE approvals SET escalated_at=?, escalated_queue=?, escalated_person=? WHERE id=?",
                        (_ts(t), queue, person, a.id))
            msg = f"Escalated: {a.request_id} ({a.role}) re-sent to {person} after {waited} days; first answer counts"
            _log(con, a.request_id, "Flow", "System", "Escalated", f"Stage {a.stage}, round {a.round}: to {person}")
            _message(con, queue, person, a.request_id, msg + ".")
            events.append(msg)
    for r in query(con, "SELECT * FROM requests WHERE status='Ready for SAP import'").itertuples():
        f = con.execute("SELECT created_at FROM sap_files WHERE request_id=?", (r.id,)).fetchone()
        if f and (t - datetime.strptime(f[0], "%Y-%m-%d %H:%M")).days >= 1:
            _message(con, "MDM Analyst", "", r.id, f"Reminder: {r.id} is still waiting to be imported into SAP B1.")
            events.append(f"MDM reminded to import {r.id}")
    for r in query(con, "SELECT * FROM requests WHERE status='Changes requested'").itertuples():
        asked = query(con, "SELECT MAX(ts) AS ts FROM log WHERE request_id=? AND action='Request changes'", (r.id,)).ts[0]
        if asked and (t - datetime.strptime(asked, "%Y-%m-%d %H:%M")).days >= CLOSE_AFTER_DAYS:
            con.execute("UPDATE approvals SET status='Withdrawn' WHERE request_id=? AND status='Pending'", (r.id,))
            con.execute("UPDATE requests SET status='Closed', stage='Closed', completed_at=? WHERE id=?", (_ts(t), r.id))
            _log(con, r.id, "Flow", "System", "Closed", f"Not resubmitted within {CLOSE_AFTER_DAYS} days")
            _message(con, "Requestor", r.requestor, r.id, f"{r.id} was closed: not resubmitted within "
                     f"{CLOSE_AFTER_DAYS} days.")
            events.append(f"{r.id} closed (not resubmitted)")
    con.commit()
    return events


# --------------------------------------------------------------------------- views
def requests_view(con) -> pd.DataFrame:
    df = table(con, "requests")
    if df.empty:
        return df
    df["name"] = df.apply(lambda r: json.loads(r.data).get(NAME_FIELD[r.type], ""), axis=1)
    ap = query(con, "SELECT a.* FROM approvals a JOIN requests r ON r.id=a.request_id WHERE a.status='Pending'")
    waiting = (ap.person + " (" + ap.role + ")").groupby(ap.request_id).agg(", ".join)
    df["waiting_on"] = df.id.map(waiting).fillna("")
    df.loc[~df.status.isin(OPEN), "waiting_on"] = ""
    t = now(con)
    end = lambda r: datetime.strptime(r.completed_at, "%Y-%m-%d %H:%M") if r.completed_at else t
    df["days_open"] = df.apply(lambda r: (end(r) - datetime.strptime(r.submitted_at, "%Y-%m-%d %H:%M")).days, axis=1)
    return df.sort_values("id", ascending=False)


def can_see_sensitive(con, rtype, role) -> bool:
    vis = fields(con, rtype).query("Sensitive == 'Yes'").VisibleToRoles
    return any(role in str(v).split(";") or v == "All" for v in vis)


def approvals_for(con, role) -> pd.DataFrame:
    """Open cards in a role's queue, including cards escalated to it."""
    return query(con, "SELECT a.*, r.type, r.entity, r.requestor, r.status AS req_status FROM approvals a "
                      "JOIN requests r ON r.id=a.request_id WHERE a.status='Pending' "
                      f"AND r.status IN ({','.join('?' * len(OPEN))}) AND (a.queue=? OR a.escalated_queue=?) "
                      "ORDER BY a.assigned_at", (*OPEN, role, role))


def messages_for(con, role, name) -> pd.DataFrame:
    if role == "Requestor":
        return query(con, "SELECT * FROM messages WHERE to_role='Requestor' AND to_name=? ORDER BY id DESC", (name,))
    return query(con, "SELECT * FROM messages WHERE to_role=? ORDER BY id DESC", (role,))


# --------------------------------------------------------------------------- demo seed
def _seed(con):
    """Four requests in different states, so every role has something to look at."""
    base = now(con).replace(hour=10, minute=0)
    back = lambda d, h=0: base - timedelta(days=d, hours=h)
    clear = dict(status="Clear", record="", message="")
    cards = lambda rid: {r["role"]: r["id"] for r in con.execute(
        "SELECT id, role FROM approvals WHERE request_id=? AND status='Pending'", (rid,)).fetchall()}

    # Done: created in SAP
    r = submit(con, "Customer", "SPD", "Amy", dict(
        CustomerName="Kent Vale Medical Centre Pte Ltd", Country="SG", RegistrationNo="201933214M",
        BillingAddress="12 Kent Vale Road, Singapore 129797", ContactEmail="purchasing@kentvale.example",
        Segment="Clinic", PaymentTerms="30 days", CreditLimit="20000"), clear, ts=back(12))
    for role, aid in cards(r).items():
        decide(con, aid, "Approve", role, "", ts=back(10))
    decide(con, cards(r)["MDM Analyst"], "Approve", "Priya (MDM Analyst)", "Checked against ACRA", ts=back(9))
    mark_created(con, r, request(con, r)["sap_code"], "Priya (MDM Analyst)", ts=back(8))

    # Waiting on MDM: SAP file ready to import
    r = submit(con, "Item", "QTS", "Amy", dict(
        ItemDescription="Sterile Pipette Tips 200uL (rack of 96)", ProductFamily="B", UnitOfMeasure="Box",
        HSCode="3926.90.99", IsRegulated="No", ManufacturerPartNo="PT-200-R96"), clear, ts=back(6))
    for role, aid in cards(r).items():
        decide(con, aid, "Approve", role, "", ts=back(5))
    decide(con, cards(r)["MDM Analyst"], "Approve", "Priya (MDM Analyst)", "", ts=back(3))

    # Sent back: Finance asked for changes, Business Support approved, BU Head still waiting
    r = submit(con, "Vendor", "QTG", "Amy", dict(
        VendorName="Mekong Medical Supplies JSC", Country="Vietnam", TaxID="0312345678",
        SuppliesRegulatedGoods="Yes", ISO13485CertNo="ISO13485-VN-22817", BankName="Vietcombank",
        BankAccount="0071001234567", PaymentTerms="30 days"), clear, ts=back(3))
    c = cards(r)
    decide(con, c["Business Support"], "Approve", "Business Support", "", ts=back(2))
    decide(con, c["Finance"], "Request changes", "Wei Jie (Finance Manager)",
           "Please attach the bank's confirmation letter and use 45 days, our standard for new vendors.", ts=back(2, -3))

    # In progress, overdue: Finance hasn't answered for 5 days, so it was reminded and escalated
    r = submit(con, "Customer", "SPD", "Daniel", dict(
        CustomerName="Penang Adventist Hospital", Country="MY", RegistrationNo="196501000123",
        BillingAddress="465 Jalan Burma, 10350 George Town, Penang", ContactEmail="procurement@pah.example",
        Segment="Hospital", PaymentTerms="45 days", CreditLimit="50000"), clear, ts=back(5))
    c = cards(r)
    decide(con, c["BU Head"], "Approve", "SPD BU Head", "Key account for Penang", ts=back(4))
    run_reminders(con)
