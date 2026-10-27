"""
OneRecord prototype for the Lives Group MDM case (SMU DSA Data Case Competition 2026).

    streamlit run app.py

One app for both parts: the regional business view (a strategic overview with analytic drill-downs, forecasting
and MDM ops) and the request workflow. The workflow is the live Power App running in Microsoft 365, embedded in the
"Requests" pages (views/m365_pages.py), so a request raised here runs the real Power Automate flows.
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="OneRecord", page_icon=str(Path(__file__).parent / "assets" / "icon.svg"), layout="wide")

from views import analytics_pages as ap  # noqa: E402
from views import common  # noqa: E402
from views import home  # noqa: E402
from views import m365_pages as mp  # noqa: E402

sections = {
    "": [st.Page(home.render, title="Overview", url_path="overview", icon=":material/space_dashboard:",
                 default=True)],
    # grouped by what each page is for: what's happening, what to do about it, and why trust or fund it
    "Insights": [
        st.Page(ap.growth, title="Country deep-dive", url_path="growth", icon=":material/public:"),
        st.Page(ap.forecasting, title="Forecasting", url_path="forecast", icon=":material/show_chart:"),
    ],
    "Actions": [
        st.Page(ap.actions, title="Customers", url_path="actions", icon=":material/groups:"),
        st.Page(ap.quality, title="MDM ops", url_path="data-quality", icon=":material/fact_check:"),
    ],
    # the live Power App: getting clean records in
    "Requests": [
        st.Page(mp.new_request, title="New request", url_path="new-request", icon=":material/edit_note:"),
        st.Page(mp.my_requests, title="My requests", url_path="my-requests", icon=":material/pin_drop:"),
        st.Page(mp.rules, title="Rules", url_path="rules", icon=":material/tune:"),
    ],
    "Context": [
        st.Page(ap.inbound, title="Orders vs enquiries", url_path="inbound", icon=":material/inbox:"),
        st.Page(ap.business_case, title="Business case", url_path="business-case", icon=":material/payments:"),
    ],
}
common.PAGES.update({common.page_id(p): p for group in sections.values() for p in group})  # links and access

ASSETS = Path(__file__).parent / "assets"
st.logo(str(ASSETS / "logo_light.svg"), size="large", icon_image=str(ASSETS / "icon.svg"))
nav = st.navigation([p for group in sections.values() for p in group], position="hidden")
if not common.allowed(nav):  # e.g. just switched to Priya while on Forecasting: go to her start page
    st.switch_page(common.PAGES[common.user()["pages"][0]])
common.page_style()
common.sidebar(sections, nav)
nav.run()
