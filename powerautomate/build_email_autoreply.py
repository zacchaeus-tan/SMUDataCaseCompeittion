"""Build "OneRecord - Email auto-reply" as an importable package (Import > Import Package (Legacy)).

Usage: python3 powerautomate/build_email_autoreply.py  ->  powerautomate/OneRecord-EmailAutoReply.zip

Closes the old email route. When a staff member emails a master data request to the mailbox this flow watches
(the MDM shared mailbox in production; a teammate's inbox for the demo), it replies with the request form's link
and the "no form, no record" rule. Detection uses the same phrases as onerecord/classify.py. Standard connector
(Office 365 Outlook) only, so no premium licence. Set APP_URL and INTERNAL_DOMAIN in pkg.py first.
"""
from pathlib import Path

from pkg import APP_URL, INTERNAL_DOMAIN, after, condition, definition, write_package

OUT = Path(__file__).with_name("OneRecord-EmailAutoReply.zip")
NAME = "OneRecord - Email auto-reply"
APIS = ["shared_office365"]

# Phrases that mark a master data request (kept in line with the mdm_request signals in onerecord/classify.py)
PHRASES = ["new customer", "new vendor", "new supplier", "new item", "item code", "customer code", "vendor code",
           "set up a customer", "set up a vendor", "set up an item", "setup customer", "create customer",
           "create vendor", "create item", "supplier registration", "vendor registration", "register supplier",
           "new cost centre", "new cost center", "master data", "mdm request"]


def o365(op, **params):
    return {"type": "OpenApiConnection", "runAfter": {}, "inputs": {
        "parameters": params,
        "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_office365",
                 "connectionName": "shared_office365", "operationId": op},
        "authentication": "@parameters('$authentication')"}}


subject = "triggerOutputs()?['body/subject']"
sender = "toLower(coalesce(triggerOutputs()?['body/from'], ''))"
text = f"toLower(concat(coalesce({subject}, ''), ' ', coalesce(triggerOutputs()?['body/bodyPreview'], '')))"
looks_like_request = "or(" + ", ".join(f"contains({text}, '{ph}')" for ph in PHRASES) + ")"
# Never answer our own replies (their subject says OneRecord), out-of-office messages or non-staff senders
should_reply = (f"and({looks_like_request}, endsWith({sender}, '{INTERNAL_DOMAIN}'), "
                f"not(contains(toLower(coalesce({subject}, '')), 'onerecord')), "
                f"not(startsWith(toLower(coalesce({subject}, '')), 'automatic reply')))")

BODY = (
    "<p>Hi,</p>"
    "<p>Thanks for your email. New customer, item, vendor and cost centre requests now go through the "
    "<b>OneRecord request form</b>. It shows only the fields your request needs, checks for duplicates while you "
    "type, sends it to the right approvers at the same time, and lets you see where it stands at any moment.</p>"
    f"<p><a href=\"{APP_URL}\">Open the OneRecord request form</a> (about 3 minutes).</p>"
    "<p>Requests sent by email aren't set up in SAP. If you can't use the form, reply to this email and the MDM "
    "team will help you.</p>"
    "<p>MDM team, Lives Group</p>"
)

actions = {
    "If_master_data_request": condition(should_reply, {
        "Reply_with_form_link": o365(
            "SendEmailV2", **{
                "emailMessage/To": "@{triggerOutputs()?['body/from']}",
                "emailMessage/Subject": "RE: @{triggerOutputs()?['body/subject']} (please use the OneRecord form)",
                "emailMessage/Body": BODY,
                "emailMessage/Importance": "Normal",
            }),
    }),
}

flow = definition({"When_a_new_email_arrives": {
    "type": "OpenApiConnectionNotification",
    "splitOn": "@triggerOutputs()?['body/value']",
    "inputs": {"parameters": {"folderPath": "Inbox", "importance": "Any", "fetchOnlyWithAttachment": False,
                              "includeAttachments": False},
               "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_office365",
                        "connectionName": "shared_office365", "operationId": "OnNewEmailV3"},
               "authentication": "@parameters('$authentication')"}}}, actions)

if __name__ == "__main__":
    write_package(OUT, NAME, "Replies to emailed master data requests with the OneRecord form link", flow, APIS)
    print(OUT)
