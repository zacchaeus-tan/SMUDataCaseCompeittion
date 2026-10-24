"""Workflow mock-up pages: each mirrors a Power Apps screen or a Power Automate flow."""
import json

import pandas as pd
import streamlit as st

from onerecord import workflow as wf
from onerecord.config import COUNTRIES

from . import common as c

CHOICES = {
    "Country": list(COUNTRIES),
    "Segment": ["Hospital", "Laboratory", "Clinic"],
    "PaymentTerms": ["30 days", "45 days", "60 days", "90 days", "Advance"],
    "ProductFamily": ["A", "B", "C"],
    "UnitOfMeasure": ["Kit", "Box", "Pack", "Unit", "Set"],
    "Department": ["Sales", "Marketing", "Regulatory Affairs", "Service", "Finance", "Warehouse"],
}
# Streamlit text colours for a status word: green done, orange waiting, red stopped
STATUS_COLOR = {"Approved": "green", "Pending": "orange", "Rejected": "red", "Cancelled": "gray"}
SECTION = "Workflow mock-up"


def _page(title, where):
    c.header(SECTION, title)
    st.caption(f"In production: {where}")


def _status(s):
    return f":{STATUS_COLOR.get(s, 'gray')}[{s}]"


def _fields(data):
    """Request details as a two-column Field / Value table rather than raw JSON."""
    if not data:
        st.caption("Nothing to show.")
        return
    st.dataframe(pd.DataFrame({"Field": list(data), "Value": [str(v) for v in data.values()]}),
                 hide_index=True, width="stretch")


# --------------------------------------------------------------------------- 1. form
def _clear_form():
    """Reset every form widget (top selectors, all detail fields of every request type, the duplicate tick-box)."""
    for k in list(st.session_state):
        if k.startswith(("req_", "Customer_", "Item_", "Vendor_", "Cost Center_", "dup_ok")):
            del st.session_state[k]


def new_request():
    _page("New request", "Power Apps canvas app in a Teams tab, saving to the SharePoint Requests list")
    rid = st.session_state.pop("last_request", None)  # show the confirmation once, on a blank form
    if rid:
        st.success(f"Submitted {rid}. Approval cards have been sent in Teams; you can follow it under "
                   f"Request status.")
    con = c.con()
    d = c.raw()

    top = st.columns(3)
    bus = wf.business_units(con)
    bu_name = dict(zip(bus.Title, bus.BusinessUnitName))
    rtype = c.select(top[0], "What do you need?", wf.request_types(con), key="req_type",
                             help="From the RequiredFields list: a new data domain appears here once its fields exist")
    entity = c.select(top[1], "Business entity", list(bus.Title), key="req_entity",
                              format_func=lambda k: bu_name.get(k, k),
                              help="From the BusinessUnits list: the MDM team adds a new BU there, no IT change")
    country = c.select(top[2], "Country", list(COUNTRIES), format_func=lambda k: COUNTRIES[k], key="req_country")

    fields = wf.form_fields(con, rtype)
    values = {"Country": country} if rtype in ("Customer",) else {}
    st.markdown("##### Details")
    st.caption("Fields come from the RequiredFields rule table. Conditional fields appear only when they apply.")
    cols = st.columns(2)
    shown = 0
    for _, f in fields.iterrows():
        if f.FieldName == "Country" and rtype == "Customer":
            continue
        if not wf.field_visible(f, values):
            continue
        col = cols[shown % 2]
        shown += 1
        label = f"{f.DisplayLabel}{' (restricted)' if f.Sensitive == 'Yes' else ''}"
        key = f"{rtype}_{f.FieldName}"
        help_ = (f.HelpText or None)
        if f.FieldType == "Yes/No":
            values[f.FieldName] = c.select(col, label, ["", "Yes", "No"], key=key, help=help_)
        elif f.FieldType == "Choice" and f.FieldName in CHOICES:
            values[f.FieldName] = c.select(col, label, [""] + CHOICES[f.FieldName], key=key, help=help_)
        else:
            values[f.FieldName] = col.text_input(label, key=key, help=help_)
    if (fields.Sensitive == "Yes").any():
        st.caption("Restricted fields are saved to a separate list that only Finance and MDM can open.")

    dup = wf.duplicate_check(con, rtype, values, d["customers"], d["items"])
    missing = wf.missing_fields(con, rtype, values)
    rules = pd.read_sql("SELECT * FROM RoutingRules WHERE Active='Yes'", con)
    rules = rules[rules.RequestType.isin([rtype, "Any"]) & rules.Entity.isin([entity, "Any"])]
    who = []
    for _, r in rules[rules.Stage == "1"].iterrows():
        if not r.ConditionField or str(values.get(r.ConditionField, "")) == r.ConditionValue:
            p = wf.person_for(con, r.ApproverRole, entity)
            who.append(f"{r.ApproverRole} ({p})" if p else f"{r.ApproverRole} (:red[nobody set up])")

    st.markdown("##### Checks before submitting")
    with st.container(border=True):
        st.markdown("**Required fields:** " + (f":orange[still needed:] {', '.join(missing)}" if missing
                                               else ":green[complete]"))
        name_field = {"Customer": "CustomerName", "Item": "ItemDescription"}.get(rtype)
        if name_field and not values.get(name_field):
            st.markdown("**Duplicate check:** runs as soon as you enter the name.")
        else:
            color = {"Blocked": "red", "Possible match": "orange", "Clear": "green"}[dup[0]]
            st.markdown(f"**Duplicate check:** :{color}[{dup[0].lower()}]. {dup[2]}")
        st.markdown(f"**Approvers:** {', '.join(dict.fromkeys(who))} at the same time, then the MDM team.")
        confirm = True
        if dup[0] == "Possible match":
            confirm = st.checkbox(f"I checked {dup[1]} and this is a different record", key="dup_ok")

    can_submit = not missing and dup[0] != "Blocked" and confirm and c.role() == "Requestor"
    if c.role() != "Requestor":
        st.caption("Switch the persona in the sidebar to a requestor (Amy or Marcus) to submit.")
    if st.button("Submit request", type="primary", disabled=not can_submit):
        rid = wf.submit(con, rtype, entity, country, c.persona(), {k: v for k, v in values.items() if v}, dup)
        _clear_form()
        st.session_state["last_request"] = rid
        st.rerun()


# --------------------------------------------------------------------------- 2. status
STATUS_COLS = {"id": st.column_config.TextColumn("Request"), "type": st.column_config.TextColumn("Type"),
               "subject": st.column_config.TextColumn("Subject"), "entity": st.column_config.TextColumn("Entity"),
               "status": st.column_config.TextColumn("Status"), "stage": st.column_config.TextColumn("Stage"),
               "waiting_on": st.column_config.TextColumn("Waiting on"),
               "age_days": st.column_config.NumberColumn("Days open", format="%.1f"),
               "sap_code": st.column_config.TextColumn("SAP code")}


def my_requests():
    _page("Request status", "the My requests screen in the Power App, reading the Requests list")
    con = c.con()
    df = wf.requests_view(con)
    if df.empty:
        st.info("No requests yet.")
        return
    if c.role() == "Requestor":
        df = df[df.requestor == c.persona()]
        st.caption(f"Showing requests raised by {c.persona()}.")
    st.dataframe(df[list(STATUS_COLS)], hide_index=True, width="stretch", column_config=STATUS_COLS)
    if df.empty:
        return
    rid = c.select(st, "Open a request", df.id, index=len(df) - 1)
    req = df[df.id == rid].iloc[0]
    ap = wf.table(con, "approvals")
    ap = ap[ap.request_id == rid]
    left, right = st.columns(2)
    with left:
        st.markdown(f"##### {rid}: {req.subject}")
        st.markdown(f"**Status:** {req.status}. {req.stage}")
        for _, a in ap.iterrows():
            notes = [f"decided {a.decided_at}"] if a.decided_at else []
            notes += ["reminder sent"] if a.reminded_at else []
            notes += ["escalated"] if a.escalated_at else []
            st.markdown(f"- **{a.role}**, {a.person}: {_status(a.status)}"
                        + (f" ({', '.join(notes)})" if notes else ""))
        st.markdown("**Details**")
        _fields(json.loads(req.data))
        st.markdown("**Restricted fields** (as your role sees them)")
        _fields(wf.sensitive_for(con, rid, c.role()))
    with right:
        st.markdown("##### Timeline")
        log = wf.table(con, "log")
        for _, e in log[log.request_id == rid].iterrows():
            st.markdown(f"**{e.action}**, {e.actor}  \n:gray[{e.ts}] {e.detail}")


# --------------------------------------------------------------------------- 3. approvals
def approvals():
    _page("Approvals", "Power Automate 'Start and wait for an approval', as an actionable card in Teams or Outlook")
    con = c.con()
    if c.role() == "Requestor":
        st.info("Requestors don't approve. Switch the persona in the sidebar to an approver, such as Wei Jie, a BU "
                "Head or QA.")
        return
    ap = wf.query(con, "SELECT a.*, r.type, r.entity, r.country, r.requestor, r.data, r.dup_check, r.possible_match "
                     "FROM approvals a JOIN requests r ON r.id=a.request_id WHERE a.status='Pending' AND a.role=?",
                     params=(c.role(),))
    st.caption(f"Waiting for {c.role()}: {len(ap)}")
    if ap.empty:
        st.info("Nothing is waiting for you.")
    now = wf.now(con)
    for _, a in ap.iterrows():
        data = json.loads(a.data)
        waited = wf.days_waiting(pd.to_datetime(a.assigned_at).to_pydatetime(), now)
        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            h1.markdown(f"**Approval requested: {a.request_id}**  \n"
                        f"{a.type} for {a.entity} ({COUNTRIES.get(a.country, a.country)}), from "
                        f"{a.requestor.split(' (')[0]}")
            flags = (["reminder sent"] if a.reminded_at else []) + ([":red[escalated]"] if a.escalated_at else [])
            h2.markdown(f"Waiting **{waited}** day{'s' if waited != 1 else ''}"
                        + (f"  \n{', '.join(flags)}" if flags else ""))
            _fields(data)
            sens = wf.sensitive_for(con, a.request_id, c.role())
            if sens:
                st.markdown("**Restricted (Finance and MDM only):** "
                            + "; ".join(f"{k}: {v}" for k, v in sens.items()))
            st.caption(f"Duplicate check: {a.dup_check}" + (f", closest match {a.possible_match}"
                                                             if a.possible_match else ""))
            other = pd.read_sql("SELECT role, status FROM approvals WHERE request_id=? AND id<>?", con,
                                params=(a.request_id, int(a.id)))
            if not other.empty:
                st.caption("Other approvers: " + ", ".join(f"{r} ({s.lower()})" for r, s in other.values))
            comment = st.text_input("Comment (optional)", key=f"cmt_{a.id}")
            b1, b2, _ = st.columns([1, 1, 4])
            if b1.button("Approve", key=f"ok_{a.id}", type="primary", width="stretch"):
                wf.decide(con, int(a.id), "Approved", c.persona(), comment)
                st.rerun()
            if b2.button("Reject", key=f"no_{a.id}", width="stretch"):
                wf.decide(con, int(a.id), "Rejected", c.persona(), comment or "Rejected")
                st.rerun()


# --------------------------------------------------------------------------- 4. MDM
REVIEW_PAIR_COLS = {"record_a": st.column_config.TextColumn("Record A"),
                    "name_a": st.column_config.TextColumn("Name A"),
                    "record_b": st.column_config.TextColumn("Record B"),
                    "name_b": st.column_config.TextColumn("Name B"),
                    "country": st.column_config.TextColumn("Country"),
                    "score": st.column_config.NumberColumn("Similarity", format="%.0f"),
                    "reason": st.column_config.TextColumn("Why it was flagged")}


def mdm_queue():
    _page("MDM check", "a stage-2 approval for the MDM team, then Power Automate 'Create CSV table' into a "
                       "SharePoint folder")
    con = c.con()
    if c.role() != "MDM Analyst":
        st.info("This is Priya's screen. Switch the persona in the sidebar to Priya - MDM Analyst to act on it.")
    ap = wf.query(con, "SELECT a.*, r.type, r.data, r.dup_check, r.possible_match FROM approvals a "
                     "JOIN requests r ON r.id=a.request_id WHERE a.status='Pending' AND a.stage=2")
    st.markdown(f"##### Ready for the final check ({len(ap)})")
    for _, a in ap.iterrows():
        with st.container(border=True):
            st.markdown(f"**{a.request_id}**, {a.type}. All stage-1 approvers have approved; duplicate check: "
                        f"{a.dup_check}.")
            _fields(json.loads(a.data))
            if st.button("Approve and create the SAP import row", key=f"mdm_{a.id}", type="primary",
                         disabled=c.role() != "MDM Analyst"):
                wf.decide(con, int(a.id), "Approved", c.persona(), "Final check passed")
                st.rerun()

    st.markdown("##### SAP B1 import file")
    st.caption("Rows in the shape of SAP's Data Transfer Workbench templates (simplified). Priya loads the file into "
               "SAP B1 instead of retyping each record. Phase 3 replaces this with a direct Service Layer connection.")
    f = wf.sap_file(con)
    if f.empty:
        st.info("No records generated yet.")
    else:
        st.dataframe(f, hide_index=True, width="stretch")
        st.download_button("Download import file (CSV)", f.to_csv(index=False), "sap_b1_import.csv", "text/csv")

    st.markdown("##### Possible duplicates to review")
    q = c.data_quality()
    review = q["pairs"][q["pairs"].decision == "review"]
    st.caption("Look-alike records the bulk matcher would not merge on its own. A person decides.")
    st.dataframe(review[list(REVIEW_PAIR_COLS)], hide_index=True, width="stretch", column_config=REVIEW_PAIR_COLS)


# --------------------------------------------------------------------------- 5. log
LOG_COLS = {"request_id": "Request", "ts": "Time", "actor": "Who", "role": "Role", "action": "Action",
            "detail": "Detail", "field": "Field", "old_value": "Old value", "new_value": "New value"}


def audit_log():
    _page("Audit log", "the SharePoint ApprovalLog list, written only by the flows; users can read it")
    con = c.con()
    log = wf.table(con, "log").drop(columns=["id"])
    f1, f2 = st.columns(2)
    rid = c.select(f1, "Request", ["All"] + sorted(log.request_id.unique().tolist()))
    act = f2.multiselect("Action", sorted(log.action.unique()), filter_mode=None)
    if rid != "All":
        log = log[log.request_id == rid]
    if act:
        log = log[log.action.isin(act)]
    st.dataframe(log.rename(columns=LOG_COLS), hide_index=True, width="stretch")
    st.caption("Entries are only ever added, never edited. Restricted values are never written here, only the fact "
               "that they were stored or changed.")
    st.download_button("Export (CSV)", log.to_csv(index=False), "audit_log.csv", "text/csv")


# --------------------------------------------------------------------------- 6. rules
def rules():
    _page("Rules", "SharePoint lists the flows read each time they run: RoutingRules, RequiredFields, Roles, Aliases")
    con = c.con()
    st.markdown("The MDM team changes how requests work by editing rows in these tables. Adding a business unit, a "
                "required field or an approval step is a new row. For example, add a row to RoutingRules for a new "
                "regulatory check, or set a field to Conditional in RequiredFields.")
    is_mdm = c.role() == "MDM Analyst"

    with st.container(border=True):
        st.markdown("##### Onboard a new business unit")
        st.caption("Marcus's new BU joined and its first requests went to the wrong people for two weeks. Here Priya "
                   "sets it up in a minute: one row each in BusinessUnits and Roles, plus an optional extra approval "
                   "rule. The form and the routing pick it up on the next request.")
        f = st.columns([1, 2, 2])
        code = f[0].text_input("BU code", "LGD", max_chars=6).strip().upper()
        name = f[1].text_input("Business unit name", "LGD (molecular & genomics, new BU)")
        products = f[2].text_input("Products", "A")
        g = st.columns([2, 2, 2])
        head = g[0].text_input("BU Head (approver)", "LGD BU Head")
        email = g[1].text_input("BU Head email", "<teammate-2 SMU email>")
        tz = c.select(g[2], "BU Head time zone", ["Asia/Singapore", "Asia/Kuala_Lumpur", "Asia/Bangkok",
                                                  "Asia/Jakarta", "Asia/Ho_Chi_Minh"], index=4)
        qa = st.checkbox("Every item from this BU also needs Quality/Regulatory sign-off (new regulatory requirement)",
                         value=True)
        exists = code in set(wf.business_units(con).Title)
        if st.button("Add business unit", type="primary", disabled=not is_mdm or not code or exists):
            wf.add_business_unit(con, code, name, products, head, email, tz, qa)
            st.session_state["bu_added"] = (
                f"{code} is live. Switch to Marcus, open New request and pick {code} as the entity: the BU Head "
                f"card goes to {head}" + (", and every item also gets a Quality/Regulatory check." if qa else "."))
            st.rerun()  # refresh the button state and the rule tables below
        if msg := st.session_state.pop("bu_added", None):
            st.success(msg)
        elif exists:
            st.caption(f"{code} already exists. Reset the demo data in the sidebar to run this again.")
        elif not is_mdm:
            st.caption("Only the MDM team can add a business unit (switch the persona to Priya).")

    gaps = wf.routing_gaps(con)
    if gaps:
        st.warning("Rules check: " + "; ".join(gaps) + ". Requests would wait on nobody until this is fixed in Roles.")
    else:
        st.caption("Rules check: every active business unit has someone for every approval step.")

    tabs = st.tabs(wf.RULE_TABLES)
    for tab, name in zip(tabs, wf.RULE_TABLES):
        with tab:
            df = wf.table(con, name)
            edited = st.data_editor(df, num_rows="dynamic", width="stretch", key=f"ed_{name}",
                                    hide_index=True)
            if st.button(f"Save {name}", key=f"save_{name}", disabled=c.role() != "MDM Analyst"):
                wf.save_rules(con, name, edited)
                st.success(f"{name} saved. The next request uses the new rule, and the change is in the audit log.")
            if c.role() != "MDM Analyst":
                st.caption("Only the MDM team can save rule changes (switch the persona to Priya).")
