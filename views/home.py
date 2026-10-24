import streamlit as st

from . import common as c


def render():
    c.header("OneRecord", "Clean master data at the point of entry, faster setup, and a five-country growth view "
                          "you can trust")
    d, q = c.raw(), c.data_quality()
    f = c.forecasts()
    from onerecord.forecast import wape
    ab = f["backtest"][f["backtest"]["product"] != "C"]
    dup_share = (q["clusters"].record_id != q["clusters"].golden_id).mean()
    err_chg = wape(ab, "calendar_model") / wape(ab, "baseline_ma6") - 1
    cmp = c.regional()["compare"]
    c.kpi_row([
        c.kpi("Time to SAP today", d["requests"].cycle_days.median(), decimals=1, suffix=" days",
              help="Median, email process"),
        c.kpi("Customer records that are duplicates", dup_share * 100, suffix="%"),
        c.kpi("Forecast error vs 6-month average", err_chg * 100, suffix="%", tone=c.tone(err_chg, up_is_good=False)),
        c.kpi("False drop-off alarms removed", len(cmp["raw_drop"]) - len(cmp["clean_drop"])),
    ])

    left, right = st.columns(2)
    with left:
        st.markdown("##### Workflow mock-up")
        st.markdown(
            "A working copy of the Microsoft 365 build. A requestor fills in a form that only asks for the fields "
            "that apply and checks for duplicates while they type. Every approver gets a card at the same time, with "
            "reminders and escalation if nobody responds. The MDM team does a final check and gets a file to load "
            "into SAP B1. Every step is logged, and the rules behind it are tables the MDM team edits themselves.")
    with right:
        st.markdown("##### Regional business view")
        st.markdown(
            "What clean data makes possible: growth across the five countries, a forecast that beats the 6-month "
            "average, the customers sales should call this quarter, and the business case for the build.")
        st.caption("Use the sidebar to switch between people (requestors, approvers, the MDM team) and to move the "
                   "demo clock forward so reminders and escalation fire.")
    st.markdown("##### Prototype and Microsoft 365")
    st.dataframe({
        "This prototype": ["New request form", "Approvals", "Reminders and escalation", "Rules, roles and log",
                           "SAP import file", "Regional business view", "Email sorting AI step",
                           "AI action brief (Phase 2)"],
        "Production build": ["Power Apps canvas app in a Teams tab", "Power Automate approvals in Teams and Outlook",
                             "Scheduled Power Automate flow", "SharePoint lists (standard licence)",
                             "Power Automate 'Create CSV table' in SAP DTW format", "Power BI in a Teams tab",
                             "Power Automate AI prompt (AI Builder)",
                             "Monthly Power Automate flow with an AI prompt, posting to the sales channel in Teams"],
    }, hide_index=True, width="stretch")
    st.caption("All data is synthetic (no client data was provided). See data/README.md for what was planted and why.")
