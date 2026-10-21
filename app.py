"""
OneRecord prototype for the Lives Group MDM case (SMU DSA Data Case Competition 2026).

    streamlit run app.py

Two halves:
  - Workflow mock-up: what the Power Apps form + Power Automate flows do (production runs in Microsoft 365)
  - Regional business view: clean five-country growth, forecasting and sales actions
"""
import streamlit as st

st.set_page_config(page_title="OneRecord · Lives Group", page_icon="🗂️", layout="wide")

from views import analytics_pages as ap  # noqa: E402
from views import common  # noqa: E402
from views import home  # noqa: E402
from views import workflow_pages as wp  # noqa: E402

pages = {
    "": [st.Page(home.render, title="Overview", icon="🏠", url_path="overview", default=True)],
    "Workflow mock-up · Power Apps + Power Automate": [
        st.Page(wp.new_request, title="New request (form)", icon="📝", url_path="new-request"),
        st.Page(wp.my_requests, title="Request status", icon="📍", url_path="status"),
        st.Page(wp.approvals, title="Approvals (Teams cards)", icon="✅", url_path="approvals"),
        st.Page(wp.mdm_queue, title="MDM check & SAP file", icon="🗄️", url_path="mdm"),
        st.Page(wp.audit_log, title="Audit log", icon="🧾", url_path="audit-log"),
        st.Page(wp.rules, title="Rules (no IT needed)", icon="⚙️", url_path="rules"),
    ],
    "Regional business view": [
        st.Page(ap.growth, title="Five-country growth", icon="🌏", url_path="growth"),
        st.Page(ap.forecasting, title="Forecasting", icon="📈", url_path="forecast"),
        st.Page(ap.actions, title="Sales actions", icon="🎯", url_path="actions"),
        st.Page(ap.inbound, title="Orders vs enquiries", icon="📥", url_path="inbound"),
        st.Page(ap.quality, title="Data quality", icon="🧹", url_path="data-quality"),
        st.Page(ap.business_case, title="Business case", icon="💰", url_path="business-case"),
    ],
}

nav = st.navigation(pages)
common.sidebar()
common.clock_events()
nav.run()
