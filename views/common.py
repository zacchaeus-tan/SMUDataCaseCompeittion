"""Shared loaders, cached analytics and small UI helpers for the Streamlit app."""
import numbers
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

from onerecord import advisor, classify, dedup, forecast, insights, process, workflow
from onerecord.config import COUNTRIES, DATA, KEY, PRODUCTS

from . import theme

COUNTRY_ORDER = list(COUNTRIES)
PRODUCT_LABEL = {p: f"{p}: {n}" for p, n in PRODUCTS.items()}

# one chart style for the whole app, on top of plotly_white
CHART_TEMPLATE = pio.templates.merge_templates(pio.templates["plotly_white"], go.layout.Template(layout=dict(
    font=dict(family="Poppins, sans-serif", size=12.5, color=theme.TEXT),
    xaxis=dict(showgrid=False, linecolor="#e2e8f0", ticks="outside", tickcolor="#e2e8f0"),
    yaxis=dict(gridcolor="#eef2f6", zeroline=False),
    legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", title_text=""),
    hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font_size=12, font_family="Poppins, sans-serif"),
)))


ASSETS = Path(__file__).resolve().parent.parent / "assets"
PAGES = {}  # url_path -> page, filled in by app.py so pages can link to each other
KPI_HEIGHT = 132  # every KPI card the same height, with or without a change figure


def page_style():
    """Page-wide CSS: sections fade in on load."""
    st.html(f"<style>{(ASSETS / 'app.css').read_text()}</style>")


def chart(fig):
    # backgrounds set on the figure itself: Streamlit replaces template backgrounds with the page colour
    fig.update_layout(template=CHART_TEMPLATE, paper_bgcolor=theme.CARD, plot_bgcolor=theme.CARD)
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False})


def select(where, *args, **kwargs):
    """A dropdown you pick from but can't type into (every dropdown in the app goes through here)."""
    return where.selectbox(*args, filter_mode=None, **kwargs)


def table_height(rows):
    """Pixel height that shows every row of a st.dataframe without scrolling."""
    return 35 * (rows + 1) + 3


def header(section, headline):
    """Page header bar: the section name small, the finding as the headline, the data period on the right."""
    st.html(f'<div class="or-topbar"><div><div class="or-section">{escape(section)}</div>'
            f'<h1>{escape(headline)}</h1></div>'
            f'<div class="or-who"><span class="or-period">Apr 2025 – Sep 2026 · synthetic data</span>'
            f'<span class="or-avatar" title="Lives Group">LG</span></div></div>')


def tone(change, up_is_good=True):
    """Colour for a change: good, bad, or neutral when there is no change."""
    if not change:
        return "neutral"
    return "good" if (change > 0) == up_is_good else "bad"


def kpi(label, value, *, prefix="", suffix="", decimals=0, delta=None, tone="neutral", help=None, key=None):
    """One KPI card for kpi_row. A numeric value counts up; text is shown as is.
    `key` names the card for the ticker, so it counts from its last value even when the label changes."""
    info = f'<span class="info" title="{escape(help)}">i</span>' if help else ""
    if isinstance(value, numbers.Real) and not isinstance(value, bool):  # numpy numbers count too
        shown = f"{prefix}{value:,.{decimals}f}{suffix}"
        number = (f' data-to="{float(value)}" data-decimals="{decimals}" data-prefix="{escape(prefix)}" '
                  f'data-suffix="{escape(suffix)}" data-key="{escape(key or label)}"')
    else:
        shown, number = str(value), ""
    if delta:
        arrow = "↑ " if delta.startswith("+") else "↓ " if delta.startswith(("-", "−")) else ""
        delta = arrow + delta
    return (f'<div class="card {tone}"><div class="label">{escape(label)}{info}</div>'
            f'<div class="value"{number}>{escape(shown)}</div><div class="delta">{escape(delta or "")}</div></div>')


def kpi_row(cards, height=KPI_HEIGHT):
    """A row of equal-sized KPI cards."""
    template = (ASSETS / "kpi_row.html").read_text()  # read each time, so edits show on refresh
    html = (template.replace("__COLUMNS__", str(len(cards))).replace("__CARD_HEIGHT__", str(height))
            .replace("__CARDS__", "".join(cards)))
    components.html(html, height=height + 12)


@st.cache_data(show_spinner=False)
def raw():
    return dict(
        customers=pd.read_csv(DATA / "customer_master.csv", dtype=str).fillna(""),
        items=pd.read_csv(DATA / "item_master.csv"),
        vendors=pd.read_csv(DATA / "vendor_master.csv", dtype=str),
        po=pd.read_csv(DATA / "purchase_orders.csv"),
        requests=pd.read_csv(DATA / "mdm_requests_history.csv").fillna(""),
        steps=pd.read_csv(DATA / "mdm_request_steps.csv"),
        inbound=pd.read_csv(DATA / "inbound_messages.csv", dtype=str).fillna(""),
        holdout=pd.read_csv(DATA / "inbound_messages_holdout.csv", dtype=str).fillna(""),
    )


@st.cache_data(show_spinner="Matching duplicate records…")
def data_quality():
    d = raw()
    pairs, clusters = dedup.find_duplicates(d["customers"])
    item_map = insights.item_duplicates(d["items"])
    truth = pd.read_csv(KEY / "customer_record_truth.csv", dtype=str)
    return dict(pairs=pairs, clusters=clusters, item_map=item_map, score=dedup.evaluate(clusters, truth))


@st.cache_data(show_spinner="Building the regional view…")
def regional():
    d, q = raw(), data_quality()
    clean = insights.clean_orders(d["po"], q["clusters"], q["item_map"])
    return dict(clean=clean, growth=insights.growth_table(clean), monthly=insights.monthly(clean),
                compare=insights.raw_vs_clean(clean, d["customers"]))


@st.cache_data(show_spinner="Back-testing forecasts…")
def forecasts():
    Y = forecast.series(regional()["clean"])
    bt = forecast.backtest(Y)
    acc = forecast.accuracy_table(bt)
    ahead, effects = forecast.forecast_ahead(Y)
    ahead = forecast.with_range(ahead, forecast.error_bands(bt))
    return dict(Y=Y, backtest=bt, accuracy=acc, ahead=ahead, effects=effects,
                plan=forecast.stock_plan(Y, ahead, acc))


@st.cache_data(show_spinner="The AI is reading the regional numbers…")
def ai_brief(facts_json: str, focus: str):
    """Cached on the exact facts + focus, so reruns of the page don't call the API again."""
    import json
    return advisor.recommend(json.loads(facts_json), focus)


@st.cache_data(show_spinner="Sorting inbound emails…")
def triage():
    d = raw()
    main = classify.classify_all(d["inbound"]).merge(pd.read_csv(KEY / "inbound_message_labels.csv", dtype=str),
                                                     on="message_id")
    hold = classify.classify_all(d["holdout"]).merge(pd.read_csv(KEY / "inbound_holdout_labels.csv", dtype=str),
                                                     on="message_id")
    return dict(main=main, holdout=hold)


@st.cache_data(show_spinner=False)
def process_baseline():
    d = raw()
    return process.breakdown(d["steps"])


# --------------------------------------------------------------------------- workflow state
@st.cache_resource
def con():
    return workflow.ensure()


def reset_workflow():
    con().close()
    con.clear()
    workflow.reset().close()


def persona() -> str:
    return st.session_state.get("persona", list(workflow.PERSONAS)[0])


def role() -> str:
    return workflow.PERSONAS[persona()]


def sidebar(sections, workflow_pages, current):
    """Dashboard pages as lists with the current one highlighted; the workflow mock-up (with its persona picker
    and demo clock) folded into one section at the bottom."""
    with st.sidebar:
        for label, section_pages in sections.items():
            if label:
                st.html(f'<div class="or-navlabel">{escape(label)}</div>')
            for p in section_pages:
                _nav_link(p, current)
        st.html('<div style="height:20px"></div>')
        in_workflow = current.url_path in {p.url_path for p in workflow_pages}
        with st.expander("☰  Workflow mock-up", expanded=in_workflow):
            for p in workflow_pages:
                _nav_link(p, current)
            st.divider()
            _workflow_controls()


def _nav_link(page, current):
    on = "navon" if page.url_path == current.url_path else "navoff"
    with st.container(key=f"{on}-{page.url_path}"):
        st.page_link(page)


def _workflow_controls():
    """Persona picker and demo clock: they only matter for the workflow mock-up."""
    st.markdown("**Viewing as**")
    select(st, "Persona", list(workflow.PERSONAS), key="persona", label_visibility="collapsed",
                 help="Switch persona to see the request from each person's side. Sensitive fields are only "
                      "visible to Finance and MDM.")
    st.caption(f"Role: **{role()}**")
    st.divider()
    st.markdown("**Demo clock**")
    c = con()
    st.caption(f"Simulated time: {workflow.now(c):%a %d %b %Y, %H:%M}")
    col1, col2 = st.columns(2)
    if col1.button("+1 day", width="stretch"):
        _advance(1)
    if col2.button("+3 days", width="stretch"):
        _advance(3)
    if st.button("Reset demo data", width="stretch", type="secondary"):
        reset_workflow()
        st.toast("Workflow demo reset")
        st.rerun()
    st.caption("The clock lets you fast-forward to show reminders and escalation firing.")


def _advance(days):
    events = workflow.advance_clock(con(), days)
    st.session_state["clock_events"] = events or ["No reminders due."]
    st.rerun()


def clock_events():
    ev = st.session_state.pop("clock_events", None)
    if ev:
        for e in ev:
            st.toast(e)


def pct(x, signed=True):
    return f"{x:+.0%}" if signed else f"{x:.0%}"


def assumption(text):
    st.caption(f"**Assumption:** {text}")
