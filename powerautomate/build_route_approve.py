"""Build an importable Power Automate package (Import > Import Package (Legacy)) for the
"OneRecord - Route and approve" flow described in sharepoint/LISTS.md.

Usage: python3 powerautomate/build_route_approve.py   ->  powerautomate/OneRecord-RouteAndApprove.zip
"""
import json
import uuid
import zipfile
from pathlib import Path

OUT = Path(__file__).with_name("OneRecord-RouteAndApprove.zip")
NAME = "OneRecord - Route and approve"
SITE = "https://smu.sharepoint.com/teams/DataCaseCompetition2026"
LISTS = {  # list GUIDs on the team site
    "Requests": "016ebf84-d2d7-4fdc-a51a-8f43c1235b93",
    "SensitiveDetails": "a11b50e7-c929-4440-a0cf-95c32238d6bd",
    "RoutingRules": "b547dfe1-fea2-4297-b06b-87fdcd985c53",
    "Roles": "ddcffdf3-071e-4c53-a7a1-602cbe86ad9e",
    "ApprovalLog": "0420543c-3d28-47c5-9218-2e31486b0932",
}
# SharePoint internal column names (lists were created from CSV, so columns are field_1..n in CSV order)
REQ = {"RequestType": "field_1", "Entity": "field_2", "Country": "field_3", "Requestor": "field_4",
       "Status": "field_5", "CurrentStage": "field_6", "CompletedAt": "field_8", "CustomerName": "field_9",
       "RegistrationNo": "field_10", "BillingAddress": "field_11", "ContactEmail": "ContactEmail",
       "Segment": "field_13", "ItemDescription": "field_14", "ProductFamily": "field_15",
       "UnitOfMeasure": "field_16", "HSCode": "field_17", "IsRegulated": "field_18",
       "RegulatoryLicenceNo": "field_19", "ShelfLifeMonths": "field_20", "VendorName": "field_21",
       "TaxID": "field_22", "SuppliesRegulatedGoods": "field_23", "ISO13485CertNo": "field_24",
       "CostCenterName": "field_25", "Department": "field_26", "Owner": "field_27", "BudgetYear": "field_28",
       "DuplicateCheck": "field_29", "PossibleMatchID": "field_30", "SAPCode": "field_31"}
RULE = {"RequestType": "field_1", "Entity": "field_2", "ConditionField": "field_3", "ConditionValue": "field_4",
        "ApproverRole": "field_5", "Stage": "field_6", "Active": "field_9"}
ROLE = {"Role": "field_1", "Entity": "field_2", "PersonName": "field_3", "PersonEmail": "field_4"}
LOG = {"RequestID": "field_1", "Timestamp": "field_2", "Actor": "field_3", "ActorRole": "field_4",
       "Action": "field_5", "Detail": "field_6"}
SENS = {"RequestID": "field_1", "PaymentTerms": "field_2", "CreditLimit": "field_3"}

APIS = {
    "shared_sharepointonline": "SharePoint",
    "shared_approvals": "Approvals",
    "shared_teams": "Microsoft Teams",
}


def t(col):
    """Trigger (new Requests item) column."""
    return f"triggerBody()?['{REQ[col]}']"


def sp(op, table=None, **params):
    p = {"dataset": SITE}
    if table:
        p["table"] = LISTS[table]
    p.update(params)
    return {"type": "OpenApiConnection", "runAfter": {},
            "inputs": {"parameters": p,
                       "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                                "connectionName": "shared_sharepointonline", "operationId": op},
                       "authentication": "@parameters('$authentication')"}}


def after(action, *prev):
    action["runAfter"] = {p: ["Succeeded"] for p in prev}
    return action


def update_request(prev, **cols):
    params = {"id": "@triggerBody()?['ID']", "item/Title": "@triggerBody()?['Title']"}
    params.update({f"item/{REQ[k]}": v for k, v in cols.items()})
    return after(sp("PatchItem", "Requests", **params), *prev)


def teams_to_requestor(message, *prev):
    return after({"type": "OpenApiConnection", "inputs": {
        "parameters": {"poster": "Flow bot", "location": "Chat with Flow bot",
                       "body/recipient": "@{triggerBody()?['Author']?['Email']};",
                       "body/messageBody": f"<p>{message}</p>"},
        "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_teams",
                 "connectionName": "shared_teams", "operationId": "PostMessageToConversation"},
        "authentication": "@parameters('$authentication')"}}, *prev)


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
    inner = {
        f"Find_stage_{stage}_approver": {"type": "Query", "runAfter": {}, "inputs": {
            "from": "@outputs('Get_roles')?['body/value']",
            "where": f"@and(equals(item()?['{ROLE['Role']}'], {role}), "
                     f"or(equals(item()?['{ROLE['Entity']}'], 'Any'), equals(item()?['{ROLE['Entity']}'], {t('Entity')})))"}},
        approval: after({"type": "OpenApiConnectionWebhook", "inputs": {
            "parameters": {
                "approvalType": "Basic",
                "WebhookApprovalCreationInput/title":
                    f"@{{triggerBody()?['Title']}}: @{{{t('RequestType')}}} request for @{{{t('Entity')}}} (@{{{role}}} check)",
                "WebhookApprovalCreationInput/assignedTo":
                    f"@{{first(body('Find_stage_{stage}_approver'))?['{ROLE['PersonEmail']}']}}",
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
            "authentication": "@parameters('$authentication')"}}, f"Find_stage_{stage}_approver"),
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

definition = {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                   "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
    "triggers": {"When_a_request_is_submitted": {
        "type": "OpenApiConnection", "recurrence": {"interval": 1, "frequency": "Minute"},
        "splitOn": "@triggerOutputs()?['body/value']",
        "inputs": {"parameters": {"dataset": SITE, "table": LISTS["Requests"]},
                   "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                            "connectionName": "shared_sharepointonline", "operationId": "GetOnNewItems"},
                   "authentication": "@parameters('$authentication')"}}},
    "actions": actions,
}

# ---------------------------------------------------------------------------- package files
# Layout mirrors a real "Export > Package (.zip)" from this tenant: the flow's resource id in manifest.json is
# also its folder name and its entry in Microsoft.Flow/flows/manifest.json.
ICONS = {
    "shared_sharepointonline": "https://static.powerapps.com/resource/ppcr/releases/v1.0.1827/1.0.1827.4913/sharepointonline/icon.png",
    "shared_approvals": "https://static.powerapps.com/resource/ppcr/releases/v1.0.1826/1.0.1826.4893/approvals/icon.png",
    "shared_teams": "https://static.powerapps.com/resource/ppcr/releases/v1.0.1834/1.0.1834.5088/teams/icon.png",
}
new_id = lambda: str(uuid.uuid4())
flow_name = new_id()   # the flow's own name inside definition.json
flow_res = new_id()    # package resource id = folder name
api_res = {k: new_id() for k in APIS}
conn_res = {k: new_id() for k in APIS}

resources = {flow_res: {
    "type": "Microsoft.Flow/flows", "suggestedCreationType": "New", "creationType": "Existing, New, Update",
    "details": {"displayName": NAME}, "configurableBy": "User", "hierarchy": "Root",
    "dependsOn": [r for k in APIS for r in (api_res[k], conn_res[k])]}}
for k, display in APIS.items():
    resources[api_res[k]] = {
        "id": f"/providers/Microsoft.PowerApps/apis/{k}", "name": k, "type": "Microsoft.PowerApps/apis",
        "suggestedCreationType": "Existing", "details": {"displayName": display, "iconUri": ICONS[k]},
        "configurableBy": "System", "hierarchy": "Child", "dependsOn": []}
    resources[conn_res[k]] = {
        "type": "Microsoft.PowerApps/apis/connections", "suggestedCreationType": "Existing",
        "creationType": "Existing", "details": {"displayName": display, "iconUri": ICONS[k]},
        "configurableBy": "User", "hierarchy": "Child", "dependsOn": [api_res[k]]}
manifest = {"schema": "1.0",
            "details": {"displayName": NAME, "description": "Parallel approvals for OneRecord master data requests",
                        "createdTime": "2026-10-22T10:30:00.0000000Z", "packageTelemetryId": new_id(),
                        "creator": "N/A", "sourceEnvironment": ""},
            "resources": resources}

definition["outputs"] = {}
flow_def = {
    "name": flow_name, "id": f"/providers/Microsoft.Flow/flows/{flow_name}", "type": "Microsoft.Flow/flows",
    "properties": {
        "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows", "displayName": NAME,
        "definition": definition,
        "connectionReferences": {k: {"connectionName": uuid.uuid4().hex, "source": "Embedded",
                                     "id": f"/providers/Microsoft.PowerApps/apis/{k}", "tier": "NotSpecified",
                                     "apiName": k.replace("shared_", ""),
                                     "isProcessSimpleApiReferenceConversionAlreadyDone": False}
                                 for k in APIS},
        "flowFailureAlertSubscribed": False, "isManaged": False},
}

base = f"Microsoft.Flow/flows/{flow_res}"
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("manifest.json", json.dumps(manifest))
    z.writestr("Microsoft.Flow/flows/manifest.json",
               json.dumps({"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [flow_res]}}))
    z.writestr(f"{base}/definition.json", json.dumps(flow_def))
    z.writestr(f"{base}/apisMap.json", json.dumps({k: api_res[k] for k in APIS}))
    # keyed by connection reference name (as used in the definition's connectionReferences)
    z.writestr(f"{base}/connectionsMap.json", json.dumps({k: conn_res[k] for k in APIS}))
print(OUT, "actions:", len(actions))
