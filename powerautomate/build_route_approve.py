"""Build an importable Power Automate package (Import > Import Package (Legacy)) for the
"OneRecord - Route and approve" flow described in sharepoint/LISTS.md.

Usage: python3 powerautomate/build_route_approve.py   ->  powerautomate/OneRecord-RouteAndApprove.zip
Each approval also writes an "Assigned" row to ApprovalLog, which build_reminders.py relies on.
"""
from pathlib import Path

from pkg import LISTS, LOG, REQ, ROLE, RULE, SENS, SITE, after, definition, log_row, sp, teams_chat, write_package

OUT = Path(__file__).with_name("OneRecord-RouteAndApprove.zip")
NAME = "OneRecord - Route and approve"


def t(col):
    """Trigger (new Requests item) column."""
    return f"triggerBody()?['{REQ[col]}']"


def update_request(prev, **cols):
    params = {"id": "@triggerBody()?['ID']", "item/Title": "@triggerBody()?['Title']"}
    params.update({f"item/{REQ[k]}": v for k, v in cols.items()})
    return after(sp("PatchItem", "Requests", **params), *prev)


def teams_to_requestor(message, *prev):
    return after(teams_chat("@{triggerBody()?['Author']?['Email']}", message), *prev)


NAME_EXPR = f"coalesce({t('CustomerName')}, {t('ItemDescription')}, {t('VendorName')}, {t('CostCenterName')})"


def stage_loop(stage):
    """Filter the active rules for this stage, then one parallel approval per rule."""
    loop = f"Stage_{stage}_approvals"
    approval = f"Stage_{stage}_approval"
    stage_test = (f"less(item()?['{RULE['Stage']}'], 1.5)" if stage == 1
                  else f"greater(item()?['{RULE['Stage']}'], 1.5)")
    where = (
        f"@and(equals(item()?['{RULE['Active']}'], true), {stage_test}, "
        f"or(equals(item()?['{RULE['RequestType']}'], {t('RequestType')}), equals(item()?['{RULE['RequestType']}'], 'Any')), "
        f"or(equals(item()?['{RULE['Entity']}'], 'Any'), equals(item()?['{RULE['Entity']}'], {t('Entity')})), "
        f"or(empty(item()?['{RULE['ConditionField']}']), "
        f"and(equals(item()?['{RULE['ConditionField']}'], 'IsRegulated'), equals({t('IsRegulated')}, true)), "
        f"and(equals(item()?['{RULE['ConditionField']}'], 'SuppliesRegulatedGoods'), equals({t('SuppliesRegulatedGoods')}, true))))"
    )
    role = f"items('{loop}')?['{RULE['ApproverRole']}']"
    first_resp = f"first(outputs('{approval}')?['body/responses'])"
    approver_email = f"@{{first(body('Find_stage_{stage}_approver'))?['{ROLE['PersonEmail']}']}}"
    inner = {
        f"Find_stage_{stage}_approver": {"type": "Query", "runAfter": {}, "inputs": {
            "from": "@outputs('Get_roles')?['body/value']",
            "where": f"@and(equals(item()?['{ROLE['Role']}'], {role}), "
                     f"or(equals(item()?['{ROLE['Entity']}'], 'Any'), equals(item()?['{ROLE['Entity']}'], {t('Entity')})))"}},
        f"Log_stage_{stage}_assigned": after(log_row(
            "@triggerBody()?['Title']", approver_email, f"@{{{role}}}", "Assigned", f"Stage {stage}"),
            f"Find_stage_{stage}_approver"),
        approval: after({"type": "OpenApiConnectionWebhook", "inputs": {
            "parameters": {
                "approvalType": "Basic",
                "WebhookApprovalCreationInput/title":
                    f"@{{triggerBody()?['Title']}}: @{{{t('RequestType')}}} request for @{{{t('Entity')}}} (@{{{role}}} check)",
                "WebhookApprovalCreationInput/assignedTo": approver_email,
                "WebhookApprovalCreationInput/details": (
                    f"**Requested by:** @{{{t('Requestor')}}}\n\n"
                    f"**Name:** @{{{NAME_EXPR}}}\n\n"
                    f"**Country:** @{{{t('Country')}}}\n\n"
                    f"**Duplicate check:** @{{{t('DuplicateCheck')}}} @{{{t('PossibleMatchID')}}}\n\n"
                    f"**Your check:** @{{{role}}} (stage {stage})"),
                "WebhookApprovalCreationInput/itemLink": "@{triggerBody()?['{Link}']}",
                "WebhookApprovalCreationInput/itemLinkDescription": "Open the request in SharePoint",
                "WebhookApprovalCreationInput/enableNotifications": True,
                "WebhookApprovalCreationInput/enableReassignment": True,
            },
            "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_approvals",
                     "connectionName": "shared_approvals", "operationId": "StartAndWaitForAnApproval"},
            "authentication": "@parameters('$authentication')"}}, f"Log_stage_{stage}_assigned"),
        f"Log_stage_{stage}_decision": after(sp("PostItem", "ApprovalLog", **{
            "item/Title": "@triggerBody()?['Title']",
            f"item/{LOG['RequestID']}": "@triggerBody()?['Title']",
            f"item/{LOG['Timestamp']}": "@utcNow()",
            f"item/{LOG['Actor']}": f"@{{{first_resp}?['responder/displayName']}}",
            f"item/{LOG['ActorRole']}": f"@{{{role}}}",
            f"item/{LOG['Action']}": f"@{{outputs('{approval}')?['body/outcome']}}",
            f"item/{LOG['Detail']}": f"Stage {stage}. @{{{first_resp}?['comments']}}",
        }), approval),
        f"If_stage_{stage}_rejected": after({
            "type": "If",
            "expression": {"and": [{"equals": [f"@outputs('{approval}')?['body/outcome']", "Reject"]}]},
            "actions": {f"Mark_rejected_stage_{stage}": update_request(
                [], Status="Rejected", CurrentStage=f"Rejected at @{{{role}}} check (stage {stage})")},
            "else": {"actions": {}},
        }, f"Log_stage_{stage}_decision"),
    }
    return {
        f"Filter_stage_{stage}_rules": {"type": "Query", "runAfter": {}, "inputs": {
            "from": "@outputs('Get_routing_rules')?['body/value']", "where": where}},
        loop: {"type": "Foreach", "runAfter": {}, "foreach": f"@body('Filter_stage_{stage}_rules')",
               "actions": inner, "runtimeConfiguration": {"concurrency": {"repetitions": 20}}},
    }


def rejected_gate(stage, prev):
    """After a stage: re-read the request; if any approver rejected, tell the requestor and stop."""
    check = f"Check_after_stage_{stage}"
    return {
        check: after(sp("GetItem", "Requests", id="@triggerBody()?['ID']"), prev),
        f"If_rejected_after_stage_{stage}": after({
            "type": "If",
            "expression": {"and": [{"equals": [f"@outputs('{check}')?['body/{REQ['Status']}']", "Rejected"]}]},
            "actions": {
                f"Tell_requestor_rejected_{stage}": teams_to_requestor(
                    "Your request @{triggerBody()?['Title']} was rejected. Open the Approvals app in Teams to see who rejected it and why."),
                f"Stop_after_stage_{stage}": after({"type": "Terminate", "inputs": {"runStatus": "Succeeded"}},
                                                   f"Tell_requestor_rejected_{stage}"),
            },
            "else": {"actions": {}},
        }, check),
    }


actions = {}
actions["Get_routing_rules"] = sp("GetItems", "RoutingRules")
actions["Get_roles"] = after(sp("GetItems", "Roles"), "Get_routing_rules")

s1 = stage_loop(1)
actions["Filter_stage_1_rules"] = after(s1["Filter_stage_1_rules"], "Get_roles")
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

# Approved: build the SAP Business One import file
actions["Get_sensitive_details"] = after(sp(
    "GetItems", "SensitiveDetails", **{"$filter": f"{SENS['RequestID']} eq '@{{triggerBody()?['Title']}}'"}),
    "If_rejected_after_stage_2")
sens = f"first(outputs('Get_sensitive_details')?['body/value'])"
record = {"RequestID": "@{triggerBody()?['Title']}"}
record.update({k: f"@{{{t(k)}}}" for k in ["RequestType", "Entity", "Country"]})
record["Name"] = f"@{{{NAME_EXPR}}}"
record.update({k: f"@{{{t(k)}}}" for k in [
    "RegistrationNo", "BillingAddress", "ContactEmail", "Segment", "ProductFamily", "UnitOfMeasure", "HSCode",
    "IsRegulated", "RegulatoryLicenceNo", "ShelfLifeMonths", "TaxID", "SuppliesRegulatedGoods", "ISO13485CertNo",
    "Department", "Owner", "BudgetYear"]})
record["PaymentTerms"] = f"@{{{sens}?['{SENS['PaymentTerms']}']}}"
record["CreditLimit"] = f"@{{{sens}?['{SENS['CreditLimit']}']}}"
actions["SAP_import_record"] = after({"type": "Compose", "inputs": record}, "Get_sensitive_details")
actions["Create_CSV_table"] = after({"type": "Table", "inputs": {
    "from": "@createArray(outputs('SAP_import_record'))", "format": "CSV"}}, "SAP_import_record")
actions["Save_SAP_import_file"] = after(sp(
    "CreateFile", folderPath="/Shared Documents/SAP_Imports",
    name="@{triggerBody()?['Title']}-SAP-import.csv", body="@body('Create_CSV_table')"), "Create_CSV_table")
actions["Mark_created_in_SAP"] = update_request(
    ["Save_SAP_import_file"], Status="Created in SAP", CompletedAt="@utcNow()",
    CurrentStage="Approved. SAP import file: SAP_Imports/@{triggerBody()?['Title']}-SAP-import.csv")
actions["Log_SAP_file"] = after(sp("PostItem", "ApprovalLog", **{
    "item/Title": "@triggerBody()?['Title']", f"item/{LOG['RequestID']}": "@triggerBody()?['Title']",
    f"item/{LOG['Timestamp']}": "@utcNow()", f"item/{LOG['Actor']}": "OneRecord",
    f"item/{LOG['ActorRole']}": "System", f"item/{LOG['Action']}": "SAP import file created",
    f"item/{LOG['Detail']}": "SAP_Imports/@{triggerBody()?['Title']}-SAP-import.csv"}), "Mark_created_in_SAP")
actions["Tell_requestor_approved"] = teams_to_requestor(
    "Good news: your request @{triggerBody()?['Title']} was approved by every approver and the SAP import file has been created.",
    "Log_SAP_file")

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
