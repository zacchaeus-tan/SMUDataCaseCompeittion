"""The request workflow pages. Each mirrors a screen of the Power App or what a Power Automate flow sends to Teams;
the logic is in onerecord/workflow.py. Everyone shares one demo database."""
import json

import pandas as pd
import streamlit as st

from onerecord import workflow as wf

from . import common as c

SECTION = "Requests"
SOURCE = "Shared demo data"
STATUS_COLOR = {"Pending approval": "orange", "Resubmitted": "orange", "Changes requested": "violet",
                "Ready for SAP import": "blue", "Created in SAP": "green", "Rejected": "red", "Closed": "gray"}
FORM_KEYS = ("req_type", "req_entity", "req_notsame", "req_reason", "req_reply", "edit_id")


def _status(s):
    return f":{STATUS_COLOR.get(s, 'gray')}[**{s}**]"


def _labels(con, rtype):
    return dict(zip(wf.fields(con, rtype).FieldName, wf.fields(con, rtype).DisplayLabel))


def _details(con, req, u):
    """The request's values as Field / Value rows. Sensitive values only for the roles allowed to see them
    (RequiredFields.VisibleToRoles) and for the requestor on their own request, as the restricted list allows."""
    labels = _labels(con, req["type"])
    rows = [(labels.get(k, k), v) for k, v in req["values"].items() if str(v).strip()]
    if req["sensitive"]:
        allowed = wf.can_see_sensitive(con, req["type"], u["wf_role"]) or req["requestor"] == u["name"]
        rows += [(labels.get(k, k) + " 🔒", v if allowed else "Restricted: Finance and MDM only")
                 for k, v in req["sensitive"].items()]
    st.dataframe(pd.DataFrame(rows, columns=["Field", "Value"]), hide_index=True, width="stretch",
                 height=c.table_height(len(rows)))


def _teams(con, u, limit=8):
    msgs = wf.messages_for(con, u["wf_role"], u["name"]).head(limit)
    with st.expander(f"Teams messages for {u['name']} ({len(msgs)})", icon=":material/chat:"):
        if msgs.empty:
            st.caption("No messages yet.")
        for m in msgs.itertuples():
            st.markdown(f"**{m.ts}** · {m.text}")


# --------------------------------------------------------------------------- New request (and Edit and resubmit)
def _widget(con, rtype, f, key, col):
    help_text = f.HelpText or None
    label = f.DisplayLabel + (" 🔒" if f.Sensitive == "Yes" else "")
    if f.FieldType == "Yes/No":
        if key not in st.session_state:
            st.session_state[key] = "No"
        return col.segmented_control(label, ["Yes", "No"], key=key, help=help_text) or ""
    if f.FieldType == "Choice":
        opts = wf.choices(con, f.FieldName)
        if st.session_state.get(key) not in opts:
            st.session_state.pop(key, None)
        return c.select(col, label, opts, index=None, key=key, placeholder="Choose", help=help_text) or ""
    return col.text_input(label, key=key, help=help_text)


def new_request():
    con, u = c.wf_con(), c.user()
    editing = st.session_state.get("edit_id")
    c.header(SECTION, f"Edit and resubmit {editing}" if editing else "Raise a master-data request", SOURCE)
    done = st.session_state.pop("submitted", None)
    if done:
        st.success(done, icon=":material/check_circle:")
    if editing:
        req = wf.request(con, editing)
        st.info(f"**{editing}** was sent back. Make the changes asked for, or reply to the approver. Only the "
                f"approver who asked sees it again; the others carry on.", icon=":material/undo:")
    else:
        st.caption("Customer, item, vendor or cost-centre setup. Only the fields that apply are shown, formats and "
                   "duplicates are checked while you type, and you see who will approve before you submit.")
    bus = wf.business_units(con)
    top = st.columns(2)
    rtype = c.select(top[0], "Request type", wf.TYPES, key="req_type", disabled=bool(editing))
    entity = c.select(top[1], "Business entity", list(bus.Title), index=None, key="req_entity", placeholder="Choose",
                      format_func=dict(zip(bus.Title, bus.BusinessUnitName)).get, disabled=bool(editing),
                      help="Which Lives Group business this is for")

    values = {}
    for _ in range(2):  # a choice can reveal a field (e.g. Regulated = Yes adds the licence no.): settle in two passes
        shown = wf.visible_fields(con, rtype, values)
        values = {f.FieldName: str(st.session_state.get(f"f_{rtype}_{f.FieldName}", "") or "")
                  for f in shown.itertuples()}
    with st.container(key="card-reqform"):
        st.markdown(f"##### {rtype} details")
        cols = st.columns(2)
        for i, f in enumerate(shown.itertuples()):
            values[f.FieldName] = _widget(con, rtype, f, f"f_{rtype}_{f.FieldName}", cols[i % 2])
        check = wf.check_form(con, rtype, entity, values, st.session_state.get("req_notsame", False),
                              st.session_state.get("req_reason", ""), editing)
        for fname, problem in check["problems"].items():
            st.markdown(f":red[**{_labels(con, rtype)[fname]}** {problem}]")

    dup = check["dup"]
    if dup["status"] != "Clear":
        (st.error if dup["status"] == "Blocked" else st.warning)(
            f"**{dup['status']}.** {dup['message']}", icon=":material/content_copy:")
        st.toggle(f"Not the same: this is a different {rtype.lower()}", key="req_notsame")
        if st.session_state.get("req_notsame"):
            st.text_area("Why is it different? (at least 10 characters; approvers see this)", key="req_reason")
    elif any(values.get(f) for f in ("CustomerName", "ItemDescription", "VendorName", "Department")):
        st.success("No duplicate found in SAP or in requests waiting for approval.", icon=":material/verified:")

    _who_approves(check, entity)
    if editing:
        st.text_input("Reply to the approver (optional)", key="req_reply")
        note = wf.change_note(con, rtype, {**req["values"], **req["sensitive"]}, values)
        st.caption(f"Your changes: {note}")
        if note == "No fields changed." and not st.session_state.get("req_reply", "").strip():
            check["todo"].append("Make the changes asked for, or reply to the approver.")
            check["ok"] = False
    label = "Resubmit" if editing else "Submit request"
    if check["ok"]:
        st.caption("Ready to " + ("resubmit." if editing else "submit."))
    else:
        st.caption(" ".join(check["todo"]))
    left, right = st.columns([1, 4])
    if left.button(label, type="primary", disabled=not check["ok"], width="stretch"):
        if editing:
            wf.resubmit(con, editing, values, u["name"], st.session_state.get("req_reply", ""))
            msg = f"{editing} resubmitted. The approvers who asked for changes have it again."
        else:
            rid = wf.submit(con, rtype, entity, u["name"], values, dup, st.session_state.get("req_reason", ""))
            msg = f"{rid} submitted. Approval cards went to Teams; follow it in My requests."
        _clear_form()
        st.session_state["submitted"] = msg
        st.rerun()
    if editing and right.button("Cancel editing"):
        _clear_form()
        st.rerun()


def _who_approves(check, entity):
    with st.container(key="card-approvers"):
        st.markdown("##### Who will approve")
        if not entity:
            st.caption("Choose a business entity to see who will approve.")
            return
        s1 = [s for s in check["steps"] if s[0] == 1]
        s2 = [s for s in check["steps"] if s[0] == 2]
        name = lambda s: f"**{s[1]}** ({s[2] or 'nobody set up: the MDM team approves instead'})"
        st.markdown(", ".join(map(name, s1)) + (", all at the same time" if len(s1) > 1 else "")
                    + ("; then " if s1 and s2 else "") + ", ".join(map(name, s2)) + ".")


def _clear_form():
    for k in list(st.session_state):
        if k.startswith("f_") or k in FORM_KEYS:
            del st.session_state[k]


def _start_edit(con, rid):
    """Edit and resubmit: open the form with the request's answers filled in."""
    _clear_form()
    req = wf.request(con, rid)
    st.session_state.update(edit_id=rid, req_type=req["type"], req_entity=req["entity"])
    for k, v in {**req["values"], **req["sensitive"]}.items():
        st.session_state[f"f_{req['type']}_{k}"] = v
    st.switch_page(c.PAGES["new-request"])


# --------------------------------------------------------------------------- My requests
def my_requests():
    con, u = c.wf_con(), c.user()
    c.header(SECTION, "Where my requests stand", SOURCE)
    df = wf.requests_view(con)
    mdm = u["wf_role"] == "MDM Analyst"
    show_all = mdm and st.toggle("Show everyone's requests", value=True)
    mine = df if show_all or df.empty else df[df.requestor == u["name"]]
    _teams(con, u)
    if mine.empty:
        st.info("No requests yet. Raise one on New request.", icon=":material/inbox:")
        return
    st.caption("Select a request to see who it's waiting on and its timeline.")
    shown = mine[["id", "type", "name", "entity", "requestor", "status", "waiting_on", "days_open", "sap_code"]]
    pick = st.dataframe(shown, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
                        key="myreq_table", height=c.table_height(len(shown)), column_config={
                            "id": "Request", "type": "Type", "name": "Name", "entity": "Entity",
                            "requestor": "Requestor", "status": "Status", "waiting_on": "Waiting on",
                            "days_open": st.column_config.NumberColumn("Days open"), "sap_code": "SAP code"})
    rows = [r for r in pick.selection.rows if r < len(shown)]
    rid = shown.iloc[rows[0]].id if rows else shown.iloc[0].id
    _request_detail(con, u, rid)


def _request_detail(con, u, rid):
    req = wf.request(con, rid)
    v = wf.requests_view(con).set_index("id").loc[rid]
    with st.container(key="card-reqdetail"):
        st.markdown(f"#### {rid} · {v['name']}")
        st.markdown(f"{_status(req['status'])} · {req['stage']} · {v.days_open} days open"
                    + (f" · SAP code **{req['sap_code']}**" if req["sap_code"] else ""))
        if v.waiting_on:
            st.markdown(f"**Waiting on:** {v.waiting_on}")
        if req["status"] == "Changes requested" and req["requestor"] == u["name"]:
            ask = wf.query(con, "SELECT * FROM log WHERE request_id=? AND action='Request changes' ORDER BY id DESC",
                           (rid,)).iloc[0]
            st.warning(f"**{ask.role} asked for changes:** {ask.detail}", icon=":material/undo:")
            if st.button("Edit and resubmit", type="primary"):
                _start_edit(con, rid)
        if req["status"] == "Ready for SAP import":
            _sap_actions(con, u, req)
        left, right = st.columns(2)
        with left:
            st.markdown("**Submitted details**")
            _details(con, req, u)
            if req["dup_status"] and req["dup_status"] != "Clear":
                st.caption(f"Duplicate check: {req['dup_status']} ({req['dup_record']}). Reason given: "
                           f"{req['dup_reason']}")
            if req["change_note"]:
                st.caption(f"Last changes: {req['change_note']}")
        with right:
            st.markdown("**Timeline**")
            log = wf.query(con, "SELECT ts, action, actor, role, detail FROM log WHERE request_id=? ORDER BY id", (rid,))
            st.dataframe(log, hide_index=True, width="stretch", height=c.table_height(min(len(log), 14)),
                         column_config={"ts": "When", "action": "What", "actor": "Who", "role": "Role",
                                        "detail": "Detail"})


def _sap_actions(con, u, req):
    f = con.execute("SELECT filename, content FROM sap_files WHERE request_id=?", (req["id"],)).fetchone()
    if u["wf_role"] != "MDM Analyst":
        st.info(f"Approved. The MDM team is importing it into SAP B1 as **{req['sap_code']}**.", icon=":material/sync:")
        return
    st.info("Approved. Import the DTW file into SAP B1, then mark it as created.", icon=":material/upload_file:")
    a, b, d = st.columns([1.4, 1, 1], vertical_alignment="bottom")
    a.download_button(f"Download {f['filename']}", f["content"], file_name=f["filename"], mime="text/plain",
                      key=f"dtw_{req['id']}")
    code = b.text_input("SAP code given", value=req["sap_code"], key=f"code_{req['id']}",
                        help="Change it if SAP gave a different code")
    if d.button("Mark as created in SAP", type="primary", key=f"made_{req['id']}"):
        wf.mark_created(con, req["id"], code.strip() or req["sap_code"], u["name"])
        st.toast(f"{req['id']} is live in SAP as {code}")
        st.rerun()


# --------------------------------------------------------------------------- Approvals (the Teams cards)
def approvals():
    con, u = c.wf_con(), c.user()
    role = u["wf_role"]
    cards = wf.approvals_for(con, role)
    c.header(SECTION, f"{len(cards)} approval{'s' if len(cards) != 1 else ''} waiting for {u['name']}", SOURCE)
    st.caption("These are the approval cards Teams shows you. Every first-stage approver gets theirs at the same "
               "time; the MDM final check comes last.")
    _teams(con, u)
    if role == "MDM Analyst":
        ready = wf.query(con, "SELECT id FROM requests WHERE status='Ready for SAP import' ORDER BY id")
        for rid in ready.id:
            with st.container(key=f"card-sap-{rid}"):
                req = wf.request(con, rid)
                st.markdown(f"#### {rid} · import into SAP B1")
                _sap_actions(con, u, req)
    if cards.empty:
        st.success("Nothing waiting for you.", icon=":material/task_alt:")
    for a in cards.itertuples():
        req = wf.request(con, a.request_id)
        with st.container(key=f"card-appr-{a.id}"):
            name = req["values"].get(wf.NAME_FIELD[a.type], "")
            st.markdown(f"#### {a.request_id} from {a.requestor}: {a.type} · {name}")
            waited = (wf.now(con) - pd.Timestamp(a.assigned_at)).days
            extra = []
            if a.escalated_queue == role and a.queue != role:
                extra.append(f"escalated to you: {a.person} hasn't answered")
            elif a.queue != a.role:
                extra.append(f"no {a.role} is set up for {a.entity}, so you approve in their place")
            st.markdown(f"**{a.role}** for **{a.entity}** · stage {a.stage}"
                        + (f", round {a.round}" if a.round > 1 else "") + f" · waiting {waited} days"
                        + "".join(f" · :orange[{e}]" for e in extra))
            if req["dup_status"] != "Clear":
                st.warning(f"Duplicate check said **{req['dup_status']}** ({req['dup_record']}). The requestor says: "
                           f"{req['dup_reason']}", icon=":material/warning:")
            if req["change_note"]:
                st.caption(f"Changed since last time: {req['change_note']}")
            _details(con, req, u)
            with st.form(f"decide_{a.id}", border=False):
                comment = st.text_input("Comment (needed to reject or ask for changes)", key=f"cm_{a.id}")
                b1, b2, b3, _ = st.columns([1, 1.3, 1, 2])
                pressed = [d for d, b in (("Approve", b1.form_submit_button("Approve", type="primary")),
                                          ("Request changes", b2.form_submit_button("Request changes")),
                                          ("Reject", b3.form_submit_button("Reject"))) if b]
            if pressed:
                if pressed[0] != "Approve" and len(comment.strip()) < 5:
                    st.error("Say what's wrong or what to change.")
                else:
                    wf.decide(con, a.id, pressed[0], u["name"], comment.strip())
                    st.toast(f"{a.request_id}: {pressed[0]}")
                    st.rerun()


# --------------------------------------------------------------------------- Audit log
def audit_log():
    con = c.wf_con()
    c.header(SECTION, "Audit log: every step, only ever added to", SOURCE)
    log = wf.query(con, "SELECT ts, request_id, action, actor, role, detail FROM log ORDER BY id DESC")
    pick = st.multiselect("Request", sorted(set(log.request_id) - {""}), placeholder="All requests")
    if pick:
        log = log[log.request_id.isin(pick)]
    st.dataframe(log, hide_index=True, width="stretch", column_config={
        "ts": "When", "request_id": "Request", "action": "What", "actor": "Who", "role": "Role", "detail": "Detail"})
    st.caption("Sensitive values are never written to the log.")


# --------------------------------------------------------------------------- Rules
def _when(field, value, labels):
    if not field:
        return "always"
    return f"only when {labels.get(field, field)} is {' or '.join(v.strip() for v in value.replace(',', ';').split(';'))}"


def rules():
    con, u = c.wf_con(), c.user()
    mdm = u["wf_role"] == "MDM Analyst"
    c.header(SECTION, "Approval rules, without IT", SOURCE)
    st.caption("The form and the approval flow read these lists on every request, so a change applies to the next "
               "one. " + ("You can change them below." if mdm else "View only: the MDM team changes the rules."))
    gaps = wf.routing_gaps(con)
    if gaps:
        st.warning("**Needs attention:** " + "; ".join(gaps) + ". Requests for these go to MDM until someone is "
                   "added.", icon=":material/person_off:")
    bus = wf.business_units(con)
    rules_df = wf.query(con, "SELECT * FROM RoutingRules WHERE Active='Yes'")
    for tab, rtype in zip(st.tabs(wf.TYPES), wf.TYPES):
        with tab:
            f = wf.fields(con, rtype)
            labels = dict(zip(f.FieldName, f.DisplayLabel))
            left, right = st.columns(2)
            with left, st.container(key=f"card-rf-{rtype.replace(' ', '')}"):
                st.markdown("##### What the form asks for")
                for r in f.itertuples():
                    st.markdown(f"- **{r.DisplayLabel}**{' 🔒' if r.Sensitive == 'Yes' else ''}: "
                                f"{_when(r.ConditionField, r.ConditionValue, labels) if r.Required == 'Conditional' else 'always'}")
            with right, st.container(key=f"card-rr-{rtype.replace(' ', '')}"):
                st.markdown("##### Who approves")
                biz = c.select(st, "Show for", list(bus.Title), key=f"rules_bu_{rtype}",
                               format_func=dict(zip(bus.Title, bus.BusinessUnitName)).get)
                mine = rules_df[rules_df.RequestType.isin([rtype, "Any"]) & rules_df.Entity.isin([biz, "Any"])]
                for stage, title in (("1", "Step 1, all at the same time"), ("2", "Then")):
                    st.markdown(f"**{title}**")
                    for r in mine[mine.Stage == stage].itertuples():
                        p = wf.person_for(con, r.ApproverRole, biz)
                        st.markdown(f"- **{r.ApproverRole}** ({p.PersonName if p is not None else ':red[nobody set up]'}), "
                                    f"{_when(r.ConditionField, r.ConditionValue, labels)}; reminder after {r.SLADays} day{'' if r.SLADays == '1' else 's'}")
    if mdm:
        _rule_editor(con, u)


def _rule_editor(con, u):
    st.markdown("#### Change the rules")
    with st.expander("Add a business unit", icon=":material/add_business:"):
        with st.form("add_bu"):
            a, b = st.columns(2)
            code = a.text_input("Code (e.g. LGD)").strip().upper()
            name = b.text_input("Name")
            products = a.text_input("Product lines it sells (e.g. A, C)")
            head = b.text_input("BU Head (name)")
            tz = c.select(a, "BU Head's time zone", ["Asia/Singapore", "Asia/Kuala_Lumpur", "Asia/Bangkok",
                                                     "Asia/Jakarta", "Asia/Ho_Chi_Minh"])
            if st.form_submit_button("Add business unit", type="primary"):
                if not code or not name:
                    st.error("Enter a code and a name.")
                elif code in set(wf.table(con, "BusinessUnits").Title):
                    st.error(f"{code} already exists.")
                else:
                    wf.add_business_unit(con, code, name, products, head.strip(), tz, u["name"])
                    st.toast(f"{code} added")
                    st.rerun()
    lists = {"RoutingRules": "Approval steps", "RequiredFields": "Form fields", "Roles": "People",
             "BusinessUnits": "Business units", "ChoiceOptions": "Dropdown options", "Aliases": "Known names"}
    for tab, (name, label) in zip(st.tabs(list(lists.values())), lists.items()):
        with tab:
            edited = st.data_editor(wf.table(con, name), num_rows="dynamic", hide_index=True, width="stretch",
                                    key=f"edit_{name}")
            if st.button(f"Save {label.lower()}", key=f"save_{name}", type="primary"):
                wf.save_table(con, name, edited, u["name"])
                st.toast(f"{label} saved")
                st.rerun()


# --------------------------------------------------------------------------- sidebar demo controls
def demo_controls():
    """Fast-forward the clock to see reminders and escalation fire, or start the shared demo over."""
    con = c.wf_con()
    with st.expander("Demo clock", icon=":material/schedule:"):
        st.caption(f"Simulated time: {wf.now(con):%a %d %b %Y, %H:%M}")
        a, b = st.columns(2)
        days = 1 if a.button("+1 day", width="stretch") else 3 if b.button("+3 days", width="stretch") else 0
        if days:
            for e in wf.advance_clock(con, days) or ["No reminders due."]:
                st.toast(e)
        if st.button("Reset demo data", width="stretch"):
            wf.reset().close()
            _clear_form()
            st.toast("Demo data reset for everyone")
            st.rerun()
        st.caption("Everyone using this app shares the demo data.")
