"""Build the OneRecord reminder & escalation flows as importable packages (Import > Import Package (Legacy)).

Usage: python3 powerautomate/build_reminders.py
  -> OneRecord-Reminders.zip         hourly; messages each approver at 9 AM in their own time zone (Roles.TimeZone)
  -> OneRecord-Reminders-SendNow.zip  run by hand (for demos); skips the 9 AM check

An approval is open when ApprovalLog has an "Assigned" row (written by the Route and approve flow) that has no
decision yet. An approver can be asked again after "Request changes", so each Assigned row says its round
("Stage 1, round 2"): round N is open while the role has N - 1 decisions (Approve / Reject / Request changes / Cancelled) on
that request. An approver who asked for changes is therefore not chased while the requestor edits.
Days are calendar days since the Assigned row.
  * days >= EscalateAfterDays (and the role has an EscalateTo): message EscalateTo, log "Escalated"
  * otherwise days >= SLADays: remind the approver, log "Reminder sent"
SLADays / EscalateAfterDays come from the matching RoutingRules row; a blank EscalateAfterDays never escalates.
"""
from pathlib import Path

from pkg import LOG, REQ, ROLE, RULE, after, condition, definition, log_row, sp, teams_chat, write_package

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
NEVER = 999999  # stands in for a blank SLADays / EscalateAfterDays


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
    actions["Get_requests"] = after(sp("GetItems", "Requests", **{"$top": 5000}), "Get_decisions")
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
    key = f"concat('|', item()?['{LOG['RequestID']}'], '|', item()?['{LOG['ActorRole']}'], '|')"
    decisions = f"sub(length(split(outputs('Decided_keys'), {key})), 1)"
    detail = f"coalesce(item()?['{LOG['Detail']}'], '')"
    round_no = f"if(contains({detail}, 'round '), int(last(split({detail}, 'round '))), 1)"
    actions["Open_approvals"] = after({"type": "Query", "inputs": {
        "from": "@outputs('Get_assigned')?['body/value']",
        "where": f"@equals({decisions}, sub({round_no}, 1))"}}, "Decided_keys")

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
        "escalateAfterDays": f"@coalesce({rule}?['{RULE['EscalateAfterDays']}'], {NEVER})",
        "escalateTo": f"@{{{role_row}?['{ROLE['EscalateTo']}']}}",
        "localHour": f"@convertFromUtc(utcNow(), coalesce(outputs('Time_zone_map')?[coalesce({role_row}?['{ROLE['TimeZone']}'], 'Asia/Singapore')], "
                     f"'Singapore Standard Time'), 'HH')",
    }}, "Find_rule")

    what = (f"@{{{f}?['requestId']}} (@{{{f}?['requestType']}} request for @{{{f}?['entity']}}, "
            f"@{{{f}?['role']}} check, @{{{f}?['stage']}})")
    escalate = {
        "Message_escalation_contact": teams_chat(
            f"@{{{f}?['escalateTo']}}",
            f"Escalation: the approval for {what} assigned to @{{{f}?['approver']}} has been waiting "
            f"@{{{f}?['daysWaiting']}} days (escalation after @{{{f}?['escalateAfterDays']}} days). Please follow up."),
        "Log_escalation": after(log_row(
            f"@{{{f}?['requestId']}}", "OneRecord", "System", "Escalated",
            f"To @{{{f}?['escalateTo']}}: @{{{f}?['role']}} approval by @{{{f}?['approver']}} waiting @{{{f}?['daysWaiting']}} days"),
            "Message_escalation_contact"),
    }
    remind = {
        "Message_approver": teams_chat(
            f"@{{{f}?['approver']}}",
            f"Reminder: your approval for {what} has been waiting @{{{f}?['daysWaiting']}} days "
            f"(target: @{{{f}?['slaDays']}} days). Please respond in the Approvals app in Teams. If you've reassigned it, "
            f"the new approver has it and you can ignore this."),
        "Log_reminder": after(log_row(
            f"@{{{f}?['requestId']}}", "OneRecord", "System", "Reminder sent",
            f"To @{{{f}?['approver']}}: @{{{f}?['role']}} approval waiting @{{{f}?['daysWaiting']}} days"),
            "Message_approver"),
    }
    is_remind_due = condition(f"greaterOrEquals({f}?['daysWaiting'], {f}?['slaDays'])", remind)
    decide = condition(
        f"and(not(empty({f}?['escalateTo'])), greaterOrEquals({f}?['daysWaiting'], {f}?['escalateAfterDays']))",
        escalate, {"If_reminder_due": is_remind_due})
    if at_9am_only:
        inner["If_9am_for_this_approver"] = after(
            condition(f"equals({f}?['localHour'], '09')", {"If_escalation_due": decide}), "Facts")
    else:
        inner["If_escalation_due"] = after(decide, "Facts")

    actions[loop] = after({"type": "Foreach", "foreach": "@body('Open_approvals')", "actions": inner,
                           "runtimeConfiguration": {"concurrency": {"repetitions": 10}}}, "Open_approvals")

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
         "Hourly: reminds overdue approvers at 9 AM their time and escalates to EscalateTo"),
        (False, "OneRecord - Reminders (send now)", "OneRecord-Reminders-SendNow.zip",
         "Run by hand: sends every due reminder/escalation immediately (for demos)"),
    ]:
        print(write_package(HERE / out, name, desc, build(at_9am), APIS))
