import streamlit as st

from . import common as c


def render():
    st.title("OneRecord")
    st.markdown("#### Clean master data at the point of entry → faster setup → a five-country growth view you can trust")
    d, q = c.raw(), c.data_quality()
    f = c.forecasts()
    from onerecord.forecast import wape
    ab = f["backtest"][f["backtest"]["product"] != "C"]
    k = st.columns(4)
    k[0].metric("Request → SAP today", f"{d['requests'].cycle_days.median():.1f} days", help="Median, email process")
    k[1].metric("Customer records that are duplicates", f"{(q['clusters'].record_id != q['clusters'].golden_id).mean():.0%}")
    k[2].metric("Forecast error vs 6-month average", f"{wape(ab, 'calendar_model') / wape(ab, 'baseline_ma6') - 1:+.0%}")
    k[3].metric("False drop-off alarms removed", len(c.regional()["compare"]["raw_drop"]) - len(c.regional()["compare"]["clean_drop"]))

    left, right = st.columns(2)
    with left:
        st.markdown("##### What this prototype shows")
        st.markdown(
            "**Workflow mock-up** — what the Power Apps form and Power Automate flows do:\n"
            "1. *New request* — the form asks only for the fields that apply and blocks duplicates\n"
            "2. *Approvals* — every check runs **in parallel** as a Teams card, with reminders and escalation\n"
            "3. *MDM check* — Priya approves once and gets an SAP B1 import file\n"
            "4. *Audit log* and *Rules* — who did what, and rules the MDM team edits without IT\n\n"
            "**Regional business view** — clean data put to work: five-country growth, a forecast that beats "
            "the 6-month average, sales actions, and the business case.")
    with right:
        st.markdown("##### Demo script (Amy's story)")
        st.markdown(
            "1. Persona **Amy** → *New request* → Item → regulated **Yes** (licence field appears) → type "
            "*Dengue NS1 rapid test 25T* (duplicate warning)\n"
            "2. Persona **Wei Jie / QA / BU Head** → *Approvals* → approve in parallel\n"
            "3. Sidebar **+3 days** on a stalled request → reminder & escalation fire\n"
            "4. Persona **Priya** → *MDM check* → approve → download the SAP file\n"
            "5. Persona **Priya** → *Rules* → onboard Marcus's new BU → persona **Marcus** → *New request* "
            "picks it up and routes to its own BU Head, no IT\n"
            "6. *Five-country growth* → *Forecasting* → *Sales actions*")
    st.markdown("##### Prototype ↔ Microsoft 365")
    st.dataframe({
        "This prototype": ["New request form", "Approvals (cards)", "Reminders / escalation", "Rules, roles, log",
                           "SAP import file", "Regional business view", "Email triage AI step",
                           "AI action brief (Phase 2)"],
        "Production build": ["Power Apps canvas app in a Teams tab", "Power Automate approvals in Teams/Outlook",
                             "Scheduled Power Automate flow", "SharePoint lists (standard licence)",
                             "Power Automate 'Create CSV table' → SAP DTW", "Power BI in a Teams tab",
                             "Power Automate AI prompt (AI Builder)",
                             "Monthly Power Automate flow + AI prompt → Teams sales channel"],
    }, hide_index=True, width="stretch")
    st.caption("All data is synthetic (no client data was provided). See data/README.md for what was planted and why.")
