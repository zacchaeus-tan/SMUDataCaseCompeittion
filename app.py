"""
OneRecord prototype for the Lives Group MDM case (SMU DSA Data Case Competition 2026).

    streamlit run app.py

Two halves:
  - Regional business view: a strategic overview with analytic drill-downs (the dashboard)
  - Workflow mock-up: what the Power Apps form + Power Automate flows do, folded into the bottom of the sidebar
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="OneRecord", page_icon=str(Path(__file__).parent / "assets" / "icon.svg"), layout="wide")

from views import analytics_pages as ap  # noqa: E402
from views import common  # noqa: E402
from views import home  # noqa: E402
from views import workflow_pages as wp  # noqa: E402

sections = {
    "": [st.Page(home.render, title="Overview", url_path="overview", icon=":material/space_dashboard:",
                 default=True)],
    "Drill-down": [
        st.Page(ap.growth, title="Country deep-dive", url_path="growth", icon=":material/public:"),
        st.Page(ap.forecasting, title="Forecasting", url_path="forecast", icon=":material/show_chart:"),
        st.Page(ap.actions, title="Customers", url_path="actions", icon=":material/groups:"),
        st.Page(ap.quality, title="MDM ops", url_path="data-quality", icon=":material/fact_check:"),
    ],
    "More": [
        st.Page(ap.inbound, title="Orders vs enquiries", url_path="inbound", icon=":material/inbox:"),
        st.Page(ap.business_case, title="Business case", url_path="business-case", icon=":material/payments:"),
    ],
}
workflow_pages = [
    st.Page(wp.new_request, title="New request", url_path="new-request", icon=":material/edit_note:"),
    st.Page(wp.my_requests, title="Request status", url_path="status", icon=":material/pin_drop:"),
    st.Page(wp.approvals, title="Approvals", url_path="approvals", icon=":material/task_alt:"),
    st.Page(wp.mdm_queue, title="MDM check", url_path="mdm", icon=":material/storage:"),
    st.Page(wp.audit_log, title="Audit log", url_path="audit-log", icon=":material/receipt_long:"),
    st.Page(wp.rules, title="Rules", url_path="rules", icon=":material/tune:"),
]
common.PAGES.update({p.url_path: p for group in sections.values() for p in group})  # for "see the evidence" links

ASSETS = Path(__file__).parent / "assets"
st.logo(str(ASSETS / "logo_light.svg"), size="large", icon_image=str(ASSETS / "icon.svg"))
nav = st.navigation([p for group in sections.values() for p in group] + workflow_pages, position="hidden")
common.page_style()
common.sidebar(sections, workflow_pages, nav)
common.clock_events()
nav.run()
