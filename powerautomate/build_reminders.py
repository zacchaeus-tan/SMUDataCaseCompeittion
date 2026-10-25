"""Build the OneRecord reminder & escalation flows as importable packages (Import > Import Package (Legacy)).

Usage: python3 powerautomate/build_reminders.py
  -> OneRecord-Reminders.zip         hourly; messages each approver at 9 AM in their own time zone (Roles.TimeZone)
  -> OneRecord-Reminders-SendNow.zip  run by hand (for demos); skips the 9 AM check

An approval is open when ApprovalLog has an "Assigned" row (written by the Route and approve flow) that has no
decision yet. An approver can be asked again after "Request changes", so each Assigned row says its round
("Stage 1, round 2"): round N is open while the role has N - 1 decisions (Approve / Reject / Request changes / Cancelled) on
that request. An approver who asked for changes is therefore not chased while the requestor edits.
Days are calendar days since the Assigned row. Only requests that are still open (Pending approval, Changes requested,
Resubmitted) are chased: once a request is rejected, cancelled or closed, its other cards are left alone.
  * days >= SLADays: remind the approver, log "Reminder sent"
  * if the card was escalated (the Route and approve flow re-sends an unanswered stage-1 card to the approver and their
    EscalateTo, and logs "Escalated" with the same "Stage N, round R" as the Assigned row), remind the EscalateTo too
SLADays comes from the matching RoutingRules row.

It also nudges the MDM Analyst at 9 AM (their time) about every request that has been "Ready for SAP import" for a
day or more, until it is marked as created in SAP.
"""
from pathlib import Path

from pkg import LOG, REQ, ROLE, RULE, after, app_link, condition, definition, log_row, sp, teams_chat, write_package

HERE = Path(__file__).parent
APIS = ["shared_sharepointonline", "shared_teams"]

# Roles.TimeZone holds IANA names; Power Automate's convertFromUtc needs Windows time zone ids.
TIME_ZONES = {
    "Asia/Singapore": "Singapore Standard Time",
    "Asia/Kuala_Lumpur": "Singapore Standard Time",
    "Asia/Bangkok": "SE Asia Standard Time",
    "Asia/Jakarta": "SE Asia Standard Time",
    "Asia/Ho_Chi_Minh": "SE Asia Standard Time",
}
NEVER = 999999  # stands in for a blank SLADays
OPEN = "createArray('Pending approval', 'Changes requested', 'Resubmitted')"


def build(at_9am_only):
    loop = "Chase_each_open_approval"
    row = f"items('{loop}')"
    req = "first(body('Find_request'))"
    role_row = "first(body('Find_role'))"
    rule = "first(body('Find_rule'))"
    f = "outputs('Facts')"

    actions = {}
    actions["Get_assigned"] = sp("GetItems", "ApprovalLog",
                                 **{"$filter": f"{LOG['Action']} eq 'Assigned'", "$top": 5000})
    actions["Get_decisions"] = after(sp("GetItems", "ApprovalLog", **{
        "$filter": f"{LOG['Action']} eq 'Approve' or {LOG['Action']} eq 'Reject' or {LOG['Action']} eq 'Request changes' "
                   f"or {LOG['Action']} eq 'Cancelled'",
        "$top": 5000}), "Get_assigned")
    actions["Get_escalations"] = after(sp("GetItems", "ApprovalLog", **{
        "$filter": f"{LOG['Action']} eq 'Escalated'", "$top": 5000}), "Get_decisions")
    actions["Get_requests"] = after(sp("GetItems", "Requests", **{"$top": 5000}), "Get_escalations")
    actions["Get_routing_rules"] = after(sp("GetItems", "RoutingRules"), "Get_requests")
    actions["Get_roles"] = after(sp("GetItems", "Roles"), "Get_routing_rules")
    actions["Time_zone_map"] = after({"type": "Compose", "inputs": TIME_ZONES}, "Get_roles")
    # "|REQ-0004|Finance|" once per decision, so counting a key gives that role's number of decisions
    actions["Decided_keys_list"] = after({"type": "Select", "inputs": {
        "from": "@outputs('Get_decisions')?['body/value']",
        "select": f"@concat('|', item()?['{LOG['RequestID']}'], '|', item()?['{LOG['ActorRole']}'], '|')"}},
        "Time_zone_map")
    actions["Decided_keys"] = after({"type": "Compose", "inputs": "@join(body('Decided_keys_list'), '')"},
                                    "Decided_keys_list")
    actions["Escalated_keys_list"] = after({"type": "Select", "inputs": {
        "from": "@outputs('Get_escalations')?['body/value']",
        "select": f"@concat('|', item()?['{LOG['RequestID']}'], '|', item()?['{LOG['ActorRole']}'], '|', "
                  f"item()?['{LOG['Detail']}'])"}}, "Decided_keys")
    actions["Escalated_keys"] = after({"type": "Compose", "inputs": "@join(body('Escalated_keys_list'), '')"},
                                      "Escalated_keys_list")
    key = f"concat('|', item()?['{LOG['RequestID']}'], '|', item()?['{LOG['ActorRole']}'], '|')"
    decisions = f"sub(length(split(outputs('Decided_keys'), {key})), 1)"
    detail = f"coalesce(item()?['{LOG['Detail']}'], '')"
    round_no = f"if(contains({detail}, 'round '), int(last(split({detail}, 'round '))), 1)"
    actions["Open_approvals"] = after({"type": "Query", "inputs": {
        "from": "@outputs('Get_assigned')?['body/value']",
        "where": f"@equals({decisions}, sub({round_no}, 1))"}}, "Escalated_keys")

    inner = {}
    inner["Find_request"] = {"type": "Query", "runAfter": {}, "inputs": {
        "from": "@outputs('Get_requests')?['body/value']",
        "where": f"@equals(item()?['Title'], {row}?['{LOG['RequestID']}'])"}}
    inner["Find_role"] = after({"type": "Query", "inputs": {
        "from": "@outputs('Get_roles')?['body/value']",
        "where": f"@and(equals(item()?['{ROLE['Role']}'], {row}?['{LOG['ActorRole']}']), "
                 f"or(equals(item()?['{ROLE['Entity']}'], 'Any'), equals(item()?['{ROLE['Entity']}'], {req}?['{REQ['Entity']}'])))"}},
        "Find_request")
    inner["Find_rule"] = after({"type": "Query", "inputs": {
        "from": "@outputs('Get_routing_rules')?['body/value']",
        "where": f"@and(equals(item()?['{RULE['ApproverRole']}'], {row}?['{LOG['ActorRole']}']), "
                 f"equals(item()?['{RULE['Active']}'], true), "
                 f"or(equals(item()?['{RULE['RequestType']}'], 'Any'), equals(item()?['{RULE['RequestType']}'], {req}?['{REQ['RequestType']}'])), "
                 f"or(equals(item()?['{RULE['Entity']}'], 'Any'), equals(item()?['{RULE['Entity']}'], {req}?['{REQ['Entity']}'])))"}},
        "Find_role")
    inner["Facts"] = after({"type": "Compose", "inputs": {
        "requestId": f"@{{{row}?['{LOG['RequestID']}']}}",
        "role": f"@{{{row}?['{LOG['ActorRole']}']}}",
        "approver": f"@{{{row}?['{LOG['Actor']}']}}",
        "stage": f"@{{{row}?['{LOG['Detail']}']}}",
        "requestType": f"@{{{req}?['{REQ['RequestType']}']}}",
        "entity": f"@{{{req}?['{REQ['Entity']}']}}",
        "daysWaiting": f"@div(sub(ticks(utcNow()), ticks({row}?['{LOG['Timestamp']}'])), 864000000000)",
        "slaDays": f"@coalesce({rule}?['{RULE['SLADays']}'], {NEVER})",
        "escalateTo": f"@{{{role_row}?['{ROLE['EscalateTo']}']}}",
        "escalated": f"@contains(outputs('Escalated_keys'), concat('|', {row}?['{LOG['RequestID']}'], '|', "
                     f"{row}?['{LOG['ActorRole']}'], '|', {row}?['{LOG['Detail']}'], ':'))",
        "open": f"@contains({OPEN}, coalesce({req}?['{REQ['Status']}'], ''))",
        "localHour": f"@convertFromUtc(utcNow(), coalesce(outputs('Time_zone_map')?[coalesce({role_row}?['{ROLE['TimeZone']}'], 'Asia/Singapore')], "
                     f"'Singapore Standard Time'), 'HH')",
    }}, "Find_rule")

    what = (f"@{{{f}?['requestId']}} (@{{{f}?['requestType']}} request for @{{{f}?['entity']}}, "
            f"@{{{f}?['role']}} check, @{{{f}?['stage']}})")
    also_manager = f"and({f}?['escalated'], contains(coalesce({f}?['escalateTo'], ''), '@'))"
    remind = {
        "Message_approver": teams_chat(
            f"@{{{f}?['approver']}}",
            f"Reminder: your approval for {what} has been waiting @{{{f}?['daysWaiting']}} days "
            f"(target: @{{{f}?['slaDays']}} days). Please respond in the Approvals app in Teams. "
            f"@{{if({f}?['escalated'], concat('It has been escalated, so ', {f}?['escalateTo'], ' can answer it too: "
            f"use the card marked (escalated). '), '')}}If you've reassigned it, the new approver has it and you can "
            f"ignore this."),
        "Log_reminder": after(log_row(
            f"@{{{f}?['requestId']}}", "OneRecord", "System", "Reminder sent",
            f"To @{{{f}?['approver']}}: @{{{f}?['role']}} approval waiting @{{{f}?['daysWaiting']}} days"),
            "Message_approver"),
        "If_escalated_remind_manager": after(condition(also_manager, {
            "Message_escalation_contact": teams_chat(
                f"@{{{f}?['escalateTo']}}",
                f"Reminder: the approval for {what} has been waiting @{{{f}?['daysWaiting']}} days. It was escalated "
                f"to you, so you can answer it on @{{{f}?['approver']}}'s behalf: open the Approvals app in Teams and "
                f"use the card marked (escalated). The first answer counts."),
            "Log_manager_reminder": after(log_row(
                f"@{{{f}?['requestId']}}", "OneRecord", "System", "Reminder sent",
                f"To @{{{f}?['escalateTo']}} (escalated): @{{{f}?['role']}} approval waiting @{{{f}?['daysWaiting']}} days"),
                "Message_escalation_contact"),
        }), "Log_reminder"),
    }
    # Only requests still open are chased; then the usual "days >= SLADays" test
    decide = condition(f"and({f}?['open'], greaterOrEquals({f}?['daysWaiting'], {f}?['slaDays']))", remind)
    if at_9am_only:
        inner["If_9am_for_this_approver"] = after(
            condition(f"equals({f}?['localHour'], '09')", {"If_reminder_due": decide}), "Facts")
    else:
        inner["If_reminder_due"] = after(decide, "Facts")

    actions[loop] = after({"type": "Foreach", "foreach": "@body('Open_approvals')", "actions": inner,
                           "runtimeConfiguration": {"concurrency": {"repetitions": 10}}}, "Open_approvals")

    sap_loop = "Nudge_MDM_for_SAP_import"
    srow = f"items('{sap_loop}')"
    sreq = "first(body('Find_ready_request'))"
    mdm = "first(body('Find_MDM_analyst'))"
    g = "outputs('SAP_facts')"
    actions["Get_SAP_files"] = after(sp("GetItems", "ApprovalLog", **{
        "$filter": f"{LOG['Action']} eq 'SAP import file created'", "$top": 5000}), loop)
    actions["Find_MDM_analyst"] = after({"type": "Query", "inputs": {
        "from": "@outputs('Get_roles')?['body/value']",
        "where": f"@equals(item()?['{ROLE['Role']}'], 'MDM Analyst')"}}, "Get_SAP_files")
    sap = {}
    sap["Find_ready_request"] = {"type": "Query", "runAfter": {}, "inputs": {
        "from": "@outputs('Get_requests')?['body/value']",
        "where": f"@and(equals(item()?['Title'], {srow}?['{LOG['RequestID']}']), "
                 f"equals(item()?['{REQ['Status']}'], 'Ready for SAP import'))"}}
    sap["SAP_facts"] = after({"type": "Compose", "inputs": {
        "requestId": f"@{{{srow}?['{LOG['RequestID']}']}}",
        "ready": f"@not(empty(body('Find_ready_request')))",
        "file": f"@{{{srow}?['{LOG['Detail']}']}}",
        "requestType": f"@{{{sreq}?['{REQ['RequestType']}']}}",
        "daysWaiting": f"@div(sub(ticks(utcNow()), ticks({srow}?['{LOG['Timestamp']}'])), 864000000000)",
        "mdm": f"@{{{mdm}?['{ROLE['PersonEmail']}']}}",
        "localHour": f"@convertFromUtc(utcNow(), coalesce(outputs('Time_zone_map')?[coalesce({mdm}?['{ROLE['TimeZone']}'], "
                     f"'Asia/Singapore')], 'Singapore Standard Time'), 'HH')",
    }}, "Find_ready_request")
    nudge = {
        "Message_MDM_import": teams_chat(
            f"@{{{g}?['mdm']}}",
            f"Reminder: @{{{g}?['requestId']}} (@{{{g}?['requestType']}}) has been approved and ready for SAP import "
            f"for @{{{g}?['daysWaiting']}} days. Import @{{{g}?['file']}} with the Data Transfer Workbench, then press "
            f"Mark as created in SAP: the requestor can't use it until then.<br>"
            + app_link(f"@{{{g}?['requestId']}}")),
        "Log_MDM_import_reminder": after(log_row(
            f"@{{{g}?['requestId']}}", "OneRecord", "System", "Reminder sent",
            f"To @{{{g}?['mdm']}}: ready for SAP import for @{{{g}?['daysWaiting']}} days"), "Message_MDM_import"),
    }
    due = condition(f"and({g}?['ready'], greaterOrEquals({g}?['daysWaiting'], 1), contains(coalesce({g}?['mdm'], ''), '@'))",
                    nudge)
    sap["If_SAP_import_overdue"] = after(
        condition(f"equals({g}?['localHour'], '09')", {"If_import_due": due}) if at_9am_only else due, "SAP_facts")
    actions[sap_loop] = after({"type": "Foreach", "foreach": "@outputs('Get_SAP_files')?['body/value']",
                               "actions": sap, "runtimeConfiguration": {"concurrency": {"repetitions": 10}}},
                              "Find_MDM_analyst")

    if at_9am_only:
        trigger = {"Every_hour": {"type": "Recurrence", "recurrence": {
            "frequency": "Hour", "interval": 1, "startTime": "2026-10-22T00:00:00Z"}}}
    else:
        trigger = {"manual": {"type": "Request", "kind": "Button", "inputs": {
            "schema": {"type": "object", "properties": {}, "required": []}}}}
    return definition(trigger, actions)


if __name__ == "__main__":
    for at_9am, name, out, desc in [
        (True, "OneRecord - Reminders and escalation", "OneRecord-Reminders.zip",
         "Hourly: at 9 AM their time, reminds overdue approvers (and managers of escalated cards) and MDM about SAP imports"),
        (False, "OneRecord - Reminders (send now)", "OneRecord-Reminders-SendNow.zip",
         "Run by hand: sends every due reminder/escalation immediately (for demos)"),
    ]:
        print(write_package(HERE / out, name, desc, build(at_9am), APIS))
