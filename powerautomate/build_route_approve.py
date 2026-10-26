"""Build an importable Power Automate package (Import > Import Package (Legacy)) for the
"OneRecord - Route and approve" flow described in sharepoint/LISTS.md.

Usage: python3 powerautomate/build_route_approve.py   ->  powerautomate/OneRecord-RouteAndApprove.zip
Each approval also writes an "Assigned" row to ApprovalLog, which build_reminders.py relies on.
"""
import re
from pathlib import Path

from pkg import (CC, CUST, ESCALATE_AFTER, ESCALATED_WAIT, ITEM, LISTS, LOG, REQ, RF, ROLE, RULE, SENS, SITE, VEND,
                 after, app_link, condition, definition, log_row, sp, teams_chat, write_package)

OUT = Path(__file__).with_name("OneRecord-RouteAndApprove.zip")
NAME = "OneRecord - Route and approve"


def t(col):
    """Trigger (new Requests item) column."""
    return f"triggerBody()?['{REQ[col]}']"


def update_request(prev, **cols):
    params = {"id": "@triggerBody()?['ID']", "item/Title": "@triggerBody()?['Title']"}
    params.update({f"item/{REQ[k]}": v for k, v in cols.items()})
    return after(sp("PatchItem", "Requests", **params), *prev)


REQUEST_LINK = app_link("@{triggerBody()?['Title']}")
ANY = ["Succeeded", "Failed", "TimedOut", "Skipped"]
STATUS, BODY = "['status']", "['outputs']?['body']"  # parts of actions('X'): works even when X was skipped


def teams_to_requestor(message, *prev):
    """A Teams message to the requestor, ending with a link that opens the request in the app."""
    return after(teams_chat("@{triggerBody()?['Author']?['Email']}", f"{message}<br>{REQUEST_LINK}"), *prev)


def duration_text(iso):
    """P4D -> '4 days', PT10M -> '10 minutes' (for messages)."""
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?", iso)
    parts = [f"{n} {unit}{'' if n == '1' else 's'}" for n, unit in zip(m.groups(), ("day", "hour", "minute")) if n]
    return " ".join(parts) or iso


NAME_EXPR = f"coalesce({t('CustomerName')}, {t('ItemDescription')}, {t('VendorName')}, {t('CostCenterName')})"


QA_ROLE = "Quality/Regulatory"
RESPONSES = ["Approve", "Request changes", "Reject"]

# Request fields an approval step can depend on (RoutingRules "Only if" = ConditionField, "is" = ConditionValue,
# one value or several separated by ";", any of them matches). The Rules screen offers exactly these, and the app's
# approver preview mirrors the matching (gen_form.py ROUTE_FIELDS): change them together.
ROUTE_FIELDS = ["Country", "ProductFamily", "IsRegulated", "SuppliesRegulatedGoods", "Segment", "UnitOfMeasure",
                "Department"]
YES_NO = {"IsRegulated", "SuppliesRegulatedGoods"}  # Yes/No columns; "Not sure" is saved as Yes, so it matches Yes


def norm(expr):
    """Lower case, no spaces, so 'Regulatory Affairs' matches 'regulatory affairs'. Blank-safe: flow expressions
    evaluate every argument of if / and / or, so nothing here may fail on a blank value."""
    return f"toLower(replace(string(coalesce({expr}, '')), ' ', ''))"


def route_facts():
    """The request's value for each routing field, normalised; a blank field is '-' so it never matches a rule."""
    return {f.lower(): (f"@if(equals({t(f)}, true), 'yes', 'no')" if f in YES_NO
                        else f"@if(empty({t(f)}), '-', {norm(t(f))})") for f in ROUTE_FIELDS}


def condition_met(rule):
    """True when the rule has no condition, or the request's value is one of the rule's values."""
    cf, cv = f"{rule}?['{RULE['ConditionField']}']", f"{rule}?['{RULE['ConditionValue']}']"
    return (f"or(empty({cf}), and(not(empty({cv})), contains(split({norm(f'replace(string(coalesce({cv}, {chr(39)}{chr(39)})), {chr(39)},{chr(39)}, {chr(39)};{chr(39)})')}, ';'), "
            f"coalesce(outputs('Route_facts')?[{norm(cf)}], '-'))))")
WAIT_FOR_EDIT = "P14D"  # how long a sent-back request waits for the requestor before it is closed


def short(expr, n=240):
    """Text cut to fit a single-line SharePoint column (255 characters)."""
    text = f"string(coalesce({expr}, ''))"
    return f"substring({text}, 0, min({n}, length({text})))"


# Version pinning. Every approval counts only for the version of the request it was given: the fields the requestor
# fills in plus the SensitiveDetails row (by its Modified time, so no bank or credit values are copied around). The
# version under approval is kept in the "Pinned" variable. It moves only when the flow itself allows a change: an
# Edit and resubmit after Request changes, or Quality/Regulatory deciding a "Not sure" item. Any other change (someone
# editing the row in SharePoint) puts the request on hold, and the SAP file is only written if it still matches.
CONTENT = ["RequestType", "Entity", "Country", "CustomerName", "RegistrationNo", "BillingAddress", "ContactEmail",
           "Segment", "ItemDescription", "ProductFamily", "UnitOfMeasure", "HSCode", "IsRegulated", "RegulatedAnswer",
           "RegulatoryLicenceNo", "ShelfLifeMonths", "ManufacturerPartNo", "VendorName", "TaxID",
           "SuppliesRegulatedGoods", "ISO13485CertNo", "CostCenterName", "Department", "Owner", "BudgetYear",
           "DuplicateCheck", "PossibleMatchID", "DupReason"]
EDITING = "createArray('Changes requested', 'Resubmitted')"  # the requestor may change the request in these
ON_HOLD = "On hold"


def fingerprint(request_action, sensitive_action):
    """The request's content as one text value, from a Get item on Requests and a Get items on SensitiveDetails."""
    values = [f"outputs('{request_action}')?['body/{REQ[c]}']" for c in CONTENT]
    values.append(f"first(outputs('{sensitive_action}')?['body/value'])?['Modified']")
    return f"string(createArray({', '.join(values)}))"


def get_sensitive():
    """This request's SensitiveDetails row (none for Item / Cost Center requests)."""
    return sp("GetItems", "SensitiveDetails", **{
        "$filter": f"{SENS['RequestID']} eq '@{{triggerBody()?['Title']}}'", "$top": 1})


def repin(name, prev, request_action=None, sensitive_action=None):
    """Re-read the request (and its sensitive row) and make that the version under approval."""
    req_a, sens_a = request_action or f"{name}_request", sensitive_action or f"{name}_sensitive"
    out = {}
    if not request_action:
        out[req_a] = after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"), prev)
        prev = req_a
    if not sensitive_action:
        out[sens_a] = after(get_sensitive(), prev)
        prev = sens_a
    out[name] = after({"type": "SetVariable", "inputs": {
        "name": "Pinned", "value": f"@{fingerprint(req_a, sens_a)}"}}, prev)
    return out


def hold_request(stage_label, why, *prev):
    """Stop a request whose content changed outside OneRecord: status On hold, log it, tell MDM and the requestor."""
    key = re.sub(r"\W", "_", stage_label)
    mdm = f"first(body('Find_MDM_analyst'))?['{ROLE['PersonEmail']}']"
    return {
        f"Mark_on_hold_{key}": update_request(
            list(prev), Status=ON_HOLD, CurrentStage="On hold: changed outside OneRecord while it was being approved"),
        f"Log_on_hold_{key}": after(log_row(
            "@triggerBody()?['Title']", "OneRecord", "System", "Changed outside OneRecord", why),
            f"Mark_on_hold_{key}"),
        f"Tell_MDM_on_hold_{key}": after(teams_chat(
            f"@{{{mdm}}}",
            f"@{{triggerBody()?['Title']}} was put on hold: its details or its payment / bank details were changed "
            f"directly in SharePoint, not through Edit and resubmit, so the approvals given no longer match what "
            f"would go into SAP. Nothing was sent to SAP. Check the version history of the request, then ask the "
            f"requestor to submit a new request.<br>{REQUEST_LINK}"), f"Log_on_hold_{key}"),
        f"Tell_requestor_on_hold_{key}": after(teams_to_requestor(
            f"Your request @{{triggerBody()?['Title']}} is on hold because it was changed outside OneRecord while it "
            f"was being approved. The MDM team will contact you. To change a request, use Edit and resubmit when an "
            f"approver asks for changes."), f"Tell_MDM_on_hold_{key}"),
    }


def stage_loop(stage):
    """Filter the active rules for this stage, then one parallel approval per rule.

    Each approval runs in rounds: an approver can Approve, Reject or Request changes. Request changes sends the
    request back to the requestor (status "Changes requested"), waits until they resubmit it from the app, then asks
    the same approver again. The other approvers carry on meanwhile; the MDM card shows what changed.
    """
    loop = f"Stage_{stage}_approvals"
    approval = f"Stage_{stage}_approval"
    rnd = f"Review_round_{stage}"
    latest = f"Get_latest_{stage}"
    stage_test = (f"less(item()?['{RULE['Stage']}'], 1.5)" if stage == 1
                  else f"greater(item()?['{RULE['Stage']}'], 1.5)")
    where = (
        f"@and(equals(item()?['{RULE['Active']}'], true), {stage_test}, "
        f"or(equals(item()?['{RULE['RequestType']}'], {t('RequestType')}), equals(item()?['{RULE['RequestType']}'], 'Any')), "
        f"or(equals(item()?['{RULE['Entity']}'], 'Any'), equals(item()?['{RULE['Entity']}'], {t('Entity')})), "
        f"{condition_met('item()')})"
    )
    role = f"items('{loop}')?['{RULE['ApproverRole']}']"
    escalated = f"Escalated_approval_{stage}"  # stage 1 only: the card re-sent to approver + EscalateTo
    card = f"Card_{stage}"  # whichever card decided: the first one, or the re-sent one after escalation
    first_resp = f"first(outputs('{card}')?['body']?['responses'])"
    comments = f"{first_resp}?['comments']"
    # The card's result. Anything other than Approve / Reject / Request changes (the sender pressed Cancel request,
    # or the approval action failed) counts as "Cancelled", so it can never slip through as an approval.
    outcome = f"outputs('Outcome_{stage}')"
    raw_outcome = f"outputs('{card}')?['body']?['outcome']"
    round_no = f"add(iterationIndexes('{rnd}'), 1)"

    def cur(col):
        """The request as it is now (it may have been edited since it was submitted)."""
        return f"outputs('{latest}')?['body/{REQ[col]}']"

    name_now = f"coalesce({cur('CustomerName')}, {cur('ItemDescription')}, {cur('VendorName')}, {cur('CostCenterName')})"
    # Routing gap: no Roles row, a blank email or a placeholder (no "@") -> the MDM Analyst approves on the
    # missing role's behalf, gets a Teams nudge to fix Roles, and the gap is logged and shown on the request.
    routing = f"Stage_{stage}_routing"
    found = f"first(body('Find_stage_{stage}_approver'))?['{ROLE['PersonEmail']}']"
    mdm = f"first(body('Find_MDM_analyst'))?['{ROLE['PersonEmail']}']"
    valid = f"contains(coalesce({found}, ''), '@')"
    esc_found = f"first(body('Find_stage_{stage}_approver'))?['{ROLE['EscalateTo']}']"
    esc_to = f"outputs('{routing}')?['escalateTo']"
    approver_email = f"@{{outputs('{routing}')?['email']}}"
    gap = f"outputs('{routing}')?['gap']"
    entity = t('Entity')
    status_now = lambda action: f"outputs('{action}')?['body/{REQ['Status']}']"

    poll = f"Poll_request_{stage}"
    sent_back = {
        f"Mark_changes_requested_{stage}": update_request(
            [], Status="Changes requested",
            CurrentStage=f"@{{{short(f'concat({role}, {chr(39)} asked for changes: {chr(39)}, coalesce({comments}, {chr(39)}(no comment){chr(39)}))')}}}"),
        f"Tell_requestor_changes_{stage}": teams_to_requestor(
            f"@{{{role}}} asked for changes on your request @{{triggerBody()?['Title']}}: "
            f"@{{coalesce({comments}, '(no comment)')}}. Open it with the link below and press Edit and resubmit.",
            f"Mark_changes_requested_{stage}"),
        # Poll every 5 minutes until the requestor resubmits (the app sets Status = "Resubmitted")
        f"Wait_for_resubmit_{stage}": after({
            "type": "Until", "expression": f"@not(equals({status_now(poll)}, 'Changes requested'))",
            "limit": {"count": 5000, "timeout": WAIT_FOR_EDIT},
            "actions": {
                f"Wait_5_minutes_{stage}": {"type": "Wait", "runAfter": {},
                                            "inputs": {"interval": {"count": 5, "unit": "Minute"}}},
                poll: after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"), f"Wait_5_minutes_{stage}"),
            }}, f"Tell_requestor_changes_{stage}"),
    }
    last_change = f"last(split(coalesce(outputs('{poll}')?['body/{REQ['ChangeNote']}'], ''), decodeUriComponent('%0A')))"
    no_reply = {
        f"Close_no_response_{stage}": update_request(
            [], Status="Rejected",
            CurrentStage=f"Closed: no changes within 14 days of the @{{{role}}} request"),
        f"Log_no_response_{stage}": after(log_row(
            "@triggerBody()?['Title']", "OneRecord", "System", "Closed",
            f"No resubmit within 14 days of the @{{{role}}} request for changes"), f"Close_no_response_{stage}"),
        f"Tell_requestor_closed_{stage}": teams_to_requestor(
            f"Your request @{{triggerBody()?['Title']}} was closed because it wasn't resubmitted within 14 days of "
            f"the @{{{role}}} request for changes. Submit a new request when you have the details.",
            f"Log_no_response_{stage}"),
    }
    sent_back[f"After_wait_{stage}"] = {
        **condition(f"equals({status_now(poll)}, 'Resubmitted')", {
            f"Log_resubmitted_{stage}": log_row(
                "@triggerBody()?['Title']", "@{triggerBody()?['Author']?['Email']}", "Requestor", "Resubmitted",
                f"@{{{short(last_change)}}}"),
            # The edited request is now the version under approval (pinned before it goes back to Pending, so no
            # other card can see the new content while the old version is still pinned)
            **repin(f"Pin_resubmitted_{stage}", f"Log_resubmitted_{stage}"),
            f"Back_to_pending_{stage}": update_request(
                [f"Pin_resubmitted_{stage}"], Status="Pending approval",
                CurrentStage=f"Resubmitted; back with @{{{role}}}"),
        }, {f"If_no_response_{stage}": condition(f"equals({status_now(poll)}, 'Changes requested')", no_reply)}),
        "runAfter": {f"Wait_for_resubmit_{stage}": ["Succeeded", "Failed", "TimedOut"]},
    }

    def card_action(assigned_to, title_suffix="", note="", timeout=None):
        """The approval card (Approve / Request changes / Reject). The first answer decides."""
        action = {"type": "OpenApiConnectionWebhook", "inputs": {
                "parameters": {
                    "approvalType": "CustomResponse",  # exact value from Peek code in the tenant
                    "WebhookApprovalCreationInput/responseOptions": RESPONSES,
                    # The card header always names the flow's connection owner, so the title names the requestor
                    "WebhookApprovalCreationInput/title":
                        f"@{{triggerBody()?['Title']}} from @{{if(empty({t('Requestor')}), "
                        f"triggerBody()?['Author']?['DisplayName'], {t('Requestor')})}}: "
                        f"@{{{t('RequestType')}}} request for @{{{t('Entity')}}} "
                        f"(@{{{role}}} check)@{{if(greater({round_no}, 1), concat(' - round ', string({round_no})), '')}}"
                        + title_suffix,
                    "WebhookApprovalCreationInput/assignedTo": assigned_to,
                    "WebhookApprovalCreationInput/details": (
                        note +
                        f"**Requested by:** @{{{t('Requestor')}}}\n\n"
                        f"**Name:** @{{{name_now}}}\n\n"
                        f"**Country:** @{{{cur('Country')}}}\n\n"
                        f"**Duplicate check:** @{{if(equals({cur('DuplicateCheck')}, 'Clear'), '', '\u26a0\ufe0f ')}}"
                        f"@{{{cur('DuplicateCheck')}}} @{{{cur('PossibleMatchID')}}}\n\n"
                        f"@{{if(empty({cur('DupReason')}), '', concat('**Requestor says it is not a duplicate:** ', "
                        f"{cur('DupReason')}))}}\n\n"
                        f"**Your check:** @{{{role}}} (stage {stage})\n\n"
                        f"@{{if(empty(items('{loop}')?['{RULE['ConditionField']}']), '', concat('**Why this check:** "
                        f"the step applies when ', items('{loop}')?['{RULE['ConditionField']}'], ' is ', "
                        f"items('{loop}')?['{RULE['ConditionValue']}'], '.'))}}\n\n"
                        f"@{{if(equals({t('RequestType')}, 'Item'), concat('**Regulated (requestor answer):** ', "
                        f"coalesce({cur('RegulatedAnswer')}, if(equals({cur('IsRegulated')}, true), 'Yes', 'No'))), '')}}\n\n"
                        f"@{{if(and(equals({role}, '{QA_ROLE}'), equals({cur('RegulatedAnswer')}, 'Not sure')), "
                        f"'**The requestor was not sure whether this item is regulated, so you decide.** Approve = not "
                        f"regulated (it is recorded as No). If it is regulated, choose Request changes and ask for the "
                        f"licence no.', '')}}\n\n"
                        f"@{{if(empty({cur('ChangeNote')}), '', concat('**Changed after an approver asked:** ', "
                        f"{cur('ChangeNote')}))}}\n\n"
                        f"If something is missing or wrong, choose **Request changes** and say what: it goes back to the "
                        f"requestor and returns to you when fixed.\n\n"
                        f"@{{if({gap}, concat('**Note:** No ', {role}, ' is set up for ', {entity}, "
                        f"' in Roles, so this came to MDM. Your decision counts for the ', {role}, ' step.'), '')}}\n\n"
                        f"@{{if(and(contains(outputs('Sensitive_roles'), concat(';', {role}, ';')), "
                        f"not(empty(outputs('Sensitive_link')))), concat('**Payment & bank details:** "
                        f"[View in the restricted SensitiveDetails list](', outputs('Sensitive_link'), ')'), '')}}"),
                    "WebhookApprovalCreationInput/itemLink": "@{triggerBody()?['{Link}']}",
                    "WebhookApprovalCreationInput/itemLinkDescription": "Open the request in SharePoint",
                    "WebhookApprovalCreationInput/enableNotifications": True,
                    "WebhookApprovalCreationInput/enableReassignment": True,
                },
                "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_approvals",
                         "connectionName": "shared_approvals", "operationId": "StartAndWaitForAnApproval"},
                "authentication": "@parameters('$authentication')"}}
        if timeout:
            action["limit"] = {"timeout": timeout}
        return action

    status_at_answer = f"coalesce(outputs('Status_now_{stage}')?['body/{REQ['Status']}'], '')"
    alive = f"contains(createArray('Pending approval', 'Changes requested', 'Resubmitted'), {status_at_answer})"
    # Version check when the card is answered. "outside": the request no longer matches the pinned version and nobody
    # is editing it through the app, so it was changed in SharePoint. "stale": an Approve given on an older version
    # (the card was sent before a resubmit) or while the requestor is editing; it doesn't count and is asked again.
    integrity = f"outputs('Integrity_{stage}')"
    counted = f"and({alive}, not(equals({integrity}, 'outside')))"  # the answer may change the request
    version = f"outputs('Status_now_{stage}')?['body/{{VersionNumber}}']"
    wait_poll = f"Poll_editing_{stage}"
    not_counted = {
        f"Log_not_counted_{stage}": log_row(
            "@triggerBody()?['Title']", f"@{{coalesce({first_resp}?['responder/email'], 'OneRecord')}}",
            f"@{{{role}}}", "Approval not counted",
            f"Stage {stage}, round @{{{round_no}}}: the request was resubmitted after this card was sent, so the "
            f"approval was for an older version. Asked again on the current version."),
        # If the requestor is still editing, ask again only once they've resubmitted
        f"If_still_editing_{stage}": after(condition(f"contains({EDITING}, {status_at_answer})", {
            f"Wait_for_edit_{stage}": {
                "type": "Until", "runAfter": {},
                "expression": f"@not(contains({EDITING}, coalesce(outputs('{wait_poll}')?['body/{REQ['Status']}'], '')))",
                "limit": {"count": 5000, "timeout": WAIT_FOR_EDIT},
                "actions": {
                    f"Wait_5_minutes_edit_{stage}": {"type": "Wait", "runAfter": {},
                                                     "inputs": {"interval": {"count": 5, "unit": "Minute"}}},
                    wait_poll: after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"),
                                     f"Wait_5_minutes_edit_{stage}"),
                }}}), f"Log_not_counted_{stage}"),
    }
    if stage == 1:
        both = f"if(empty({esc_to}), outputs('{routing}')?['email'], concat(outputs('{routing}')?['email'], ';', {esc_to}))"
        waited = duration_text(ESCALATE_AFTER)
        escalation = {f"If_escalate_{stage}": {**condition(f"equals(actions('{approval}')?['status'], 'TimedOut')", {
            f"Log_escalated_{stage}": log_row(
                "@triggerBody()?['Title']", f"@{{coalesce(if(empty({esc_to}), null, {esc_to}), outputs('{routing}')?['email'])}}",
                f"@{{{role}}}", "Escalated",
                # starts "Stage 1, round N:" so the reminders flow can match it to the open Assigned row
                f"Stage {stage}, round @{{{round_no}}}: no answer within {waited}; card re-sent to @{{{both}}}"),
            escalated: after(card_action(
                f"@{{{both}}}", title_suffix=" (escalated)", timeout=ESCALATED_WAIT,
                note=(f"**Escalated:** this wasn't answered within {waited}, so it now goes to @{{{both}}}. "
                      f"Either of you can answer; the first answer counts. It replaces the earlier card, which no "
                      f"longer changes anything.\n\n")), f"Log_escalated_{stage}"),
        }), "runAfter": {approval: ANY}}}
        pick = lambda part: (f"if(equals(actions('{approval}')?['status'], 'TimedOut'), "
                             f"actions('{escalated}')?{part}, actions('{approval}')?{part})")
        card_inputs = {"status": f"@{{{pick(STATUS)}}}", "body": f"@{pick(BODY)}"}
        card_after = {f"If_escalate_{stage}": ANY}
    else:
        escalation = {}
        card_inputs = {"status": f"@{{actions('{approval}')?['status']}}",
                       "body": f"@actions('{approval}')?['outputs']?['body']"}
        card_after = {approval: ANY}

    round_actions = {
        latest: sp("GetItem", "Requests", id="@triggerBody()?['ID']"),
        # The version this card shows
        f"Sensitive_seen_{stage}": after(get_sensitive(), latest),
        f"Seen_{stage}": after({"type": "Compose", "inputs": f"@{fingerprint(latest, f'Sensitive_seen_{stage}')}"},
                               f"Sensitive_seen_{stage}"),
        f"Log_stage_{stage}_assigned": after(log_row(
            "@triggerBody()?['Title']", approver_email, f"@{{{role}}}", "Assigned",
            f"Stage {stage}, round @{{{round_no}}}"), f"Seen_{stage}"),
        approval: after(card_action(approver_email, timeout=ESCALATE_AFTER if stage == 1 else None),
                        f"Log_stage_{stage}_assigned"),
        **escalation,
        card: {"type": "Compose", "inputs": card_inputs, "runAfter": card_after},
        f"Outcome_{stage}": after({"type": "Compose", "inputs":
            f"@if(and(equals(outputs('{card}')?['status'], 'Succeeded'), "
            f"contains(createArray('Approve', 'Reject', 'Request changes'), coalesce({raw_outcome}, ''))), "
            f"{raw_outcome}, 'Cancelled')"}, card),
        # A decision only changes the request while it is still open: once one approver has rejected it (or it was
        # cancelled or closed), later answers from the other parallel cards are logged but change nothing.
        f"Status_now_{stage}": after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"), f"Outcome_{stage}"),
        f"Sensitive_now_{stage}": after(get_sensitive(), f"Status_now_{stage}"),
        f"Integrity_{stage}": after({"type": "Compose", "inputs":
            f"@if(and(not(equals({outcome}, 'Cancelled')), not(contains({EDITING}, {status_at_answer})), "
            f"not(equals({fingerprint(f'Status_now_{stage}', f'Sensitive_now_{stage}')}, variables('Pinned')))), "
            f"'outside', if(and(equals({outcome}, 'Approve'), or(contains({EDITING}, {status_at_answer}), "
            f"not(equals(outputs('Seen_{stage}'), variables('Pinned'))))), 'stale', 'ok'))"},
            f"Sensitive_now_{stage}"),
        # Answered by someone other than the assigned approver: the card was reassigned in Teams. Log the hand-off.
        f"If_stage_{stage}_reassigned": after(condition(
            f"and(not(equals({outcome}, 'Cancelled')), not(empty({first_resp}?['responder/email'])), "
            f"not(equals(toLower({first_resp}?['responder/email']), toLower(outputs('{routing}')?['email']))), "
            f"not(equals(toLower({first_resp}?['responder/email']), toLower({esc_to}))))", {
                f"Log_reassigned_{stage}": log_row(
                    "@triggerBody()?['Title']", f"@{{{first_resp}?['responder/email']}}", f"@{{{role}}}", "Reassigned",
                    f"Stage {stage}, round @{{{round_no}}}: assigned to @{{outputs('{routing}')?['email']}}, "
                    f"answered by @{{{first_resp}?['responder/displayName']}}")}), f"Integrity_{stage}"),
        f"Log_stage_{stage}_decision": after(sp("PostItem", "ApprovalLog", **{
            "item/Title": "@triggerBody()?['Title']",
            f"item/{LOG['RequestID']}": "@triggerBody()?['Title']",
            f"item/{LOG['Timestamp']}": "@utcNow()",
            f"item/{LOG['Actor']}": f"@{{coalesce({first_resp}?['responder/displayName'], 'OneRecord')}}",
            f"item/{LOG['ActorRole']}": f"@{{{role}}}",
            f"item/{LOG['Action']}": f"@{{{outcome}}}",
            # The SharePoint version of the request when it was answered, so the exact content can be looked up
            # in the request's version history
            f"item/{LOG['Detail']}": f"@{{{short(f'concat({chr(39)}Stage {stage}, round {chr(39)}, string({round_no}), {chr(39)} (request version {chr(39)}, string(coalesce({version}, {chr(39)}?{chr(39)})), {chr(39)}). {chr(39)}, coalesce({comments}, {chr(39)}{chr(39)}))')}}}",
        }), f"If_stage_{stage}_reassigned"),
        # Changed in SharePoint outside the app: stop the request before anything reaches SAP
        f"If_stage_{stage}_changed_outside": after(condition(
            f"and({alive}, equals({integrity}, 'outside'))",
            hold_request(f"stage_{stage}",
                         f"Stage {stage}, round @{{{round_no}}}, answered by @{{{role}}}: the request (version "
                         f"@{{{version}}}) or its payment / bank details no longer match the version under approval")),
            f"Log_stage_{stage}_decision"),
        # Approved an older version: not counted, asked again on the current one
        f"If_stage_{stage}_not_counted": after(condition(f"and({alive}, equals({integrity}, 'stale'))", not_counted),
                                               f"If_stage_{stage}_changed_outside"),
        # The card was cancelled (Cancel request in Teams): the request is withdrawn
        f"If_stage_{stage}_cancelled": after(condition(f"and(equals({outcome}, 'Cancelled'), {counted})", {
            f"Mark_cancelled_stage_{stage}": update_request(
                [], Status="Cancelled", CurrentStage=f"Cancelled at @{{{role}}} check (stage {stage})"),
            f"Tell_requestor_cancelled_{stage}": teams_to_requestor(
                f"Your request @{{triggerBody()?['Title']}} was cancelled at the @{{{role}}} check. "
                f"Submit a new request if it's still needed.", f"Mark_cancelled_stage_{stage}"),
        }), f"Log_stage_{stage}_decision"),
        # A rejection reaches the requestor straight away, not after every parallel approver has answered
        f"If_stage_{stage}_rejected": after(condition(f"and(equals({outcome}, 'Reject'), {counted})", {
            f"Mark_rejected_stage_{stage}": update_request(
                [], Status="Rejected", CurrentStage=f"Rejected at @{{{role}}} check (stage {stage})"),
            f"Tell_requestor_rejected_{stage}": teams_to_requestor(
                f"Your request @{{triggerBody()?['Title']}} was rejected by @{{{role}}}: "
                f"@{{coalesce({comments}, '(no comment)')}}", f"Mark_rejected_stage_{stage}"),
        }), f"If_stage_{stage}_cancelled"),
        # "Not sure" items: Quality/Regulatory approving means "not regulated", so record that
        f"If_stage_{stage}_regulated_decided": after(condition(
            f"and(equals({outcome}, 'Approve'), equals({integrity}, 'ok'), {alive}, equals({role}, '{QA_ROLE}'), "
            f"equals({cur('RegulatedAnswer')}, 'Not sure'))", {
                f"Record_not_regulated_{stage}": update_request(
                    [], IsRegulated=False, RegulatedAnswer="No (decided by Quality/Regulatory)"),
                f"Log_not_regulated_{stage}": after(log_row(
                    "@triggerBody()?['Title']", "OneRecord", "System", "Regulated decided",
                    f"Requestor was not sure; @{{{first_resp}?['responder/displayName']}} ({QA_ROLE}) approved, "
                    f"so it is recorded as not regulated"), f"Record_not_regulated_{stage}"),
                # The flow changed the request itself, so the recorded answer is now the version under approval
                **repin(f"Pin_regulated_{stage}", f"Log_not_regulated_{stage}", sensitive_action=f"Sensitive_now_{stage}"),
            }), f"If_stage_{stage}_rejected"),
        f"If_stage_{stage}_changes_requested": after(condition(f"and(equals({outcome}, 'Request changes'), {counted})",
                                                               sent_back),
                                                     f"If_stage_{stage}_regulated_decided"),
        f"Round_end_{stage}": after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"),
                                    f"If_stage_{stage}_changes_requested"),
    }

    inner = {
        f"Find_stage_{stage}_approver": {"type": "Query", "runAfter": {}, "inputs": {
            "from": "@outputs('Get_roles')?['body/value']",
            "where": f"@and(equals(item()?['{ROLE['Role']}'], {role}), "
                     f"or(equals(item()?['{ROLE['Entity']}'], 'Any'), equals(item()?['{ROLE['Entity']}'], {entity})))"}},
        routing: after({"type": "Compose", "inputs": {
            "found": f"@{{{found}}}",
            "gap": f"@not({valid})",
            "email": f"@if({valid}, {found}, {mdm})",
            "escalateTo": f"@{{if(and({valid}, contains(coalesce({esc_found}, ''), '@')), {esc_found}, '')}}",
        }}, f"Find_stage_{stage}_approver"),
        f"If_stage_{stage}_routing_gap": after(condition(gap, {
            f"Tell_MDM_routing_gap_{stage}": teams_chat(
                f"@{{{mdm}}}",
                f"Routing gap: no valid @{{{role}}} is set up for @{{{entity}}} in the Roles list, so "
                f"@{{triggerBody()?['Title']}} was sent to you instead. Please add or fix a Roles row "
                f"(Role = @{{{role}}}, Entity = @{{{entity}}} or Any).<br>{REQUEST_LINK}"),
            f"Log_routing_gap_{stage}": after(log_row(
                "@triggerBody()?['Title']", "OneRecord", "System", "Routing gap",
                f"No valid @{{{role}}} for @{{{entity}}} (found: '@{{outputs('{routing}')?['found']}}'); "
                f"sent to MDM @{{{mdm}}}"), f"Tell_MDM_routing_gap_{stage}"),
            f"Show_routing_gap_{stage}": update_request(
                [f"Log_routing_gap_{stage}"],
                CurrentStage=f"@{{{role}}} missing for @{{{entity}}} in Roles; sent to MDM"),
        }), routing),
        # Ask again after each resubmit or an approval that didn't count; stop on Approve / Reject, or when the
        # request has been closed or put on hold
        rnd: after({"type": "Until",
                    "expression": f"@or(not(or(equals({outcome}, 'Request changes'), equals({integrity}, 'stale'))), "
                                  f"contains(createArray('Rejected', 'Cancelled', '{ON_HOLD}'), "
                                  f"{status_now(f'Round_end_{stage}')}))",
                    "limit": {"count": 10, "timeout": "P30D"}, "actions": round_actions},
                   f"If_stage_{stage}_routing_gap"),
    }
    return {
        f"Filter_stage_{stage}_rules": {"type": "Query", "runAfter": {}, "inputs": {
            "from": "@outputs('Get_routing_rules')?['body/value']", "where": where}},
        loop: {"type": "Foreach", "runAfter": {}, "foreach": f"@body('Filter_stage_{stage}_rules')",
               "actions": inner, "runtimeConfiguration": {"concurrency": {"repetitions": 20}}},
    }


def rejected_gate(stage, prev):
    """After a stage: re-read the request; if it was rejected, closed or put on hold, stop (people were already told)."""
    check = f"Check_after_stage_{stage}"
    return {
        check: {**sp("GetItem", "Requests", id="@triggerBody()?['ID']"), "runAfter": {prev: ANY}},
        f"If_rejected_after_stage_{stage}": after({
            "type": "If",
            "expression": {"or": [{"equals": [f"@outputs('{check}')?['body/{REQ['Status']}']", s]}
                                  for s in ("Rejected", "Cancelled", ON_HOLD)]},
            "actions": {f"Stop_after_stage_{stage}": {"type": "Terminate", "runAfter": {},
                                                      "inputs": {"runStatus": "Succeeded"}}},
            "else": {"actions": {}},
        }, check),
    }


actions = {}
# The master list row added for this request (set when the record is approved, updated once it is in SAP)
actions["Init_master_row_id"] = {"type": "InitializeVariable", "runAfter": {}, "inputs": {
    "variables": [{"name": "MasterRowID", "type": "integer", "value": 0}]}}
actions["Get_routing_rules"] = after(sp("GetItems", "RoutingRules"), "Init_master_row_id")
actions["Get_roles"] = after(sp("GetItems", "Roles"), "Get_routing_rules")

ROUTE_FACTS = route_facts()  # built here, while t() still reads the submitted request
s1 = stage_loop(1)
actions["Find_MDM_analyst"] = after({"type": "Query", "inputs": {
    "from": "@outputs('Get_roles')?['body/value']",
    "where": f"@equals(item()?['{ROLE['Role']}'], 'MDM Analyst')"}}, "Get_roles")
# Who may see sensitive fields for this request type (RequiredFields rows with Sensitive = Yes), and the
# request's row in SensitiveDetails (only Customer/Vendor requests have one). Cards link to it; values stay out.
actions["Get_required_fields"] = after(sp("GetItems", "RequiredFields", **{
    "$filter": f"{RF['RequestType']} eq '@{{triggerBody()?['{REQ['RequestType']}']}}'"}), "Find_MDM_analyst")
actions["Sensitive_fields"] = after({"type": "Query", "inputs": {
    "from": "@outputs('Get_required_fields')?['body/value']",
    "where": f"@equals(item()?['{RF['Sensitive']}'], 'Yes')"}}, "Get_required_fields")
actions["Sensitive_role_lists"] = after({"type": "Select", "inputs": {
    "from": "@body('Sensitive_fields')", "select": f"@item()?['{RF['VisibleToRoles']}']"}}, "Sensitive_fields")
actions["Sensitive_roles"] = after({"type": "Compose", "inputs":
    "@concat(';', replace(join(body('Sensitive_role_lists'), ';'), '; ', ';'), ';')"}, "Sensitive_role_lists")
actions["Get_sensitive_item"] = after(sp("GetItems", "SensitiveDetails", **{
    "$filter": f"{SENS['RequestID']} eq '@{{triggerBody()?['Title']}}'", "$top": 1}), "Sensitive_roles")
actions["Sensitive_link"] = after({"type": "Compose", "inputs":
    "@{first(outputs('Get_sensitive_item')?['body/value'])?['{Link}']}"}, "Get_sensitive_item")
# The version as submitted is the first version under approval
actions["Get_request_as_submitted"] = after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"), "Sensitive_link")
actions["Init_pinned_version"] = after({"type": "InitializeVariable", "inputs": {"variables": [{
    "name": "Pinned", "type": "string",
    "value": f"@{fingerprint('Get_request_as_submitted', 'Get_sensitive_item')}"}]}}, "Get_request_as_submitted")
# The request's values for the "Only if" conditions on approval steps (read by both stages' rule filters)
actions["Route_facts"] = after({"type": "Compose", "inputs": ROUTE_FACTS}, "Init_pinned_version")
actions["Filter_stage_1_rules"] = after(s1["Filter_stage_1_rules"], "Route_facts")
actions["Mark_stage_1"] = update_request(
    ["Filter_stage_1_rules"], Status="Pending approval",
    CurrentStage="Stage 1: waiting for @{length(body('Filter_stage_1_rules'))} approvers in parallel")
actions["Stage_1_approvals"] = after(s1["Stage_1_approvals"], "Mark_stage_1")
actions.update(rejected_gate(1, "Stage_1_approvals"))

s2 = stage_loop(2)
actions["Filter_stage_2_rules"] = after(s2["Filter_stage_2_rules"], "If_rejected_after_stage_1")
actions["Mark_stage_2"] = update_request(["Filter_stage_2_rules"], CurrentStage="Stage 2: MDM final review")
actions["Stage_2_approvals"] = after(s2["Stage_2_approvals"], "Mark_stage_2")
actions.update(rejected_gate(2, "Stage_2_approvals"))

# Approved: write a SAP Business One Data Transfer Workbench (DTW) file for the new record.
# Tab-delimited .txt with DTW's two header rows (object property names, then database column names) and one data
# row. The flow proposes the SAP code from the request number, so it is unique and never clashes with existing
# codes (C1..., V2..., A-1...). Segment / payment terms go in as text; real SAP uses numeric codes (MDM maps them).
TAB, CRLF = "decodeUriComponent('%09')", "decodeUriComponent('%0D%0A')"


def t(col):  # noqa: F811 - from here on, values come from the request as approved
    """The approved request (re-read after stage 2), so edits made after a Request changes are included."""
    return f"outputs('Check_after_stage_2')?['body/{REQ[col]}']"


# Payment and bank details are read again now, not reused from submission, so an edit made after a Request changes
# (e.g. Finance asking for a lower credit limit) is what goes into SAP
sens = "first(outputs('Get_sensitive_final')?['body/value'])"
rid = "triggerBody()?['Title']"
req_no = "triggerBody()?['ID']"


def txt(expr):
    """A value as single-line text (tabs and line breaks would break the row)."""
    return (f"replace(replace(replace(string(coalesce({expr}, '')), {TAB}, ' '), "
            f"decodeUriComponent('%0D'), ' '), decodeUriComponent('%0A'), ' ')")


def yes_no(expr):
    return f"if(equals({expr}, true), 'tYES', 'tNO')"


SAP_CODE = (f"if(equals({t('RequestType')}, 'Customer'), concat('C2', formatNumber({req_no}, '0000')), "
            f"if(equals({t('RequestType')}, 'Vendor'), concat('V3', formatNumber({req_no}, '000')), "
            f"if(equals({t('RequestType')}, 'Item'), concat({t('ProductFamily')}, '-', string(add(5000, {req_no}))), "
            f"concat({t('Entity')}, '-', toUpper(substring(concat({t('Department')}, 'XXX'), 0, 3)), string({req_no})))))")
code = "outputs('SAP_code')"

# (DTW object, file object name, [(property, database column, value expression)])
DTW = {
    "Customer": ("oBusinessPartners", "BusinessPartners", [
        ("RecordKey", "RecordKey", "'1'"), ("CardCode", "CardCode", code),
        ("CardName", "CardName", txt(t("CustomerName"))), ("CardType", "CardType", "'cCustomer'"),
        ("GroupCode", "GroupCode", txt(t("Segment"))), ("FederalTaxID", "LicTradNum", txt(t("RegistrationNo"))),
        ("Address", "Address", txt(t("BillingAddress"))), ("Country", "Country", txt(t("Country"))),
        ("EmailAddress", "E_Mail", txt(t("ContactEmail"))),
        ("PayTermsGrpCode", "GroupNum", txt(f"{sens}?['{SENS['PaymentTerms']}']")),
        ("CreditLimit", "CreditLine", txt(f"{sens}?['{SENS['CreditLimit']}']")),
        ("U_Entity", "U_Entity", txt(t("Entity"))), ("U_OneRecordID", "U_OneRecordID", rid)]),
    "Vendor": ("oBusinessPartners", "BusinessPartners", [
        ("RecordKey", "RecordKey", "'1'"), ("CardCode", "CardCode", code),
        ("CardName", "CardName", txt(t("VendorName"))), ("CardType", "CardType", "'cSupplier'"),
        ("FederalTaxID", "LicTradNum", txt(t("TaxID"))), ("Country", "Country", txt(t("Country"))),
        ("PayTermsGrpCode", "GroupNum", txt(f"{sens}?['{SENS['PaymentTerms']}']")),
        ("DefaultBankCode", "BankCode", txt(f"{sens}?['field_4']")),
        ("DefaultAccount", "DflAccount", txt(f"{sens}?['field_5']")),
        ("U_Regulated", "U_Regulated", yes_no(t("SuppliesRegulatedGoods"))),
        ("U_ISO13485", "U_ISO13485", txt(t("ISO13485CertNo"))),
        ("U_Entity", "U_Entity", txt(t("Entity"))), ("U_OneRecordID", "U_OneRecordID", rid)]),
    "Item": ("oItems", "Items", [
        ("RecordKey", "RecordKey", "'1'"), ("ItemCode", "ItemCode", code),
        ("ItemName", "ItemName", txt(t("ItemDescription"))),
        ("ItemsGroupCode", "ItmsGrpCod", txt(t("ProductFamily"))),
        ("InventoryUOM", "InvntryUom", txt(t("UnitOfMeasure"))),
        ("SupplierCatalogNo", "SuppCatNum", txt(t("ManufacturerPartNo"))),
        ("U_HSCode", "U_HSCode", txt(t("HSCode"))), ("U_Regulated", "U_Regulated", yes_no(t("IsRegulated"))),
        ("U_LicenceNo", "U_LicenceNo", txt(t("RegulatoryLicenceNo"))),
        ("U_ShelfLifeMonths", "U_ShelfLifeMonths", txt(t("ShelfLifeMonths"))),
        ("U_Entity", "U_Entity", txt(t("Entity"))), ("U_OneRecordID", "U_OneRecordID", rid)]),
    "Cost Center": ("oProfitCenters", "ProfitCenters", [
        ("RecordKey", "RecordKey", "'1'"), ("CenterCode", "PrcCode", code),
        ("CenterName", "PrcName", txt(t("CostCenterName"))), ("InWhichDimension", "DimCode", "'1'"),
        ("U_Department", "U_Department", txt(t("Department"))), ("U_Owner", "U_Owner", txt(t("Owner"))),
        ("U_BudgetYear", "U_BudgetYear", txt(t("BudgetYear"))),
        ("U_Entity", "U_Entity", txt(t("Entity"))), ("U_OneRecordID", "U_OneRecordID", rid)]),
}


def dtw_body(cols):
    row = lambda xs: f"join(createArray({', '.join(xs)}), {TAB})"
    return (f"@concat({row([repr(c[0]) for c in cols])}, {CRLF}, {row([repr(c[1]) for c in cols])}, {CRLF}, "
            f"{row([c[2] for c in cols])}, {CRLF})")


# Last check before anything is written for SAP: the request and its sensitive row must still be exactly the version
# every approval was given for. If not (edited in SharePoint after the last approval), no SAP file; on hold instead.
actions["Get_sensitive_final"] = after(get_sensitive(), "If_rejected_after_stage_2")
actions["If_changed_after_approval"] = after({
    **condition(f"not(equals({fingerprint('Check_after_stage_2', 'Get_sensitive_final')}, variables('Pinned')))", {
        **hold_request("final", "After the last approval: the request (version "
                                "@{outputs('Check_after_stage_2')?['body/{VersionNumber}']}) or its payment / bank "
                                "details no longer match the version that was approved. No SAP file was written."),
        "Stop_changed_after_approval": after({"type": "Terminate", "inputs": {"runStatus": "Succeeded"}},
                                             "Tell_requestor_on_hold_final"),
    })}, "Get_sensitive_final")
actions["Log_version_approved"] = after(log_row(
    "@triggerBody()?['Title']", "OneRecord", "System", "Version check passed",
    "The SAP file matches the version every approver approved (request version "
    "@{outputs('Check_after_stage_2')?['body/{VersionNumber}']})"), "If_changed_after_approval")
actions["SAP_code"] = after({"type": "Compose", "inputs": f"@{SAP_CODE}"}, "Log_version_approved")
actions["SAP_file_name"] = after({"type": "Compose", "inputs":
    "@concat(triggerBody()?['Title'], '_', " + "".join(
        f"if(equals({t('RequestType')}, '{k}'), '{v[1]}', " for k, v in DTW.items()) + "'Record'"
    + ")" * len(DTW) + ", '_DTW.txt')"}, "SAP_code")
cases = {}
for k, (obj, _, cols) in DTW.items():
    key = k.replace(" ", "_")
    cases[key] = {"case": k, "actions": {f"Save_DTW_{key}": sp(
        "CreateFile", folderPath="/Shared Documents/SAP_Imports", name="@{outputs('SAP_file_name')}",
        body=dtw_body(cols))}}
actions["Write_SAP_import_file"] = after({"type": "Switch", "expression": f"@{t('RequestType')}",
                                          "cases": cases, "default": {"actions": {}}}, "SAP_file_name")
# Approved: add the record to its master list straight away (as "Pending SAP import"), so the next request's
# duplicate check sees it, and hand over to MDM to import the file. The status only says "Created in SAP" once MDM
# confirms the import in the app (My requests > Mark as created in SAP).
PENDING_SAP = "Pending SAP import"
today = "@{formatDateTime(utcNow(), 'yyyy-MM-dd')}"
MASTER = {  # request type -> (list, column map, {master column: value})
    "Customer": ("CustomerMaster", CUST, {
        "CustomerName": f"@{{{t('CustomerName')}}}", "NormalizedName": f"@{{{t('MatchKey')}}}",
        "Country": f"@{{{t('Country')}}}", "Address": f"@{{{t('BillingAddress')}}}",
        "RegistrationNo": f"@{{{t('RegistrationNo')}}}", "Segment": f"@{{{t('Segment')}}}",
        "CreatedByEntity": f"@{{{t('Entity')}}}", "MatchKey": f"@{{{t('MatchKey')}}}", "IDKey": f"@{{{t('IDKey')}}}"}),
    "Item": ("ItemMaster", ITEM, {
        "Description": f"@{{{t('ItemDescription')}}}", "NormalizedName": f"@{{{t('MatchKey')}}}",
        "ProductFamily": f"@{{{t('ProductFamily')}}}", "OwningEntity": f"@{{{t('Entity')}}}",
        "UOM": f"@{{{t('UnitOfMeasure')}}}", "Regulated": f"@equals({t('IsRegulated')}, true)",
        "ManufacturerPartNo": f"@{{{t('ManufacturerPartNo')}}}", "MatchKey": f"@{{{t('MatchKey')}}}",
        "IDKey": f"@{{{t('IDKey')}}}"}),
    "Vendor": ("VendorMaster", VEND, {
        "VendorName": f"@{{{t('VendorName')}}}", "Country": f"@{{{t('Country')}}}",
        "CreatedByEntity": f"@{{{t('Entity')}}}", "CreatedDate": today, "TaxID": f"@{{{t('TaxID')}}}",
        "MatchKey": f"@{{{t('MatchKey')}}}", "IDKey": f"@{{{t('IDKey')}}}"}),
    "Cost Center": ("CostCentres", CC, {
        "CostCentreName": f"@{{{t('CostCenterName')}}}", "Entity": f"@{{{t('Entity')}}}",
        "Department": f"@{{{t('Department')}}}", "Owner": f"@{{{t('Owner')}}}"}),
}


def master_switch(name, build):
    return {"type": "Switch", "runAfter": {}, "expression": f"@{t('RequestType')}", "default": {"actions": {}},
            "cases": {k.replace(" ", "_"): {"case": k, "actions": build(k, *v)} for k, v in MASTER.items()}}


def add_case(kind, lst, cols, values):
    key = kind.replace(" ", "_")
    fields = {f"item/{cols[c]}": v for c, v in values.items()}
    fields.update({"item/Title": "@{outputs('SAP_code')}", f"item/{cols['SAPStatus']}": PENDING_SAP})
    return {f"Add_{key}_record": sp("PostItem", lst, **fields),
            f"Remember_{key}_row": after({"type": "SetVariable", "inputs": {
                "name": "MasterRowID", "value": f"@outputs('Add_{key}_record')?['body/ID']"}}, f"Add_{key}_record")}


poll = "Poll_SAP_status"
sap_now = f"outputs('{poll}')?['body/{REQ['SAPCode']}']"


def live_case(kind, lst, cols, values):
    return {f"Mark_{kind.replace(' ', '_')}_in_SAP": sp("PatchItem", lst, **{
        "id": "@variables('MasterRowID')", "item/Title": f"@{{{sap_now}}}", f"item/{cols['SAPStatus']}": "In SAP"})}


mdm_email = f"first(body('Find_MDM_analyst'))?['{ROLE['PersonEmail']}']"
actions["Add_to_master_list"] = after(master_switch("Add_to_master_list", add_case), "Write_SAP_import_file")
actions["Mark_ready_for_SAP"] = update_request(
    ["Add_to_master_list"], Status="Ready for SAP import", SAPCode="@{outputs('SAP_code')}",
    CurrentStage="Approved. MDM to import SAP_Imports/@{outputs('SAP_file_name')} into SAP B1 "
                 "(proposed code @{outputs('SAP_code')})")
actions["Log_SAP_file"] = after(log_row(
    "@triggerBody()?['Title']", "OneRecord", "System", "SAP import file created",
    "SAP_Imports/@{outputs('SAP_file_name')} (proposed code @{outputs('SAP_code')}); added to the master list as "
    f"{PENDING_SAP}"), "Mark_ready_for_SAP")
actions["Tell_requestor_approved"] = teams_to_requestor(
    "Good news: your request @{triggerBody()?['Title']} was approved by every approver. The MDM team is now "
    "importing it into SAP B1 (proposed code @{outputs('SAP_code')}). You'll get a message when it's live.",
    "Log_SAP_file")
actions["Tell_MDM_to_import"] = after(teams_chat(
    f"@{{{mdm_email}}}",
    "@{triggerBody()?['Title']} is approved. Import SAP_Imports/@{outputs('SAP_file_name')} into SAP B1 with the "
    "Data Transfer Workbench, then open it with the link below and press Mark as created in SAP.<br>"
    + REQUEST_LINK), "Tell_requestor_approved")
# Wait (checking every 5 minutes, up to about 17 days) for MDM to confirm the import
actions["Wait_for_SAP_import"] = after({
    "type": "Until", "expression": f"@equals(outputs('{poll}')?['body/{REQ['Status']}'], 'Created in SAP')",
    "limit": {"count": 5000, "timeout": "P30D"},
    "actions": {
        "Wait_5_minutes_SAP": {"type": "Wait", "runAfter": {}, "inputs": {"interval": {"count": 5, "unit": "Minute"}}},
        poll: after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"), "Wait_5_minutes_SAP"),
    }}, "Tell_MDM_to_import")
actions["After_SAP_import"] = {
    **condition(f"equals(outputs('{poll}')?['body/{REQ['Status']}'], 'Created in SAP')", {
        "Update_master_list": master_switch("Update_master_list", live_case),
        "Mark_completed": update_request(
            ["Update_master_list"], CompletedAt="@utcNow()",
            CurrentStage=f"Created in SAP as @{{{sap_now}}}"),
        "Log_created_in_SAP": after(log_row(
            "@triggerBody()?['Title']", f"@{{outputs('{poll}')?['body/Editor/Email']}}", "MDM Analyst",
            "Created in SAP", f"SAP code @{{{sap_now}}}; master list updated"), "Mark_completed"),
        "Tell_requestor_live": teams_to_requestor(
            f"Your request @{{triggerBody()?['Title']}} is live in SAP B1 as @{{{sap_now}}}. You can use it now.",
            "Log_created_in_SAP"),
    }, {
        "Log_import_not_confirmed": log_row(
            "@triggerBody()?['Title']", "OneRecord", "System", "SAP import not confirmed",
            "Still Ready for SAP import after the waiting period"),
        "Tell_MDM_not_confirmed": after(teams_chat(
            f"@{{{mdm_email}}}",
            "@{triggerBody()?['Title']} has been ready for SAP import for over two weeks and hasn't been marked as "
            "created in SAP. Please import it or reject it.<br>" + REQUEST_LINK), "Log_import_not_confirmed"),
    }),
    "runAfter": {"Wait_for_SAP_import": ["Succeeded", "Failed", "TimedOut"]},
}

flow = definition({"When_a_request_is_submitted": {
    "type": "OpenApiConnection", "recurrence": {"interval": 1, "frequency": "Minute"},
    "splitOn": "@triggerOutputs()?['body/value']",
    "inputs": {"parameters": {"dataset": SITE, "table": LISTS["Requests"]},
               "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                        "connectionName": "shared_sharepointonline", "operationId": "GetOnNewItems"},
               "authentication": "@parameters('$authentication')"}}}, actions)

if __name__ == "__main__":
    write_package(OUT, NAME, "Parallel approvals for OneRecord master data requests", flow,
                  ["shared_sharepointonline", "shared_approvals", "shared_teams"])
    print(OUT, "actions:", len(actions))
