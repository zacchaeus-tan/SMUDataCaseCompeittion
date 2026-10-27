"""The request workflow pages: the live OneRecord Power App, embedded. Nothing here is a copy of it. Submitting a
request writes to the SharePoint lists and starts the real Power Automate flows (parallel approvals in Teams,
reminders, escalation, the SAP DTW file)."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from onerecord.config import POWER_APP_URL

from . import common as c

APP_HEIGHT = 900
FLOW_IMAGE = Path(__file__).resolve().parent.parent / "docs" / "images" / "process_flow.png"


def _embed(screen, section, headline, intro):
    c.header(section, headline, source="Live · Microsoft 365")
    st.caption(intro)
    # the app's own StartScreen reads ?screen= (powerapps/gen_form.py); hidenavbar drops the Power Apps title bar
    url = f"{POWER_APP_URL}&screen={screen}&hidenavbar=true&source=iframe"
    with st.container(key="card-powerapp"):
        components.iframe(url, height=APP_HEIGHT, scrolling=True)
    st.caption(f"Live app in the team's Microsoft 365 (Power Apps, Power Automate, SharePoint, Teams). It signs you "
               f"in with your own Microsoft 365 account, and what you can do in it follows the app's Roles list, "
               f"not the user picked in this sidebar. Blank, or stuck on sign-in? "
               f"[Open the app in a new tab]({POWER_APP_URL}&screen={screen}). Only accounts in the demo tenant "
               f"can sign in.")


def _after_submit():
    with st.expander("What happens after Submit", expanded=False):
        st.markdown(
            "1. **Route and approve** (Power Automate) picks the approvers from the RoutingRules list and sends "
            "every first-stage approval card **at the same time** in Teams and Outlook. Each approver can approve, "
            "reject or send it back for changes.\n"
            "2. When stage 1 is done, the MDM Analyst approves last. The flow writes a **SAP B1 DTW import file** "
            "with a proposed SAP code and adds the record to the master list as *Pending SAP import*.\n"
            "3. **Reminders and escalation** nudge approvers at 9 AM in their own time zone and re-send a card to "
            "their manager after 4 days.\n"
            "4. Every step goes into the **ApprovalLog**, which you can see in *My requests*.\n"
            "5. Once MDM marks it created in SAP, the new customer's orders count in the regional view.")
        if FLOW_IMAGE.exists():
            st.image(str(FLOW_IMAGE))


def new_request():
    _embed("new", "Requests", "Raise a master-data request",
           "Customer, item, vendor or cost-centre setup. The form shows only the fields that apply, checks formats "
           "and duplicates while you type, and shows who will approve before you submit.")
    _after_submit()


def my_requests():
    _embed("mine", "Requests", "Where my requests stand",
           "Status, who is holding each request, and the full approval timeline from the ApprovalLog. MDM can mark "
           "approved records as created in SAP here.")


def rules():
    _embed("rules", "Requests", "Approval rules, without IT",
           "Add approval steps, form fields, business units, people and product lines in plain words. The flows "
           "read these lists on every request, so a change applies to the next one.")
