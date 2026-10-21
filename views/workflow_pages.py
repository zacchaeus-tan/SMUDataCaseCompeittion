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
STATUS_ICON = {"Approved": "✅", "Pending": "⏳", "Rejected": "❌", "Cancelled": "➖"}


def _badge(where):
    st.caption(f"🔷 In production: **{where}**")


# --------------------------------------------------------------------------- 1. form
def _clear_form():
    """Reset every form widget (top selectors, all detail fields of every request type, the duplicate tick-box)."""
    for k in list(st.session_state):
        if k.startswith(("req_", "Customer_", "Item_", "Vendor_", "Cost Center_", "dup_ok")):
            del st.session_state[k]


def new_request():
    st.title("New master-data request")
    _badge("Power Apps canvas app in a Teams tab, saving to the SharePoint Requests list")
    rid = st.session_state.pop("last_request", None)  # show the confirmation once, on a blank form
    if rid:
        st.success(f"Submitted **{rid}** — approval cards are on their way in Teams. Track it under *Request status*.")
    con = c.con()
    d = c.raw()

    top = st.columns(3)
    rtype = top[0].selectbox("What do you need?", ["Customer", "Item", "Vendor", "Cost Center"], key="req_type")
    entity = top[1].selectbox("Business entity", ["SPD", "QTS", "QTG"], key="req_entity")
    country = top[2].selectbox("Country", list(COUNTRIES), format_func=lambda k: f"{k} · {COUNTRIES[k]}",
                               key="req_country")

    fields = wf.form_fields(con, rtype)
    values = {"Country": country} if rtype in ("Customer",) else {}
    st.markdown("#### Details")
    st.caption("Fields come from the **RequiredFields** rule table. Conditional fields appear only when they apply.")
    cols = st.columns(2)
    shown = 0
    for _, f in fields.iterrows():
        if f.FieldName == "Country" and rtype == "Customer":
            continue
        if not wf.field_visible(f, values):
            continue
        col = cols[shown % 2]
        shown += 1
        label = f"{f.DisplayLabel}{' 🔒' if f.Sensitive == 'Yes' else ''}"
        key = f"{rtype}_{f.FieldName}"
        help_ = (f.HelpText or None)
        if f.FieldType == "Yes/No":
            values[f.FieldName] = col.selectbox(label, ["", "Yes", "No"], key=key, help=help_)
        elif f.FieldType == "Choice" and f.FieldName in CHOICES:
            values[f.FieldName] = col.selectbox(label, [""] + CHOICES[f.FieldName], key=key, help=help_)
        else:
            values[f.FieldName] = col.text_input(label, key=key, help=help_)
    if (fields.Sensitive == "Yes").any():
        st.caption("🔒 Sensitive: saved to a separate restricted list that only Finance and MDM can open.")

    st.markdown("#### Checks before anything reaches an approver")
    dup = wf.duplicate_check(con, rtype, values, d["customers"], d["items"])
    missing = wf.missing_fields(con, rtype, values)
    a, b = st.columns(2)
    with a:
        if missing:
            st.warning("**Still needed:** " + ", ".join(missing))
        else:
            st.success("All required fields complete")
    with b:
        name_field = {"Customer": "CustomerName", "Item": "ItemDescription"}.get(rtype)
        if name_field and not values.get(name_field):
            st.info("**Duplicate check** runs as soon as you enter the name.")
        else:
            {"Blocked": st.error, "Possible match": st.warning, "Clear": st.success}[dup[0]](
                f"**Duplicate check · {dup[0]}** — {dup[2]}")
    confirm = True
    if dup[0] == "Possible match":
        confirm = st.checkbox(f"I checked {dup[1]} — this really is a different record", key="dup_ok")

    rules = pd.read_sql("SELECT * FROM RoutingRules WHERE Active='Yes'", con)
    rules = rules[rules.RequestType.isin([rtype, "Any"])]
    who = [r.ApproverRole for _, r in rules[rules.Stage == "1"].iterrows()
           if not r.ConditionField or str(values.get(r.ConditionField, "")) == r.ConditionValue]
    st.info(f"**Will be routed in parallel to:** {', '.join(who)} → then MDM final check")

    can_submit = not missing and dup[0] != "Blocked" and confirm and c.role() == "Requestor"
    if c.role() != "Requestor":
        st.caption("Switch the sidebar persona to a requestor (Amy or Marcus) to submit.")
    if st.button("Submit request", type="primary", disabled=not can_submit):
        rid = wf.submit(con, rtype, entity, country, c.persona(), {k: v for k, v in values.items() if v}, dup)
        _clear_form()
        st.session_state["last_request"] = rid
        st.rerun()


# --------------------------------------------------------------------------- 2. status
def my_requests():
    st.title("Request status")
    _badge("'My requests' screen in the Power App, reading the Requests list")
    con = c.con()
    df = wf.requests_view(con)
    if df.empty:
        st.info("No requests yet.")
        return
    if c.role() == "Requestor":
        df = df[df.requestor == c.persona()]
        st.caption(f"Showing requests raised by **{c.persona()}**.")
    show = df[["id", "type", "subject", "entity", "status", "stage", "waiting_on", "age_days", "sap_code"]]
    st.dataframe(show.rename(columns={"age_days": "days open"}), hide_index=True, width="stretch")
    if df.empty:
        return
    rid = st.selectbox("Open a request", df.id, index=len(df) - 1)
    req = df[df.id == rid].iloc[0]
    ap = wf.table(con, "approvals")
    ap = ap[ap.request_id == rid]
    left, right = st.columns([1, 1])
    with left:
        st.markdown(f"#### {rid} · {req.subject}")
        st.markdown(f"**Status:** {req.status} — {req.stage}")
        for _, a in ap.iterrows():
            extra = " · reminded" if a.reminded_at else ""
            extra += " · escalated" if a.escalated_at else ""
            st.markdown(f"{STATUS_ICON.get(a.status, '•')} **{a.role}** — {a.person} · {a.status}"
                        f"{' at ' + a.decided_at if a.decided_at else ''}{extra}")
        st.markdown("**Details**")
        st.json(json.loads(req.data), expanded=False)
        st.markdown("**Sensitive fields** (as seen by your role)")
        st.json(wf.sensitive_for(con, rid, c.role()), expanded=True)
    with right:
        st.markdown("#### Timeline")
        log = wf.table(con, "log")
        for _, e in log[log.request_id == rid].iterrows():
            st.markdown(f"`{e.ts}` **{e.action}** · {e.actor}  \n{e.detail}")


# --------------------------------------------------------------------------- 3. approvals
def approvals():
    st.title("Approvals")
    _badge("Power Automate 'Start and wait for an approval' — actionable card in Teams / Outlook")
    con = c.con()
    if c.role() == "Requestor":
        st.info("Requestors don't approve. Switch the sidebar persona to an approver (e.g. Wei Jie, BU Head, QA).")
        return
    ap = wf.query(con, "SELECT a.*, r.type, r.entity, r.country, r.requestor, r.data, r.dup_check, r.possible_match "
                     "FROM approvals a JOIN requests r ON r.id=a.request_id WHERE a.status='Pending' AND a.role=?",
                     params=(c.role(),))
    st.caption(f"Pending for **{c.role()}**: {len(ap)}")
    if ap.empty:
        st.success("Nothing waiting for you. 🎉")
    now = wf.now(con)
    for _, a in ap.iterrows():
        data = json.loads(a.data)
        waited = wf.business_days(pd.to_datetime(a.assigned_at).to_pydatetime(), now)
        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            h1.markdown(f"**🟣 OneRecord · Approval requested** — {a.request_id}  \n"
                        f"{a.type} for **{a.entity}** ({a.country}) · from {a.requestor.split(' (')[0]}")
            h2.markdown(f"⏱️ waiting **{waited:.0f}** business day(s)" + ("  \n🔔 reminded" if a.reminded_at else "")
                        + ("  \n⚠️ escalated" if a.escalated_at else ""))
            st.table(pd.DataFrame({"Field": list(data), "Value": [str(v) for v in data.values()]}).set_index("Field"))
            sens = wf.sensitive_for(con, a.request_id, c.role())
            if sens:
                st.markdown("**Sensitive (Finance/MDM only):** " + " · ".join(f"{k}: {v}" for k, v in sens.items()))
            st.caption(f"Duplicate check: {a.dup_check}{' → ' + a.possible_match if a.possible_match else ''}")
            other = pd.read_sql("SELECT role, status FROM approvals WHERE request_id=? AND id<>?", con,
                                params=(a.request_id, int(a.id)))
            st.caption("Other approvers (in parallel): " + " · ".join(f"{STATUS_ICON.get(s, '')} {r}" for r, s in other.values))
            comment = st.text_input("Comment (optional)", key=f"cmt_{a.id}")
            b1, b2, _ = st.columns([1, 1, 4])
            if b1.button("Approve", key=f"ok_{a.id}", type="primary"):
                wf.decide(con, int(a.id), "Approved", c.persona(), comment)
                st.rerun()
            if b2.button("Reject", key=f"no_{a.id}"):
                wf.decide(con, int(a.id), "Rejected", c.persona(), comment or "Rejected")
                st.rerun()


# --------------------------------------------------------------------------- 4. MDM
def mdm_queue():
    st.title("MDM final check & SAP import file")
    _badge("Stage-2 approval for the MDM team + Power Automate 'Create CSV table' → SharePoint folder")
    con = c.con()
    if c.role() != "MDM Analyst":
        st.info("This is Priya's screen — switch the sidebar persona to **Priya - MDM Analyst** to act on it.")
    ap = wf.query(con, "SELECT a.*, r.type, r.data, r.dup_check, r.possible_match FROM approvals a "
                     "JOIN requests r ON r.id=a.request_id WHERE a.status='Pending' AND a.stage=2")
    st.markdown(f"#### Ready for final check ({len(ap)})")
    for _, a in ap.iterrows():
        with st.container(border=True):
            st.markdown(f"**{a.request_id}** · {a.type} · all stage-1 checks approved · duplicate check: {a.dup_check}")
            st.json(json.loads(a.data), expanded=False)
            if st.button("Approve & generate SAP import row", key=f"mdm_{a.id}", type="primary",
                         disabled=c.role() != "MDM Analyst"):
                wf.decide(con, int(a.id), "Approved", c.persona(), "Final check passed")
                st.rerun()

    st.markdown("#### SAP B1 import file")
    st.caption("Rows in the shape of SAP's Data Transfer Workbench templates (simplified). Priya loads the file "
               "into SAP B1 — no retyping. Phase 3 replaces this with a direct Service Layer integration.")
    f = wf.sap_file(con)
    if f.empty:
        st.info("No records generated yet.")
    else:
        st.dataframe(f, hide_index=True, width="stretch")
        st.download_button("Download import file (CSV)", f.to_csv(index=False), "sap_b1_import.csv", "text/csv")

    st.markdown("#### Possible duplicates for review (from the bulk matcher)")
    q = c.data_quality()
    review = q["pairs"][q["pairs"].decision == "review"]
    st.caption("Look-alike records the engine would not merge on its own. A person decides.")
    st.dataframe(review[["record_a", "name_a", "record_b", "name_b", "country", "score", "reason"]],
                 hide_index=True, width="stretch")


# --------------------------------------------------------------------------- 5. log
def audit_log():
    st.title("Audit log")
    _badge("SharePoint ApprovalLog list — written only by the flow; users have read access")
    con = c.con()
    log = wf.table(con, "log").drop(columns=["id"])
    f1, f2 = st.columns(2)
    rid = f1.selectbox("Request", ["All"] + sorted(log.request_id.unique().tolist()))
    act = f2.multiselect("Action", sorted(log.action.unique()))
    if rid != "All":
        log = log[log.request_id == rid]
    if act:
        log = log[log.action.isin(act)]
    st.dataframe(log, hide_index=True, width="stretch")
    st.caption("Entries are only ever added, never edited. Sensitive values are never written here — only the "
               "fact that they were stored or changed.")
    st.download_button("Export (CSV)", log.to_csv(index=False), "audit_log.csv", "text/csv")


# --------------------------------------------------------------------------- 6. rules
def rules():
    st.title("Rules — changed by the MDM team, not IT")
    _badge("SharePoint lists the flows read at run time: RoutingRules, RequiredFields, Roles, Aliases")
    con = c.con()
    st.markdown("Adding a business unit, a required field or an approval step = **editing a row here**. "
                "Example: add a row to *RoutingRules* for a new regulatory check, or set a field to *Conditional*.")
    tabs = st.tabs(wf.RULE_TABLES)
    for tab, name in zip(tabs, wf.RULE_TABLES):
        with tab:
            df = wf.table(con, name)
            edited = st.data_editor(df, num_rows="dynamic", width="stretch", key=f"ed_{name}",
                                    hide_index=True)
            if st.button(f"Save {name}", key=f"save_{name}", disabled=c.role() != "MDM Analyst"):
                wf.save_rules(con, name, edited)
                st.success(f"{name} saved — the next request uses the new rule. Change is in the audit log.")
            if c.role() != "MDM Analyst":
                st.caption("Only the MDM team can save rule changes (switch persona to Priya).")
