"""Shared loaders, cached analytics and small UI helpers for the Streamlit app."""
import pandas as pd
import streamlit as st

from onerecord import advisor, classify, dedup, forecast, insights, process, workflow
from onerecord.config import COUNTRIES, DATA, KEY, PRODUCTS

COUNTRY_ORDER = list(COUNTRIES)
PRODUCT_LABEL = {p: f"{p}: {n}" for p, n in PRODUCTS.items()}


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


@st.cache_data(show_spinner="Claude is reading the regional numbers…")
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


def sidebar():
    with st.sidebar:
        st.markdown("### Viewing as")
        st.selectbox("Persona", list(workflow.PERSONAS), key="persona", label_visibility="collapsed",
                     help="Switch persona to see the request from each person's side. Sensitive fields are only "
                          "visible to Finance and MDM.")
        st.caption(f"Role: **{role()}**")
        st.divider()
        st.markdown("### Demo clock")
        c = con()
        st.caption(f"Simulated time: **{workflow.now(c):%a %d %b %Y, %H:%M}**")
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
            st.toast(e, icon="⏰")


def pct(x, signed=True):
    return f"{x:+.0%}" if signed else f"{x:.0%}"


def assumption(text):
    st.caption(f"🔖 **Assumption:** {text}")
