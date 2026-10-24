"""
OneRecord prototype for the Lives Group MDM case (SMU DSA Data Case Competition 2026).

    streamlit run app.py

Two halves:
  - Workflow mock-up: what the Power Apps form + Power Automate flows do (production runs in Microsoft 365)
  - Regional business view: clean five-country growth, forecasting and sales actions
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="OneRecord · Lives Group", page_icon="🗂️", layout="wide")

from views import analytics_pages as ap  # noqa: E402
from views import common  # noqa: E402
from views import home  # noqa: E402
from views import workflow_pages as wp  # noqa: E402

pages = {
    "": [st.Page(home.render, title="Overview", url_path="overview", default=True)],
    "Workflow mock-up": [
        st.Page(wp.new_request, title="New request (form)", url_path="new-request"),
        st.Page(wp.my_requests, title="Request status", url_path="status"),
        st.Page(wp.approvals, title="Approvals (Teams cards)", url_path="approvals"),
        st.Page(wp.mdm_queue, title="MDM check & SAP file", url_path="mdm"),
        st.Page(wp.audit_log, title="Audit log", url_path="audit-log"),
        st.Page(wp.rules, title="Rules (no IT needed)", url_path="rules"),
    ],
    "Regional business view": [
        st.Page(ap.growth, title="Five-country growth", url_path="growth"),
        st.Page(ap.forecasting, title="Forecasting", url_path="forecast"),
        st.Page(ap.actions, title="Sales actions", url_path="actions"),
        st.Page(ap.inbound, title="Orders vs enquiries", url_path="inbound"),
        st.Page(ap.quality, title="Data quality", url_path="data-quality"),
        st.Page(ap.business_case, title="Business case", url_path="business-case"),
    ],
}

ASSETS = Path(__file__).parent / "assets"
st.logo(str(ASSETS / "logo.svg"), size="large", icon_image=str(ASSETS / "icon.svg"))
nav = st.navigation(pages)
common.page_style()
common.sidebar()
common.clock_events()
nav.run()
