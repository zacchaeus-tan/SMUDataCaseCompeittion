"""
Workflow mock-up of the Power Apps form + Power Automate flows, backed by SQLite.

It reads the SAME rule tables that are imported into SharePoint (sharepoint/*.csv) and behaves the way
the real flows should, so it doubles as a working spec for the Power Platform build:

  submit()      = Power Apps "Submit" + flow trigger "When an item is created in Requests"
  route()       = flow: look up RoutingRules -> start all stage-1 approvals IN PARALLEL
  decide()      = approval outcome -> log; all approved -> stage 2 (MDM); MDM approves -> SAP import row
  run_reminders = scheduled flow: reminders after SLADays, escalation after EscalateAfterDays
A simulated clock (advance_clock) lets a demo fast-forward days.
"""
import json
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
from rapidfuzz import fuzz

from .config import SHAREPOINT, STATE
from .normalise import name_key

DB = STATE / "workflow.sqlite"
RULE_TABLES = ["BusinessUnits", "RoutingRules", "RequiredFields", "Roles", "Aliases"]
SENSITIVE_ROLES = {"Finance", "MDM Analyst"}

PERSONAS = {  # display persona -> role (mirrors sharepoint/Roles.csv)
    "Amy Tan - Product Manager (requestor)": "Requestor",
    "Marcus Lee - Regional Sales, new BU (requestor)": "Requestor",
    "BU Head": "BU Head",
    "Wei Jie - Finance Manager": "Finance",
    "QA / Regulatory Lead": "Quality/Regulatory",
    "Business Support": "Business Support",
    "Priya - MDM Analyst": "MDM Analyst",
}


# --------------------------------------------------------------------------- storage
def connect():
    STATE.mkdir(exist_ok=True)
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def reset(seed_demo=True):
    """Fresh state: load rule tables from the SharePoint CSVs, empty requests, optional demo requests."""
    if DB.exists():
        DB.unlink()
    con = connect()
    con.executescript("""
    CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE requests (id TEXT PRIMARY KEY, type TEXT, entity TEXT, country TEXT, requestor TEXT,
        status TEXT, stage TEXT, submitted_at TEXT, completed_at TEXT, data TEXT, dup_check TEXT,
        possible_match TEXT, sap_code TEXT);
    CREATE TABLE sensitive (request_id TEXT PRIMARY KEY, data TEXT);
    CREATE TABLE approvals (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, role TEXT, person TEXT,
        stage INTEGER, status TEXT, assigned_at TEXT, decided_at TEXT, comment TEXT,
        reminded_at TEXT, escalated_at TEXT);
    CREATE TABLE log (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, ts TEXT, actor TEXT, role TEXT,
        action TEXT, detail TEXT, field TEXT, old_value TEXT, new_value TEXT);
    CREATE TABLE sap_import (request_id TEXT, object TEXT, payload TEXT, created_at TEXT);
    """)
    con.execute("INSERT INTO settings VALUES ('clock_offset_days', '0')")
    for t in RULE_TABLES:
        pd.read_csv(SHAREPOINT / f"{t}.csv", dtype=str).fillna("").to_sql(t, con, index=False)
    con.commit()
    if seed_demo:
        _seed(con)
    return con


def ensure():
    if not DB.exists():
        return reset()
    con = connect()
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in RULE_TABLES:  # demo state from an older version: add any rule table it lacks
        if t not in have:
            pd.read_csv(SHAREPOINT / f"{t}.csv", dtype=str).fillna("").to_sql(t, con, index=False)
    con.commit()
    return con


def now(con) -> datetime:
    off = float(con.execute("SELECT value FROM settings WHERE key='clock_offset_days'").fetchone()[0])
    return datetime.now().replace(second=0, microsecond=0) + timedelta(days=off)


def advance_clock(con, days: float):
    off = float(con.execute("SELECT value FROM settings WHERE key='clock_offset_days'").fetchone()[0]) + days
    con.execute("UPDATE settings SET value=? WHERE key='clock_offset_days'", (str(off),))
    con.commit()
    return run_reminders(con)


def query(con, sql, params=()) -> pd.DataFrame:
    """Read rows for display. Empty SQL values come back as "" (not NaN, which Python treats as true)."""
    df = pd.read_sql(sql, con, params=params)
    obj = df.select_dtypes(exclude="number").columns
    df[obj] = df[obj].fillna("")
    return df


def table(con, name) -> pd.DataFrame:
    return query(con, f"SELECT * FROM {name}")


def save_rules(con, name: str, df: pd.DataFrame, actor="Priya - MDM Analyst"):
    """The MDM team edits a rule table (SharePoint list) - no IT involved. Logged like any change."""
    df.fillna("").astype(str).to_sql(name, con, index=False, if_exists="replace")
    _log(con, "", actor, "MDM Analyst", "Rule table edited", f"{name} updated ({len(df)} rows)")
    con.commit()


def _ts(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


def _log(con, rid, actor, role, action, detail="", field="", old="", new="", ts=None):
    con.execute("INSERT INTO log (request_id, ts, actor, role, action, detail, field, old_value, new_value) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (rid, ts or _ts(now(con)), actor, role, action, detail, field, old, new))


# --------------------------------------------------------------------------- form rules
def business_units(con) -> pd.DataFrame:
    """Active business units: the form's 'Business entity' dropdown. A new BU = one row here."""
    return pd.read_sql("SELECT * FROM BusinessUnits WHERE Active='Yes'", con)


def request_types(con) -> list:
    """Request types = every type that has fields in RequiredFields. A new data domain = new field rows."""
    types = pd.read_sql("SELECT DISTINCT RequestType FROM RequiredFields", con).RequestType
    order = ["Customer", "Item", "Vendor", "Cost Center"]
    return sorted([t for t in types if t and t != "Any"], key=lambda t: (order.index(t) if t in order else 99, t))


def routing_gaps(con) -> list:
    """Rules health check: approver roles a request would be routed to with nobody set up in Roles."""
    rules = pd.read_sql("SELECT * FROM RoutingRules WHERE Active='Yes'", con)
    roles = pd.read_sql("SELECT * FROM Roles", con)
    gaps = []
    for bu in business_units(con).Title:
        for role in sorted(set(rules[rules.Entity.isin([bu, "Any"])].ApproverRole)):
            if not len(roles[(roles.Role == role) & roles.Entity.isin([bu, "Any"])]):
                gaps.append(f"{bu}: no one set up as {role} in Roles")
    return gaps


def add_business_unit(con, code, name, products, head, email, tz, qa_all_items=False,
                      actor="Priya - MDM Analyst"):
    """Onboard a business unit by adding rows to three rule lists - what the MDM team does in SharePoint."""
    if code in set(pd.read_sql("SELECT Title FROM BusinessUnits", con).Title):
        return
    _append(con, "BusinessUnits", dict(Title=code, BusinessUnitName=name, Products=products, Active="Yes"))
    _append(con, "Roles", dict(Title=f"BU Head - {code}", Role="BU Head", Entity=code, PersonName=head,
                               PersonEmail=email, EscalateTo="", TimeZone=tz))
    added = [f"BusinessUnits: {code}", f"Roles: BU Head - {code} ({head}, {tz})"]
    if qa_all_items:
        n = con.execute("SELECT COUNT(*) FROM RoutingRules").fetchone()[0] + 1
        _append(con, "RoutingRules", dict(Title=f"R{n:02d}", RequestType="Item", Entity=code, ConditionField="",
                                          ConditionValue="", ApproverRole="Quality/Regulatory", Stage="1",
                                          SLADays="2", EscalateAfterDays="4", Active="Yes"))
        added.append(f"RoutingRules: every {code} item also needs Quality/Regulatory")
    _log(con, "", actor, "MDM Analyst", "Business unit added", " | ".join(added))
    con.commit()


def _append(con, name, row: dict):
    df = pd.read_sql(f"SELECT * FROM {name}", con)
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).fillna("").astype(str).to_sql(
        name, con, index=False, if_exists="replace")


def form_fields(con, request_type) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM RequiredFields WHERE RequestType=?", con, params=(request_type,))


def field_visible(row, values) -> bool:
    if row["Required"] != "Conditional":
        return True
    return str(values.get(row["ConditionField"], "")) == row["ConditionValue"]


def missing_fields(con, request_type, values) -> list:
    out = []
    for _, r in form_fields(con, request_type).iterrows():
        if field_visible(r, values) and str(values.get(r["FieldName"], "")).strip() in ("", "None"):
            out.append(r["DisplayLabel"])
    return out


def duplicate_check(con, request_type, values, customers: pd.DataFrame, items: pd.DataFrame):
    """Live check, same three rules the Power Apps version uses (see sharepoint/LISTS.md),
    plus a typo-tolerant similarity score that production would get from the matching engine."""
    if request_type == "Customer":
        name, country, reg = values.get("CustomerName", ""), values.get("Country", ""), values.get("RegistrationNo", "")
        pool = customers[customers.country == country] if country else customers
        if reg:
            hit = pool[pool.registration_no == reg]
            if len(hit):
                r = hit.iloc[0]
                return "Blocked", r.record_id, f"Registration no. already used by {r.customer_name} ({r.record_id})"
        key = name_key(name)
        alias = pd.read_sql("SELECT * FROM Aliases", con)
        a = alias[alias.Title == key]
        if len(a):
            return "Blocked", a.iloc[0].RecordID, f"'{name}' is a known alias of {a.iloc[0].CanonicalName}"
        if len(key) >= 3:
            scored = pool.assign(score=pool.customer_name.map(lambda n: max(fuzz.ratio(key, name_key(n)),
                                                                             fuzz.token_sort_ratio(key, name_key(n)))))
            best = scored.sort_values("score", ascending=False).head(3)
            if len(best) and best.iloc[0].score >= 85:
                r = best.iloc[0]
                return "Possible match", r.record_id, f"{r.score:.0f}% similar to {r.customer_name} ({r.record_id})"
        return "Clear", "", "No similar customer found"
    if request_type == "Item":
        desc = values.get("ItemDescription", "")
        if len(desc) >= 4:
            scored = items.assign(score=items.description.map(lambda d: fuzz.token_set_ratio(desc.lower(), d.lower())))
            r = scored.sort_values("score", ascending=False).iloc[0]
            if r.score >= 85:
                return "Possible match", r.item_code, f"{r.score:.0f}% similar to {r.description} ({r.item_code})"
        return "Clear", "", "No similar item found"
    return "Clear", "", "Not checked for this request type"


# --------------------------------------------------------------------------- flow: submit & route
def _next_id(con):
    n = con.execute("SELECT COUNT(*) FROM requests").fetchone()[0] + 1
    return f"REQ-{n:04d}"


def _people(con, role, entity):
    roles = pd.read_sql("SELECT * FROM Roles", con)
    r = roles[(roles.Role == role) & (roles.Entity.isin([entity, "Any"]))]
    return r.iloc[0] if len(r) else None


def person_for(con, role, entity) -> str:
    p = _people(con, role, entity)
    return p.PersonName if p is not None else ""


def submit(con, request_type, entity, country, requestor, values: dict, dup: tuple, ts=None):
    """Power Apps submit: sensitive fields go to their own locked-down list; then the routing flow runs."""
    t = ts or now(con)
    rid = _next_id(con)
    sens_fields = set(form_fields(con, request_type).query("Sensitive == 'Yes'").FieldName)
    public = {k: v for k, v in values.items() if k not in sens_fields}
    secret = {k: v for k, v in values.items() if k in sens_fields}
    con.execute("INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rid, request_type, entity, country, requestor, "Pending approval", "", _ts(t), "",
                 json.dumps(public), dup[0], dup[1], ""))
    con.execute("INSERT INTO sensitive VALUES (?,?)", (rid, json.dumps(secret)))
    _log(con, rid, requestor, "Requestor", "Submitted", f"{request_type} request for {entity}", ts=_ts(t))
    _log(con, rid, "MDM workflow", "System", "Duplicate check", f"{dup[0]}: {dup[2]}", ts=_ts(t))
    if secret:
        _log(con, rid, "MDM workflow", "System", "Sensitive fields stored",
             f"{', '.join(sorted(secret))} saved to restricted list (Finance & MDM only)", ts=_ts(t))
    route(con, rid, request_type, entity, values, t)
    con.commit()
    return rid


def route(con, rid, request_type, entity, values, t):
    rules = pd.read_sql("SELECT * FROM RoutingRules WHERE Active='Yes'", con)
    rules = rules[rules.RequestType.isin([request_type, "Any"]) & rules.Entity.isin([entity, "Any"])]
    stage1 = []
    for _, r in rules[rules.Stage == "1"].iterrows():
        if r.ConditionField and str(values.get(r.ConditionField, "")) != r.ConditionValue:
            continue
        if r.ApproverRole in (role for role, _ in stage1):  # a BU-specific rule may repeat a general one
            continue
        p = _people(con, r.ApproverRole, entity)
        stage1.append((r.ApproverRole, p.PersonName if p is not None else r.ApproverRole))
    for role, person in stage1:
        con.execute("INSERT INTO approvals (request_id, role, person, stage, status, assigned_at) VALUES (?,?,?,?,?,?)",
                    (rid, role, person, 1, "Pending", _ts(t)))
    con.execute("UPDATE requests SET stage=? WHERE id=?", ("Stage 1: parallel checks", rid))
    _log(con, rid, "MDM workflow", "System", "Routed in parallel",
         " | ".join(f"{p} ({r})" for r, p in stage1) + " - Teams approval cards sent", ts=_ts(t))


def decide(con, approval_id, decision, actor, comment="", ts=None):
    t = ts or now(con)
    a = con.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    if a is None or a["status"] != "Pending":
        return
    rid = a["request_id"]
    con.execute("UPDATE approvals SET status=?, decided_at=?, comment=? WHERE id=?",
                (decision, _ts(t), comment, approval_id))
    _log(con, rid, actor, a["role"], decision, comment, ts=_ts(t))
    if decision == "Rejected":
        con.execute("UPDATE approvals SET status='Cancelled' WHERE request_id=? AND status='Pending'", (rid,))
        con.execute("UPDATE requests SET status='Rejected', stage='Closed', completed_at=? WHERE id=?", (_ts(t), rid))
        _log(con, rid, "MDM workflow", "System", "Requestor notified",
             f"Rejected by {a['role']}; other approvers' cards withdrawn", ts=_ts(t))
    else:
        pending = con.execute("SELECT COUNT(*) FROM approvals WHERE request_id=? AND status='Pending'", (rid,)).fetchone()[0]
        if pending == 0 and a["stage"] == 1:
            req = con.execute("SELECT entity FROM requests WHERE id=?", (rid,)).fetchone()
            p = _people(con, "MDM Analyst", req["entity"])
            con.execute("INSERT INTO approvals (request_id, role, person, stage, status, assigned_at) VALUES (?,?,?,?,?,?)",
                        (rid, "MDM Analyst", p.PersonName if p is not None else "MDM Analyst", 2, "Pending", _ts(t)))
            con.execute("UPDATE requests SET stage='Stage 2: MDM final check' WHERE id=?", (rid,))
            _log(con, rid, "MDM workflow", "System", "All checks approved", "Sent to MDM for final check", ts=_ts(t))
        elif a["stage"] == 2:
            _create_in_sap(con, rid, t)
    con.commit()


def _create_in_sap(con, rid, t):
    req = dict(con.execute("SELECT * FROM requests WHERE id=?", (rid,)).fetchone())
    data = json.loads(req["data"])
    sens = json.loads(con.execute("SELECT data FROM sensitive WHERE request_id=?", (rid,)).fetchone()[0])
    n = con.execute("SELECT COUNT(*) FROM sap_import").fetchone()[0]
    if req["type"] == "Customer":
        code, obj = f"C2{n + 1:04d}", "oBusinessPartners"
        payload = dict(CardCode=code, CardName=data.get("CustomerName"), CardType="cCustomer",
                       Country=req["country"], Address=data.get("BillingAddress"),
                       FederalTaxID=data.get("RegistrationNo"), EmailAddress=data.get("ContactEmail"),
                       GroupCode=data.get("Segment"), PayTermsGrpCode=sens.get("PaymentTerms"),
                       CreditLimit=sens.get("CreditLimit"), U_Entity=req["entity"])
    elif req["type"] == "Item":
        code, obj = f"{data.get('ProductFamily', 'X')}-{5001 + n}", "oItems"
        payload = dict(ItemCode=code, ItemName=data.get("ItemDescription"), ItemsGroupCode=data.get("ProductFamily"),
                       InventoryUOM=data.get("UnitOfMeasure"), U_HSCode=data.get("HSCode"),
                       U_Regulated=data.get("IsRegulated"), U_LicenceNo=data.get("RegulatoryLicenceNo"),
                       U_Entity=req["entity"])
    elif req["type"] == "Vendor":
        code, obj = f"V3{n + 1:03d}", "oBusinessPartners"
        payload = dict(CardCode=code, CardName=data.get("VendorName"), CardType="cSupplier",
                       Country=data.get("Country"), FederalTaxID=data.get("TaxID"),
                       PayTermsGrpCode=sens.get("PaymentTerms"), BankName=sens.get("BankName"),
                       BankAccount=sens.get("BankAccount"), U_Entity=req["entity"])
    else:
        code, obj = f"{req['entity']}-{data.get('Department', 'GEN')[:3].upper()}{n + 1}", "oProfitCenters"
        payload = dict(CenterCode=code, CenterName=data.get("CostCenterName"), U_Owner=data.get("Owner"),
                       U_Entity=req["entity"])
    con.execute("INSERT INTO sap_import VALUES (?,?,?,?)", (rid, obj, json.dumps(payload), _ts(t)))
    con.execute("UPDATE requests SET status='Created in SAP', stage='Done', completed_at=?, sap_code=? WHERE id=?",
                (_ts(t), code, rid))
    _log(con, rid, "MDM workflow", "System", "SAP import file generated", f"{obj} row for {code} (DTW template)", ts=_ts(t))
    _log(con, rid, "MDM workflow", "System", "Requestor notified", f"Record {code} is live - you can transact now", ts=_ts(t))


# --------------------------------------------------------------------------- scheduled flow: reminders
def days_waiting(start: datetime, end: datetime) -> int:
    """Whole calendar days, the same count the Power Automate reminders flow uses."""
    return max(0, (end - start).days)


def run_reminders(con) -> list:
    t = now(con)
    rules = pd.read_sql("SELECT * FROM RoutingRules", con)
    roles = pd.read_sql("SELECT * FROM Roles", con)
    events = []
    for a in con.execute("SELECT a.*, r.type, r.entity FROM approvals a JOIN requests r ON r.id=a.request_id "
                         "WHERE a.status='Pending'").fetchall():
        rule = rules[(rules.ApproverRole == a["role"]) & rules.RequestType.isin([a["type"], "Any"])]
        sla = float(rule.SLADays.iloc[0] or 2) if len(rule) else 2
        esc = float(rule.EscalateAfterDays.iloc[0] or 0) if len(rule) and rule.EscalateAfterDays.iloc[0] else None
        waited = days_waiting(datetime.strptime(a["assigned_at"], "%Y-%m-%d %H:%M"), t)
        person = roles[(roles.Role == a["role"]) & roles.Entity.isin([a["entity"], "Any"])]
        tz = person.TimeZone.iloc[0] if len(person) else "Asia/Singapore"
        if waited >= sla and not a["reminded_at"]:
            con.execute("UPDATE approvals SET reminded_at=? WHERE id=?", (_ts(t), a["id"]))
            msg = f"Reminder to {a['person']} in Teams at 09:00 {tz} ({waited} days waiting)"
            _log(con, a["request_id"], "MDM workflow", "System", "Reminder sent", msg)
            events.append(msg)
        if esc and waited >= esc and not a["escalated_at"]:
            con.execute("UPDATE approvals SET escalated_at=? WHERE id=?", (_ts(t), a["id"]))
            msg = f"Escalated: {a['person']} has not responded in {waited} days - manager notified"
            _log(con, a["request_id"], "MDM workflow", "System", "Escalated", msg)
            events.append(msg)
    con.commit()
    return events


# --------------------------------------------------------------------------- views
def requests_view(con) -> pd.DataFrame:
    df = table(con, "requests")
    if df.empty:
        return df
    df["subject"] = df.data.map(lambda d: next((v for k, v in json.loads(d).items()
                                                 if k in ("CustomerName", "ItemDescription", "VendorName", "CostCenterName")), ""))
    ap = table(con, "approvals")
    waiting = ap[ap.status == "Pending"].groupby("request_id").person.apply(lambda s: ", ".join(s))
    df["waiting_on"] = df.id.map(waiting).fillna("")
    t = now(con)
    df["age_days"] = df.apply(lambda r: round(((datetime.strptime(r.completed_at, "%Y-%m-%d %H:%M") if r.completed_at
                                                else t) - datetime.strptime(r.submitted_at, "%Y-%m-%d %H:%M")).total_seconds() / 86400, 1), axis=1)
    return df


def sensitive_for(con, rid, role) -> dict:
    row = con.execute("SELECT data FROM sensitive WHERE request_id=?", (rid,)).fetchone()
    data = json.loads(row[0]) if row else {}
    if role in SENSITIVE_ROLES:
        return data
    return {k: "•••••• (restricted)" for k in data}


def sap_file(con) -> pd.DataFrame:
    rows = []
    for r in con.execute("SELECT * FROM sap_import").fetchall():
        rows.append(dict(RequestID=r["request_id"], Object=r["object"], CreatedAt=r["created_at"], **json.loads(r["payload"])))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- demo seed
def _seed(con):
    base = now(con).replace(hour=10, minute=0)
    back = lambda d, h=0: base - timedelta(days=d, hours=h)
    r1 = submit(con, "Customer", "SPD", "SG", "Amy Tan - Product Manager (requestor)",
                dict(CustomerName="Kent Vale Medical Centre Pte Ltd", Country="SG", RegistrationNo="201933214M",
                     BillingAddress="12 Kent Vale Road, Clementi", ContactEmail="purchasing@kentvale.example",
                     Segment="Clinic", PaymentTerms="30 days", CreditLimit="20000"),
                ("Clear", "", "No similar customer found"), ts=back(6))
    for a in con.execute("SELECT id, role FROM approvals WHERE request_id=?", (r1,)).fetchall():
        if a["role"] == "BU Head":
            decide(con, a["id"], "Approved", "BU Head", "Strategic account for SPD", ts=back(5))
        if a["role"] == "Business Support":
            decide(con, a["id"], "Approved", "Business Support", "", ts=back(4, -4))
    r2 = submit(con, "Item", "QTS", "SG", "Amy Tan - Product Manager (requestor)",
                dict(ItemDescription="Dengue NS1/IgG/IgM Combo Rapid Test (25 tests)", ProductFamily="A",
                     UnitOfMeasure="Kit", HSCode="3822.19", IsRegulated="Yes", RegulatoryLicenceNo="DE0512345",
                     ShelfLifeMonths="18"), ("Clear", "", "No similar item found"), ts=back(9))
    for a in con.execute("SELECT id, role FROM approvals WHERE request_id=?", (r2,)).fetchall():
        decide(con, a["id"], "Approved", a["role"], "", ts=back(8))
    m = con.execute("SELECT id FROM approvals WHERE request_id=? AND stage=2", (r2,)).fetchone()
    decide(con, m["id"], "Approved", "Priya - MDM Analyst", "Checked against licence register", ts=back(7, -5))
    run_reminders(con)
