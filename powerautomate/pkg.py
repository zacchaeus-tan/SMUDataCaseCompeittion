"""Shared pieces for building importable Power Automate packages (Import > Import Package (Legacy)).

The package layout mirrors a real "Export > Package (.zip)" from this tenant: the flow's resource id in
manifest.json is also its folder name and its entry in Microsoft.Flow/flows/manifest.json, and
connectionsMap.json is keyed by the connection reference name used in the definition.
"""
import json
import uuid
import zipfile

SITE = "https://smu.sharepoint.com/teams/DataCaseCompetition2026"
LISTS = {  # list GUIDs on the team site
    "Requests": "016ebf84-d2d7-4fdc-a51a-8f43c1235b93",
    "SensitiveDetails": "a11b50e7-c929-4440-a0cf-95c32238d6bd",
    "RoutingRules": "b547dfe1-fea2-4297-b06b-87fdcd985c53",
    "Roles": "ddcffdf3-071e-4c53-a7a1-602cbe86ad9e",
    "ApprovalLog": "0420543c-3d28-47c5-9218-2e31486b0932",
    "RequiredFields": "6d7f2d26-8be0-409f-8a85-fbc141d462b1",
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
        "ApproverRole": "field_5", "Stage": "field_6", "SLADays": "field_7", "EscalateAfterDays": "field_8",
        "Active": "field_9"}
ROLE = {"Role": "field_1", "Entity": "field_2", "PersonName": "field_3", "PersonEmail": "field_4",
        "EscalateTo": "field_5", "TimeZone": "field_6"}
LOG = {"RequestID": "field_1", "Timestamp": "field_2", "Actor": "field_3", "ActorRole": "field_4",
       "Action": "field_5", "Detail": "field_6"}
SENS = {"RequestID": "field_1", "PaymentTerms": "field_2", "CreditLimit": "field_3"}
RF = {"RequestType": "field_1", "FieldName": "field_2", "Sensitive": "field_8", "VisibleToRoles": "field_9"}

APIS = {
    "shared_sharepointonline": ("SharePoint",
        "https://static.powerapps.com/resource/ppcr/releases/v1.0.1827/1.0.1827.4913/sharepointonline/icon.png"),
    "shared_approvals": ("Approvals",
        "https://static.powerapps.com/resource/ppcr/releases/v1.0.1826/1.0.1826.4893/approvals/icon.png"),
    "shared_teams": ("Microsoft Teams",
        "https://static.powerapps.com/resource/ppcr/releases/v1.0.1834/1.0.1834.5088/teams/icon.png"),
}


def after(action, *prev):
    action["runAfter"] = {p: ["Succeeded"] for p in prev}
    return action


def sp(op, table=None, **params):
    """A SharePoint connector action."""
    p = {"dataset": SITE}
    if table:
        p["table"] = LISTS[table]
    p.update(params)
    return {"type": "OpenApiConnection", "runAfter": {},
            "inputs": {"parameters": p,
                       "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                                "connectionName": "shared_sharepointonline", "operationId": op},
                       "authentication": "@parameters('$authentication')"}}


def log_row(request_id, actor, role, action, detail):
    """Create an ApprovalLog row (all arguments are flow expressions or literal text)."""
    return sp("PostItem", "ApprovalLog", **{
        "item/Title": request_id, f"item/{LOG['RequestID']}": request_id,
        f"item/{LOG['Timestamp']}": "@utcNow()", f"item/{LOG['Actor']}": actor,
        f"item/{LOG['ActorRole']}": role, f"item/{LOG['Action']}": action, f"item/{LOG['Detail']}": detail})


def teams_chat(recipient, message):
    """A Flow bot chat message in Teams. `recipient` is an email expression."""
    return {"type": "OpenApiConnection", "runAfter": {}, "inputs": {
        "parameters": {"poster": "Flow bot", "location": "Chat with Flow bot",
                       "body/recipient": f"{recipient};", "body/messageBody": f"<p>{message}</p>"},
        "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_teams",
                 "connectionName": "shared_teams", "operationId": "PostMessageToConversation"},
        "authentication": "@parameters('$authentication')"}}


def condition(bool_expr, yes, no=None):
    """An If action testing a boolean expression (written without the leading @)."""
    return {"type": "If", "runAfter": {},
            "expression": {"and": [{"equals": [f"@{bool_expr}", True]}]},
            "actions": yes, "else": {"actions": no or {}}}


def definition(triggers, actions):
    return {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                       "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
        "triggers": triggers, "actions": actions, "outputs": {}}


def write_package(out, name, description, flow_definition, apis):
    """Write a legacy import package containing one flow that uses the given connector keys."""
    new_id = lambda: str(uuid.uuid4())
    flow_name, flow_res = new_id(), new_id()
    api_res = {k: new_id() for k in apis}
    conn_res = {k: new_id() for k in apis}

    resources = {flow_res: {
        "type": "Microsoft.Flow/flows", "suggestedCreationType": "New", "creationType": "Existing, New, Update",
        "details": {"displayName": name}, "configurableBy": "User", "hierarchy": "Root",
        "dependsOn": [r for k in apis for r in (api_res[k], conn_res[k])]}}
    for k in apis:
        display, icon = APIS[k]
        resources[api_res[k]] = {
            "id": f"/providers/Microsoft.PowerApps/apis/{k}", "name": k, "type": "Microsoft.PowerApps/apis",
            "suggestedCreationType": "Existing", "details": {"displayName": display, "iconUri": icon},
            "configurableBy": "System", "hierarchy": "Child", "dependsOn": []}
        resources[conn_res[k]] = {
            "type": "Microsoft.PowerApps/apis/connections", "suggestedCreationType": "Existing",
            "creationType": "Existing", "details": {"displayName": display, "iconUri": icon},
            "configurableBy": "User", "hierarchy": "Child", "dependsOn": [api_res[k]]}
    manifest = {"schema": "1.0",
                "details": {"displayName": name, "description": description,
                            "createdTime": "2026-10-22T12:00:00.0000000Z", "packageTelemetryId": new_id(),
                            "creator": "N/A", "sourceEnvironment": ""},
                "resources": resources}
    flow_def = {
        "name": flow_name, "id": f"/providers/Microsoft.Flow/flows/{flow_name}", "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows", "displayName": name,
            "definition": flow_definition,
            "connectionReferences": {k: {"connectionName": uuid.uuid4().hex, "source": "Embedded",
                                         "id": f"/providers/Microsoft.PowerApps/apis/{k}", "tier": "NotSpecified",
                                         "apiName": k.replace("shared_", ""),
                                         "isProcessSimpleApiReferenceConversionAlreadyDone": False}
                                     for k in apis},
            "flowFailureAlertSubscribed": False, "isManaged": False},
    }
    base = f"Microsoft.Flow/flows/{flow_res}"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("Microsoft.Flow/flows/manifest.json",
                   json.dumps({"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [flow_res]}}))
        z.writestr(f"{base}/definition.json", json.dumps(flow_def))
        z.writestr(f"{base}/apisMap.json", json.dumps({k: api_res[k] for k in apis}))
        z.writestr(f"{base}/connectionsMap.json", json.dumps({k: conn_res[k] for k in apis}))
    return out
