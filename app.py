"""
Lives Group master data and regional dashboard prototype (SMU DSA Data Case Competition 2026).

    streamlit run app.py

The regional business view: a strategic overview with analytic drill-downs, forecasting and MDM ops.
The request workflow itself runs in Microsoft 365 (Power Apps + Power Automate; see README). An earlier Streamlit
mock-up of it is still in views/workflow_pages.py but hidden (SHOW_WORKFLOW_MOCKUP), so the demo shows one form.
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Lives Group", page_icon=str(Path(__file__).parent / "assets" / "icon.svg"), layout="wide")

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
# The mock-up's duplicate check differs from the real form's, so it stays hidden; True brings it back
SHOW_WORKFLOW_MOCKUP = False
workflow_pages = [
    st.Page(wp.new_request, title="New request", url_path="new-request", icon=":material/edit_note:"),
    st.Page(wp.my_requests, title="Request status", url_path="status", icon=":material/pin_drop:"),
    st.Page(wp.approvals, title="Approvals", url_path="approvals", icon=":material/task_alt:"),
    st.Page(wp.mdm_queue, title="MDM check", url_path="mdm", icon=":material/storage:"),
    st.Page(wp.audit_log, title="Audit log", url_path="audit-log", icon=":material/receipt_long:"),
    st.Page(wp.rules, title="Rules", url_path="rules", icon=":material/tune:"),
] if SHOW_WORKFLOW_MOCKUP else []
common.PAGES.update({common.page_id(p): p for group in sections.values() for p in group})  # links and access

ASSETS = Path(__file__).parent / "assets"
st.logo(str(ASSETS / "logo_light.svg"), size="large", icon_image=str(ASSETS / "icon.svg"))
nav = st.navigation([p for group in sections.values() for p in group] + workflow_pages, position="hidden")
if not common.allowed(nav):  # e.g. just switched to Priya while on Forecasting: go to her start page
    st.switch_page(common.PAGES[common.user()["pages"][0]])
common.page_style()
common.sidebar(sections, workflow_pages, nav)
common.clock_events()
nav.run()
