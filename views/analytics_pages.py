"""Regional business view: growth, forecasting, sales actions, inbound triage, data quality, business case."""
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from onerecord import advisor, classify, process
from onerecord.config import COUNTRIES, CURRENT, PRIOR_YEAR, PRODUCTS

from . import common as c

COLORS = {"A": "#2a6fdb", "B": "#e07b39", "C": "#5b9a68"}
ALL = "ALL"  # "All countries" option in the forecast picker
# one fixed colour per country on every chart (Okabe-Ito, readable with colour blindness)
COUNTRY_COLORS = {"SG": "#0072B2", "MY": "#E69F00", "TH": "#009E73", "ID": "#CC79A7", "VN": "#56B4E9"}
LABEL_COLORS = ["#1f4e79", "#7fa7d0", "#c9a227", "#8c6bb1"]
SCENARIO_COLORS = {"Today (email)": "#9aa3ad", "OneRecord": "#1f4e79"}
# orange = decline, blue = growth; replaces red-green, which colour-blind readers can't separate
DIVERGING = [[0, "#c4571b"], [0.5, "#f4f1ec"], [1, "#2166ac"]]

COUNTRY_COL = st.column_config.TextColumn("Country")
PRODUCT_COL = st.column_config.TextColumn("Product")


def _definition():
    with st.expander("How growth is measured"):
        st.markdown(f"Growth is the year-on-year change in units ordered, {CURRENT[0]} to {CURRENT[1]} against "
                    f"{PRIOR_YEAR[0]} to {PRIOR_YEAR[1]}. Comparing the same six months removes seasonal effects. "
                    f"Momentum compares the last 3 months with the same 3 months a year earlier. Only customer orders "
                    f"are counted; enquiries, follow-ups and master-data requests are left out.")


# --------------------------------------------------------------------------- growth
def growth():
    g = c.regional()["growth"]
    g["country_name"] = g.country.map(COUNTRIES)
    ab = g[g["product"] != "C"]
    by_country = ab.groupby("country")[["units_now", "units_prev"]].sum()
    lead = (by_country.units_now / by_country.units_prev - 1).nlargest(2).index.map(COUNTRIES)
    worst = ab.loc[ab.unit_growth.idxmin()]
    headline = f"{lead[0]} and {lead[1]} lead growth"
    if worst.unit_growth < 0:
        headline += f", while {COUNTRIES[worst.country]} product {worst['product']} is down {-worst.unit_growth:.0%}"
    c.header("Five-country growth", headline)

    tot_now, tot_prev = g.units_now.sum(), g.units_prev.sum()
    val_now, val_prev = g.value_now.sum(), g.value_prev.sum()
    best = g.loc[g[g["product"] != "C"].unit_growth.idxmax()]
    units_chg, value_chg = tot_now / tot_prev - 1, val_now / val_prev - 1
    c.kpi_row([
        c.kpi("Units, Apr–Sep 2026", tot_now, delta=c.pct(units_chg), tone=c.tone(units_chg)),
        c.kpi("Order value (SGD)", val_now / 1e6, decimals=2, suffix="M", delta=c.pct(value_chg),
              tone=c.tone(value_chg)),
        c.kpi("Active customers", c.regional()["clean"].query("month >= @CURRENT[0]").customer_id.nunique(),
              help="Real customers after merging duplicate records"),
        c.kpi("Fastest growing (A/B)", f"{best.country}, product {best['product']}", delta=c.pct(best.unit_growth),
              tone=c.tone(best.unit_growth)),
    ])
    _definition()

    _growth_map(g)

    t = g[["country", "product", "units_now", "unit_growth", "momentum_3m", "value_now", "customers_now"]].copy()
    t[["unit_growth", "momentum_3m"]] *= 100
    row_h = c.table_height(len(t))  # heatmap matches the table, so both boxes end on the same line
    left, right = st.columns(2)
    with left:
        st.markdown("##### Year-on-year unit growth")
        m = g.pivot(index="country", columns="product", values="unit_growth").reindex(c.COUNTRY_ORDER)
        fig = px.imshow(m, text_auto="+.0%", color_continuous_scale=DIVERGING, zmin=-0.3, zmax=0.3, aspect="auto",
                        labels=dict(color="YoY", x="Product", y=""))
        fig.update_layout(height=row_h, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        c.chart(fig)
    with right:
        st.markdown("##### By country and product")
        st.dataframe(t, hide_index=True, width="stretch", height=row_h, column_config={
            "country": COUNTRY_COL,
            "product": PRODUCT_COL,
            "units_now": st.column_config.NumberColumn("Units", format="localized"),
            "unit_growth": st.column_config.NumberColumn("YoY", format="%+.0f%%"),
            "momentum_3m": st.column_config.NumberColumn("Momentum", format="%+.0f%%",
                                                         help="Last 3 months vs the same 3 months a year earlier"),
            "value_now": st.column_config.NumberColumn("Value (SGD)", format="localized"),
            "customers_now": st.column_config.NumberColumn("Customers"),
        })
    st.caption("Product C (equipment) sells only 30–50 units per country each half-year, so its growth figures swing "
               "a lot. Treat them as a rough guide.")

    st.markdown("##### Monthly units")
    prod = st.radio("Product", list(PRODUCTS), horizontal=True, format_func=lambda p: c.PRODUCT_LABEL[p])
    mm = c.regional()["monthly"].query("product == @prod")
    fig = px.line(mm, x="month", y="quantity", color="country", markers=True,
                  category_orders={"country": c.COUNTRY_ORDER}, color_discrete_map=COUNTRY_COLORS)
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="units", xaxis_title="",
                      legend_title="")
    c.chart(fig)

    st.markdown("##### Takeaways")
    vn_b = g[(g.country == "VN") & (g["product"] == "B")].iloc[0]
    drops = c.regional()["compare"]["clean_drop"]
    vn_drop_val = drops[drops.country == "VN"].value_at_risk_per_q.sum()
    st.markdown(
        f"- Malaysia and Indonesia are growing fastest, with Products A and B up about 20–30% on last year. Both "
        f"need enough stock and sales cover before the December budget flush, and Indonesia's dengue season runs "
        f"from January to April.\n"
        f"- Vietnam Product B is down {abs(vn_b.unit_growth):.0%} while the market is still growing. Most of the "
        f"drop comes from a few large labs ordering much less, worth about S${vn_drop_val:,.0f} a quarter. These "
        f"accounts need follow-up from sales (see Sales actions).\n"
        f"- Singapore is a mature market: growth is in single digits and equipment sales are falling. Most new "
        f"growth there will come from selling more products to existing customers.")


ISO3 = {"SG": "SGP", "MY": "MYS", "TH": "THA", "ID": "IDN", "VN": "VNM"}
CAPITAL = {"SG": (1.35, 103.82), "MY": (3.14, 101.69), "TH": (13.76, 100.50), "ID": (-6.21, 106.85),
           "VN": (21.03, 105.85)}
LABEL_POS = {"SG": "middle right", "MY": "middle left", "TH": "middle left", "ID": "bottom center",
             "VN": "middle right"}  # KL and Singapore sit close together: push their labels apart


def _growth_map(g):
    st.markdown("##### Year-on-year growth by country")
    pick = st.radio("Show", ["All products", *PRODUCTS], horizontal=True, key="map_product",
                    format_func=lambda p: p if p == "All products" else c.PRODUCT_LABEL[p])
    d = g if pick == "All products" else g[g["product"] == pick]
    m = d.groupby("country")[["units_now", "units_prev", "value_now"]].sum().reindex(c.COUNTRY_ORDER).reset_index()
    m["growth"] = m.units_now / m.units_prev - 1
    m["iso"], m["name"] = m.country.map(ISO3), m.country.map(COUNTRIES)
    m["lat"], m["lon"] = zip(*m.country.map(CAPITAL))
    m["label"] = m.country + " " + m.growth.map(lambda x: f"{x:+.0%}")
    hover = "<b>%{customdata[0]}</b><br>Units Apr–Sep 2026: %{customdata[1]:,.0f}<br>YoY: %{customdata[2]:+.1%}" \
            "<br>Value: S$%{customdata[3]:,.0f}<extra></extra>"
    custom = m[["name", "units_now", "growth", "value_now"]].values
    fig = go.Figure()
    fig.add_choropleth(locations=m.iso, z=m.growth, colorscale=DIVERGING, zmin=-0.3, zmax=0.3, customdata=custom,
                       hovertemplate=hover, marker_line_color="white", colorbar=dict(title="YoY", tickformat="+.0%"))
    # bubbles sized by volume; they also keep Singapore visible, which is too small to see as a filled shape
    fig.add_scattergeo(lat=m.lat, lon=m.lon, text=m.label, mode="markers+text",
                       textposition=list(m.country.map(LABEL_POS)),
                       marker=dict(size=10 + 30 * m.units_now / m.units_now.max(), color="rgba(40,40,40,0.35)",
                                   line=dict(color="white", width=1)),
                       textfont=dict(size=13, color="#222"), customdata=custom, hovertemplate=hover,
                       showlegend=False)
    fig.update_geos(projection_type="mercator", lataxis_range=[-11, 24], lonaxis_range=[92, 128],
                    showcountries=True, countrycolor="#bbb", showland=True, landcolor="#f2f2f2",
                    showocean=True, oceancolor="#e8f0f8", showframe=False)
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0))
    c.chart(fig)
    st.caption("Colour shows year-on-year growth in units. Bubble size shows units ordered in Apr–Sep 2026.")


# --------------------------------------------------------------------------- forecasting
def forecasting():
    f = c.forecasts()
    bt, acc = f["backtest"], f["accuracy"]
    from onerecord.forecast import wape
    ab = bt[bt["product"] != "C"]
    cut = 1 - wape(ab, "calendar_model") / wape(ab, "baseline_ma6")
    c.header("Forecasting", f"The calendar model cuts forecast error by {cut:.0%} compared with the 6-month average")
    c.kpi_row([
        c.kpi("Today: 6-month average", wape(ab, "baseline_ma6") * 100, decimals=1, suffix="% error"),
        c.kpi("OneRecord calendar model", wape(ab, "calendar_model") * 100, decimals=1, suffix="% error",
              delta=f"{-cut:+.0%}", tone=c.tone(-cut, up_is_good=False)),
        c.kpi("Series improved", (acc[acc["product"] != "C"].Improvement > 0).sum(), suffix=" of 10",
              help="Products A and B"),
        c.kpi("Horizon tested", "1–3 months", help="Rolling origins Apr–Sep 2026; error = WAPE"),
    ])
    st.caption("Error is measured as WAPE: total absolute error divided by actual units. It covers Products A and "
               "B, forecasting 1–3 months ahead from each month Apr–Sep 2026, using only the data available at "
               "the time.")

    with st.expander("How the model works", expanded=False):
        st.markdown(
            "The 6-month average gives every month the same weight, so it reacts late to dengue season and the "
            "December budget flush. The calendar model starts from each series' level and trend, then adjusts for "
            "events Lives Group already plans around: dengue season in each country (Product A), the hospital "
            "year-end push, the January slowdown, and public holidays such as Lunar New Year, Tet, Songkran and "
            "Hari Raya. It estimates the size of each effect from all five countries together, which is why 12–18 "
            "months of history is enough. It is re-run each month alongside an error report.")
        eff = pd.DataFrame({"Calendar effect": list(f["effects"]), "Learned impact on units": list(f["effects"].values())})
        st.dataframe(eff, hide_index=True, column_config={
            "Learned impact on units": st.column_config.NumberColumn(format="percent")})

    s1, s2, s3 = st.columns([2, 2, 1.3], vertical_alignment="bottom")
    country = s1.selectbox("Country", [ALL, *c.COUNTRY_ORDER], index=1 + c.COUNTRY_ORDER.index("TH"),
                           format_func=lambda k: "All countries" if k == ALL else COUNTRIES[k])
    prod = s2.selectbox("Product", list(PRODUCTS), format_func=lambda p: c.PRODUCT_LABEL[p])
    show_ma6 = s3.toggle("Show 6-month average", disabled=country == ALL,
                         help="Pick a single country to compare with the 6-month average")
    if country == ALL:
        _forecast_all(f, prod)
    else:
        _forecast_one(f, country, prod, show_ma6)

    st.markdown("##### Accuracy by series")
    st.dataframe(acc, hide_index=True, width="stretch", column_config={
        "country": COUNTRY_COL,
        "product": PRODUCT_COL,
        "MA6 error": st.column_config.NumberColumn("6-month average error", format="percent"),
        "Model error": st.column_config.NumberColumn(format="percent"),
        "Improvement": st.column_config.NumberColumn(format="percent")})
    st.markdown(
        "The largest gains are for Product A in Indonesia, Malaysia and Thailand, where the 6-month average misses "
        "dengue season. Singapore A gets slightly worse because its dengue effect is milder than the regional "
        "estimate; a Singapore-specific effect can be added once there is more history. Vietnam B is poor under "
        "both methods because the drop comes from lost accounts, which the drop-off alerts on Sales actions cover. "
        "Product C orders are too irregular to forecast monthly and are better planned from the sales pipeline.")

    st.markdown("##### Stock plan for next quarter")
    plan = f["plan"]
    st.caption("Forecast for Oct–Dec 2026 compared with the last three months. The low–high range is based on how "
               "far actual orders landed from the model in the back-test; 8 in 10 months fell inside it. Series "
               "the model forecast poorly are flagged instead of given an action.")
    st.dataframe(plan, hide_index=True, width="stretch", column_config={
        "country": COUNTRY_COL,
        "product": PRODUCT_COL,
        "last_3_months": st.column_config.NumberColumn("Last 3 months", format="%d"),
        "next_3_months": st.column_config.NumberColumn("Forecast", format="%d"),
        "low": st.column_config.NumberColumn("Low", format="%d"),
        "high": st.column_config.NumberColumn("High", format="%d"),
        "change": st.column_config.NumberColumn("Change", format="percent"),
        "backtest_error": st.column_config.NumberColumn("Back-test error", format="percent"),
        "drivers": st.column_config.TextColumn("Calendar drivers"),
        "action": st.column_config.TextColumn("Recommended action", width="large")})
    _ai_brief(plan)


def _forecast_one(f, country, prod, show_ma6):
    """One country: actual orders, the back-test, and the next 3 months with a likely range."""
    bt, acc = f["backtest"], f["accuracy"]
    hist = f["Y"].loc[(country, prod)]
    one = bt[(bt.country == country) & (bt["product"] == prod) & (bt.horizon == 1)]
    ahead = f["ahead"][(f["ahead"].country == country) & (f["ahead"]["product"] == prod)]
    fig = go.Figure()
    fig.add_scatter(x=hist.index, y=hist.values, name="Actual orders", mode="lines+markers", line=dict(color="#333"))
    if show_ma6:
        fig.add_scatter(x=one.month, y=one.baseline_ma6, name="6-month average (back-test)", mode="lines+markers",
                        line=dict(color="#aaa", dash="dot"))
    fig.add_scatter(x=one.month, y=one.calendar_model, name="Calendar model (back-test)", mode="lines+markers",
                    line=dict(color=COLORS[prod]))
    fig.add_scatter(x=ahead.month, y=ahead.high, mode="lines", line=dict(width=0), showlegend=False,
                    hoverinfo="skip")
    fig.add_scatter(x=ahead.month, y=ahead.low, name="Likely range (8 in 10 months)", mode="lines",
                    line=dict(width=0), fill="tonexty", fillcolor="rgba(120,120,120,0.18)")
    if show_ma6:
        fig.add_scatter(x=ahead.month, y=ahead.baseline_ma6, name="6-month average, next 3 months", mode="lines",
                        line=dict(color="#aaa", dash="dash"))
    fig.add_scatter(x=ahead.month, y=ahead.calendar_model, name="Calendar model, next 3 months", mode="lines+markers",
                    line=dict(color=COLORS[prod], dash="dash"))
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="units",
                      legend=dict(orientation="h", y=-0.2))
    c.chart(fig)
    row = acc[(acc.country == country) & (acc["product"] == prod)].iloc[0]
    st.caption(f"{COUNTRIES[country]}, product {prod}: the 6-month average's error is {row['MA6 error']:.1%}, "
               f"the model's is {row['Model error']:.1%}.")


def _forecast_all(f, prod):
    """Every country on one chart: actual orders solid, the next 3 months' forecast dashed in the same colour."""
    from onerecord.forecast import wape
    fig = go.Figure()
    for k in c.COUNTRY_ORDER:
        hist = f["Y"].loc[(k, prod)]
        ahead = f["ahead"][(f["ahead"].country == k) & (f["ahead"]["product"] == prod)]
        fig.add_scatter(x=hist.index, y=hist.values, name=COUNTRIES[k], mode="lines+markers", legendgroup=k,
                        line=dict(color=COUNTRY_COLORS[k]))
        # start the dashed forecast at the last actual month so the two lines join up
        fig.add_scatter(x=[hist.index[-1], *ahead.month], y=[hist.values[-1], *ahead.calendar_model],
                        name=f"{COUNTRIES[k]} forecast", mode="lines", legendgroup=k, showlegend=False,
                        line=dict(color=COUNTRY_COLORS[k], dash="dash"))
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="units")
    c.chart(fig)
    bt = f["backtest"][f["backtest"]["product"] == prod]
    st.caption(f"Solid lines are actual orders; dashed lines are the calendar model's forecast for the next 3 months. "
               f"Across all five countries, product {prod}: the 6-month average's error is "
               f"{wape(bt, 'baseline_ma6'):.1%}, the model's is {wape(bt, 'calendar_model'):.1%}. Pick a single "
               f"country to see the likely range and the back-test.")


def _ai_brief(plan):
    st.markdown("##### AI action brief (Phase 2)")
    st.caption("Planned for Phase 2. Each month, a Power Automate flow would send the figures on these pages to an "
               "AI Builder prompt and post the five most useful actions to the sales channel in Teams. This is a "
               "preview of that prompt.")
    reg = c.regional()
    data = advisor.facts(reg["growth"], plan, reg["compare"]["clean_drop"], reg["compare"]["clean_xsell"])
    focus = st.text_input("Focus (optional)", placeholder="e.g. Vietnam, or year-end budget flush",
                          key="ai_focus")
    if not classify.ai_available():
        st.info("The preview needs an ANTHROPIC_API_KEY on this machine. The stock plan above works without it.")
    elif st.button("Preview the AI action brief", type="primary"):
        st.session_state["ai_brief"] = c.ai_brief(json.dumps(data), focus)
    res = st.session_state.get("ai_brief")
    if res:
        brief, err = res
        if err:
            c.ai_brief.clear()  # don't keep a failed call cached; the button retries
            st.warning(f"{err}. Showing the rule-based plan only.")
        else:
            st.success(f"**{brief['headline']}**")
            for i, a in enumerate(brief["actions"], 1):
                with st.container(border=True):
                    st.markdown(f"**{i}. {a['title']}**  \n"
                                f"{COUNTRIES.get(a['country'], a['country'])}, product {a['product']}. "
                                f"Owner: {a['owner']}. Confidence: {a['confidence']}.")
                    st.markdown(f"**First step:** {a['first_step']}  \n**Evidence:** {a['evidence']}  \n"
                                f"**Expected impact:** {a['expected_impact']}")
            c.assumption("AI suggestions are input for the monthly sales meeting, and every figure they cite can "
                         "be checked in the data below. The preview uses Claude; production would run the same "
                         "prompt in Power Automate.")
    with st.expander("Data sent to the AI (summary figures only, no customer master data or raw orders)"):
        st.json(data, expanded=False)


# --------------------------------------------------------------------------- actions
def _flag_false(raw, clean, golden):
    """Label each alert raised on raw SAP records: real, the same customer counted again, or a false alarm."""
    cust = raw.id.map(golden).fillna(raw.id)
    status = pd.Series("False alarm", index=raw.index)
    status[cust.isin(clean.id)] = "Real"
    status[cust.isin(clean.id) & cust.duplicated()] = "Counted twice"
    return raw.assign(status=status).sort_values("status", key=lambda s: s.eq("Real"), kind="stable")


STATUS_COL = st.column_config.TextColumn("Check", help="False alarm or counted twice: caused by duplicate records, "
                                                       "and gone once duplicates are merged")


def actions():
    cmp = c.regional()["compare"]
    c.header("Sales actions", f"{len(cmp['clean_drop'])} customers are ordering much less, with about "
                              f"S${cmp['clean_drop'].value_at_risk_per_q.sum():,.0f} a quarter at risk")
    raw = st.toggle("Show raw SAP records (before duplicates are merged)",
                    help="Runs the same analysis on the customer records as they sit in SAP today")
    if raw:
        golden = c.data_quality()["clusters"].set_index("record_id").golden_id
        drop = _flag_false(cmp["raw_drop"], cmp["clean_drop"], golden)
        xsell = _flag_false(cmp["raw_xsell"], cmp["clean_xsell"], golden)
        false_drop, false_xsell = (drop.status != "Real").sum(), (xsell.status != "Real").sum()
    else:
        drop, xsell = cmp["clean_drop"], cmp["clean_xsell"]

    at_risk = c.kpi("Value at risk per quarter", drop.value_at_risk_per_q.sum(), prefix="S$")
    if raw:
        c.kpi_row([
            c.kpi("Customer records in SAP", cmp["raw_customers"]),
            c.kpi("Drop-off alerts", len(drop), delta=f"{false_drop} not real", tone="bad"),
            c.kpi("Cross-sell leads", len(xsell), delta=f"{false_xsell} not real", tone="bad"),
            at_risk])
    else:
        c.kpi_row([
            c.kpi("Real customers", cmp["clean_customers"],
                  delta=f"{cmp['clean_customers'] - cmp['raw_customers']} duplicates merged"),
            c.kpi("Drop-off alerts", len(drop), delta=f"{len(drop) - len(cmp['raw_drop'])} vs raw records",
                  tone="good", help="With duplicate records, a customer whose orders moved to a new record looks "
                                    "like they stopped ordering."),
            c.kpi("Cross-sell leads", len(xsell), delta=f"{len(xsell) - len(cmp['raw_xsell'])} vs raw records",
                  tone="good", help="With duplicate records, one hospital can be split into an A-only and a B-only "
                                    "record, which looks like a cross-sell gap."),
            at_risk])
    if raw:
        st.warning(f"On raw records, {false_drop} of {len(drop)} drop-off alerts and {false_xsell} of {len(xsell)} "
                   f"cross-sell leads are false or counted twice, because the same customer has more than one record. "
                   f"Turn the switch off to see the cleaned view.")

    status = ["status"] if raw else []
    t1, t2 = st.tabs(["Customers dropping off", "Cross-sell opportunities"])
    with t1:
        d = drop
        st.markdown(f"{len(d)} established customers ordered at least 40% less last quarter than in the same "
                    f"quarter last year, and than their own recent average. Value at risk is about "
                    f"S${d.value_at_risk_per_q.sum():,.0f} per quarter.")
        st.dataframe(d[status + ["name", "country", "units_last_q", "units_same_q_last_year", "change",
                                 "value_at_risk_per_q", "last_order"]], hide_index=True, width="stretch",
                     column_config={
            "status": STATUS_COL,
            "name": st.column_config.TextColumn("Customer"),
            "country": COUNTRY_COL,
            "units_last_q": st.column_config.NumberColumn("Units last quarter"),
            "units_same_q_last_year": st.column_config.NumberColumn("Same quarter last year"),
            "change": st.column_config.NumberColumn("YoY", format="percent"),
            "value_at_risk_per_q": st.column_config.NumberColumn("At risk per quarter (SGD)", format="%.0f"),
            "last_order": st.column_config.TextColumn("Last order")})
        st.markdown("**Suggested next step:** account managers call the top 10 by value within two weeks and record "
                    "the reason (competitor, budget, service issue), so patterns by country become visible.")
    with t2:
        x = xsell
        st.markdown(f"{len(x)} customers buy only one of Products A and B, while most similar customers buy both. "
                    f"If all of them bought both, that would be worth about "
                    f"S${x.est_value_sgd_per_year.sum() / 1e6:,.1f}M a year.")
        st.dataframe(x[status + ["name", "country", "segment", "buys", "missing", "peers_buying_both",
                                 "est_units_per_year", "est_value_sgd_per_year"]], hide_index=True, width="stretch",
                     column_config={
            "status": STATUS_COL,
            "name": st.column_config.TextColumn("Customer"),
            "country": COUNTRY_COL,
            "segment": st.column_config.TextColumn("Segment"),
            "buys": st.column_config.TextColumn("Buys"),
            "missing": st.column_config.TextColumn("Not buying"),
            "peers_buying_both": st.column_config.NumberColumn("Similar customers buying both"),
            "est_units_per_year": st.column_config.NumberColumn("Est. units per year", format="%.0f"),
            "est_value_sgd_per_year": st.column_config.NumberColumn("Potential per year (SGD)", format="%.0f")})
        c.assumption("potential is the customer's volume of the product they already buy, multiplied by the median "
                     "ratio among similar customers who buy both. This is an upper limit; the business case "
                     "assumes 10% conversion.")
        st.markdown("**Suggested next step:** offer a reagents-and-consumables bundle to the hospitals and labs on "
                    "this list, starting with joint SPD/QTS accounts in Malaysia and Indonesia, where growth is "
                    "strongest.")


# --------------------------------------------------------------------------- inbound
REVIEW_COLS = {"message_id": "Message", "subject": "Subject", "body": "Body", "predicted": "Rules result",
               "reason": "Reason", "true_label": "Correct label", "after_ai": "After AI step", "ai_reason": "AI reason"}


def inbound():
    t = c.triage()
    main, hold = t["main"], t["holdout"]
    c.header("Orders vs enquiries", f"Rules sort {(main.predicted == main.true_label).mean():.0%} of the mailbox "
                                    f"correctly and pass {(hold.predicted == 'review').sum()} of {len(hold)} messy "
                                    f"emails to a person")
    st.caption("The regional view counts orders only. This page shows how incoming emails are sorted.")
    with st.expander("How emails are sorted"):
        st.markdown("First by channel (a dedicated order inbox, and the form for setup requests), then by rules the "
                    "MDM team can read, then by an AI prompt for whatever is left. Anything uncertain goes to a "
                    "person. There is no custom model to train or maintain.")
    c.kpi_row([c.kpi(classify.LABELS[lab], int((main.predicted == lab).sum()))
               for lab in ["purchase_order", "enquiry", "follow_up", "mdm_request"]])
    by = main[main.predicted != "review"].groupby(["country", "predicted"]).size().reset_index(name="emails")
    by["predicted"] = by.predicted.map(classify.LABELS)
    label_order = [classify.LABELS[lab] for lab in ["purchase_order", "enquiry", "follow_up", "mdm_request"]]
    fig = px.bar(by, x="country", y="emails", color="predicted", barmode="stack",
                 category_orders={"country": c.COUNTRY_ORDER, "predicted": label_order},
                 color_discrete_sequence=LABEL_COLORS)
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), legend_title="", xaxis_title="")
    c.chart(fig)

    a, b = st.columns(2)
    with a:
        st.markdown("##### Accuracy on the mailbox sample (660 emails)")
        acc = (main.predicted == main.true_label).mean()
        c.kpi_row([c.kpi("Correct", acc * 100, suffix="%")])
        st.caption("Likely optimistic, because the synthetic emails follow patterns the rules were written for.")
    with b:
        st.markdown("##### Stress test: 24 hand-written messy emails")
        auto = hold[hold.predicted != "review"]
        c.kpi_row([c.kpi("Labelled by rules", len(auto), suffix=f" of {len(hold)}",
                         delta=f"{(auto.predicted == auto.true_label).mean():.0%} of those correct" if len(auto)
                         else None)])
        st.caption("The rules made no mistakes, but sent most of the messy emails to review. The AI step is "
                   "meant to handle these.")
    st.markdown("##### Review queue (stress test)")
    cols = ["message_id", "subject", "body", "predicted", "reason", "true_label"]
    view = hold[cols].copy()
    if classify.ai_available():
        if st.button("Run AI step on the review queue", type="primary"):
            res = [classify.ai_classify(r.subject, r.body, r.attachment_name) if r.predicted == "review"
                   else (r.predicted, r.confidence, r.reason) for r in hold.itertuples()]
            st.session_state["ai_res"] = res
        if "ai_res" in st.session_state:
            view["after_ai"], _, view["ai_reason"] = zip(*st.session_state["ai_res"])
    else:
        st.caption("The AI step needs an ANTHROPIC_API_KEY on this machine. In production it is Power Automate's "
                   "AI prompt action, using the same instructions.")
    st.dataframe(view.rename(columns=REVIEW_COLS), hide_index=True, width="stretch")
    with st.expander("AI instructions (the MDM team can edit these without retraining)"):
        st.code(classify.AI_PROMPT, language="text")


# --------------------------------------------------------------------------- data quality
def quality():
    q = c.data_quality()
    cl, pairs, s = q["clusters"], q["pairs"], q["score"]
    dups = cl[cl.cluster_size > 1]
    is_dup = cl.record_id != cl.golden_id
    c.header("Data quality", f"{is_dup.sum()} of {len(cl)} customer records ({is_dup.mean():.0%}) are duplicates "
                             f"of another record")
    c.kpi_row([
        c.kpi("Customer records", len(cl)),
        c.kpi("Duplicate records found", int(is_dup.sum()), delta=f"{is_dup.mean():.0%} of records", tone="bad"),
        c.kpi("Sent to human review", int((pairs.decision == "review").sum())),
        c.kpi("Duplicate item codes", len(q["item_map"])),
    ])
    st.caption(f"Checked against the synthetic answer key: precision {s['precision']:.0%}, recall {s['recall']:.0%} "
               f"({s['found_pairs']} of {s['true_pairs']} duplicate pairs). Real SAP data will be messier, which "
               f"is why borderline matches go to human review.")
    with st.expander("How matching works"):
        st.markdown("Records are only compared within the same country across SPD, QTS and QTG. The same "
                    "registration number is a match, and different numbers never are. Otherwise the matcher compares "
                    "cleaned-up names (allowing for typos, 'Hosp.' vs 'Hospital', a missing 'Pte Ltd' and "
                    "capitalisation), backed up by city and address, and recognises acronyms such as NUH. The rules "
                    "and thresholds are fixed, so there is nothing to retrain.")
    st.markdown("##### Duplicate groups")
    show = dups.sort_values(["golden_id", "created_date"])[["golden_id", "record_id", "customer_name", "country",
                                                             "created_by_entity", "created_date", "registration_no"]]
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "golden_id": st.column_config.TextColumn("Kept record"),
        "record_id": st.column_config.TextColumn("Record"),
        "customer_name": st.column_config.TextColumn("Customer"),
        "country": COUNTRY_COL,
        "created_by_entity": st.column_config.TextColumn("Created by"),
        "created_date": st.column_config.TextColumn("Created"),
        "registration_no": st.column_config.TextColumn("Registration no.")})
    if q["item_map"]:
        st.markdown("##### Duplicate items")
        items = c.raw()["items"].set_index("item_code")
        for dup, keep in q["item_map"].items():
            st.markdown(f"- `{dup}` ({items.loc[dup, 'description']}) duplicates `{keep}` "
                        f"({items.loc[keep, 'description']}). Merging them stops the dengue test from looking "
                        f"like it is declining in Thailand and Vietnam.")
    st.markdown("##### Why it matters")
    st.markdown("Merging duplicates doesn't change country totals, because each order is still counted once. It "
                "changes the per-customer figures: how many customers there are, who appears to have stopped "
                "ordering (because their orders moved to a new record), and who appears to buy only Product A "
                "(because their B orders sit on another entity's record). Sales actions shows the before-and-after "
                "difference.")


# --------------------------------------------------------------------------- business case
def _inputs(spec):
    """One row of four number inputs, so every assumption box lines up at the same size."""
    return [col.number_input(label, lo, hi, val, step, help=tip)
            for col, (label, lo, hi, val, step, tip) in zip(st.columns(4), spec)]


def business_case():
    d = c.raw()
    bd, touch = c.process_baseline()
    summary = st.container()  # filled in once the assumptions below have been read

    with st.expander("Assumptions (change these to test the case)"):
        st.markdown("**Process**")
        bounce, notice, esc, hours = _inputs([
            ("Bounces avoided (%)", 50, 100, 90, 5, "Share of bounce-backs the smart form prevents"),
            ("Approver delay cut (%)", 0, 70, 50, 5, "Share of each approver's wait that was 'didn't see the email'"),
            ("Escalate after (days)", 2, 6, 4, 1, "Business days before a stalled approval is escalated"),
            ("Hours saved per request", 0.0, 5.0, 1.5, 0.25, "MDM and approver time saved on each request")])
        st.markdown("**Value**")
        rate, save_rate, conv, margin = _inputs([
            ("Cost per hour (SGD)", 20, 150, 50, 5, "Loaded staff cost"),
            ("Drop-offs recovered (%)", 0, 50, 20, 5, None),
            ("Cross-sell conversion (%)", 0, 30, 10, 2, None),
            ("Gross margin (%)", 10, 60, 30, 5, "Sales benefits count as gross profit, not order value")])
        st.markdown("**Cost**")
        dev_weeks, dev_rate, da_weeks, licence = _inputs([
            ("Contractor (weeks)", 0, 20, 8, 1, "Power Platform contractor"),
            ("Weekly rate (SGD)", 1000, 8000, 4000, 250, "Contractor rate per week"),
            ("Data analyst (weeks)", 0, 20, 5, 1, None),
            ("Licences per year (SGD)", 0, 20000, 3000, 500, "Licences and AI credits")])

    st.markdown("##### Where the time goes today")
    c.kpi_row([
        c.kpi("Median time to SAP", d["requests"].cycle_days.median(), decimals=1, suffix=" days"),
        c.kpi("Slowest 10%", round(d["requests"].cycle_days.quantile(.9)), suffix="+ days"),
        c.kpi("Bounced back at least once", (d["requests"].bounces > 0).mean() * 100, suffix="%"),
        c.kpi("Time spent on actual work", touch * 100, decimals=1, suffix="%",
              help="The rest of the time is spent waiting"),
    ])
    fig = px.bar(bd, x="share", y="stage", orientation="h", text_auto=".0%", color_discrete_sequence=["#1f4e79"])
    fig.update_layout(height=220, margin=dict(l=0, r=0, t=10, b=0), xaxis_tickformat=".0%", yaxis_title="",
                      xaxis_title="share of elapsed time")
    c.chart(fig)

    st.markdown("##### With OneRecord (simulated on the same 150 requests)")
    sim = process.simulate(d["requests"], d["steps"], bounce_avoided=bounce / 100, notice_cut=notice / 100,
                           escalate_after_days=esc)
    now_med, fut_med = sim.cycle_days.median(), sim.future_days.median()
    slow_chg = sim.future_days.quantile(.9) - sim.cycle_days.quantile(.9)
    c.kpi_row([
        c.kpi("Median time to SAP", fut_med, decimals=1, suffix=" days", delta=f"{fut_med - now_med:+.1f} days",
              tone=c.tone(fut_med - now_med, up_is_good=False)),
        c.kpi("Slowest 10%", sim.future_days.quantile(.9), decimals=1, suffix=" days", delta=f"{slow_chg:+.1f} days",
              tone=c.tone(slow_chg, up_is_good=False)),
        c.kpi("Faster", (1 - fut_med / now_med) * 100, suffix="%"),
    ])
    long = pd.concat([sim.assign(scenario="Today (email)", days=sim.cycle_days),
                      sim.assign(scenario="OneRecord", days=sim.future_days)])
    fig = px.histogram(long, x="days", color="scenario", barmode="overlay", nbins=40, opacity=0.7,
                       color_discrete_map=SCENARIO_COLORS)
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), legend_title="")
    c.chart(fig)
    c.assumption("parallel approvals use the same historical approver waiting times, and only the settings above "
                 "change. These are simulated results; a 4-week pilot with one entity would confirm them.")

    st.markdown("##### Value and cost (first year)")
    cmp, q = c.regional()["compare"], c.data_quality()
    ncv = process.new_customer_value(d["requests"], c.regional()["clean"], q["clusters"], now_med - fut_med)
    save_rate, conv, margin = save_rate / 100, conv / 100, margin / 100
    req_per_year = len(d["requests"]) / 1.5
    benefits = {
        "Staff time (requests × hours × rate)": req_per_year * hours * rate,
        "Gross profit pulled forward (new accounts live sooner)": ncv["pulled_forward_per_year"] * margin,
        "Gross profit kept (drop-offs recovered)": cmp["clean_drop"].value_at_risk_per_q.sum() * 4 * save_rate * margin,
        "Gross profit from cross-sell": cmp["clean_xsell"].est_value_sgd_per_year.sum() * conv * margin,
    }
    costs = {"Workflow build (contractor)": dev_weeks * dev_rate, "Analytics build": da_weeks * 3000,
             "Licences & AI credits": licence, "MDM team time (rules, training) ~4 weeks": 4 * 40 * rate}
    b, co = sum(benefits.values()), sum(costs.values())
    left, right = st.columns(2)
    left.dataframe(pd.DataFrame({"Benefit (SGD / year)": benefits}).round(0), width="stretch")
    right.dataframe(pd.DataFrame({"Cost (SGD, year 1)": costs}).round(0), width="stretch")
    with summary:
        c.header("Business case", f"Pays back in {12 * co / b:.1f} months, with requests reaching SAP in "
                                  f"{fut_med:.1f} days instead of {now_med:.1f}" if b else
                                  "These assumptions don't produce a benefit")
        c.kpi_row([
            c.kpi("Payback", 12 * co / b, decimals=1, suffix=" months") if b else c.kpi("Payback", "—"),
            c.kpi("Annual benefit", b, prefix="S$"),
            c.kpi("Year-1 cost", co, prefix="S$"),
            c.kpi("Median time to SAP", fut_med, decimals=1, suffix=" days", delta=f"{fut_med - now_med:+.1f} days",
                  tone=c.tone(fut_med - now_med, up_is_good=False)),
        ])
    c.assumption("sales-driven benefits are counted at gross margin rather than order value. Rates, hours, margin "
                 "and conversion are placeholders to agree with Lives Group. Staff time savings alone don't cover "
                 "the build cost; most of the benefit comes from new accounts going live sooner and from sales "
                 "acting on the clean data.")
    _roadmap(dev_weeks, da_weeks)


ROADMAP = [
    ("Phase 1: Fix the front door", "Weeks 1–10",
     ["Power Apps form with required fields and live duplicate check",
      "Parallel approvals in Teams, reminders, escalation, live status",
      "Restricted list for bank details and credit terms; audit log",
      "Rule lists the MDM team edits (business units, fields, approvers)",
      "SAP B1 import file, so Priya stops retyping",
      "One-off clean-up: merge the 41 duplicate customers, review queue for look-alikes",
      "4-week pilot with SPD, then QTS and QTG"],
     "Power Platform contractor ({dev} weeks); MDM team sets up rules and runs the pilot; IT does a one-off site, "
     "permissions and Teams setup",
     "Median time to SAP of 5 days or less in the pilot; at least 90% of requests through the form"),
    ("Phase 2: Use the clean data", "Months 3–6",
     ["Regional view in Power BI inside Teams",
      "Monthly forecast and stock plan replace the 6-month average spreadsheet",
      "Drop-off and cross-sell lists to account managers each month",
      "Email sorting: rules, then an AI prompt, then a person",
      "Monthly AI action brief posted to the sales channel"],
     "Data analyst ({da} weeks); IT enables AI Builder once; Sales ops owns the monthly review",
     "Forecast beats the 6-month average 3 months running; top-10 drop-offs contacted within 2 weeks"),
    ("Phase 3: Connect and scale", "After month 6, only if Phase 1–2 targets are met",
     ["Direct SAP B1 connection (Service Layer) replaces the import file",
      "Form calls the full matching engine (typo-tolerant) through one Premium connector",
      "Same duplicate clean-up for items and vendors",
      "New data domains added as rule rows, e.g. price lists"],
     "SAP B1 partner (outside help); Premium licence for the connector",
     "Request volume and error rate justify the integration cost"),
]

NOT_IN_V1 = [
    ("Direct write into SAP B1", "The import file removes the retyping at almost no risk. A live integration needs an "
                                 "SAP partner and testing, so it waits for Phase 3."),
    ("Automatic merging of duplicates", "Merging touches open orders and invoices. The matcher proposes and a person "
                                        "confirms, until it has a track record on real data."),
    ("Custom-trained AI models", "12–18 months of history is too short to train well, and someone would have to "
                                 "retrain them. Rules, a calendar-based forecast and an off-the-shelf AI prompt need "
                                 "no upkeep."),
    ("A custom web app or portal", "Power Apps, Power Automate and SharePoint are already licensed and the MDM team can "
                                   "change them. A custom app needs developers Lives Group doesn't have."),
    ("Premium connectors or Dataverse", "Standard licences keep cost and IT approval small. The one Premium connector "
                                        "comes in Phase 3, if it is worth it."),
    ("A full security redesign", "Bank details and credit terms move to a locked-down list with an audit trail. "
                                 "Field-level encryption and role redesign can follow if audit asks."),
    ("Monthly forecasts for Product C", "Equipment sells 30–50 units per country per half-year, too lumpy to forecast. "
                                        "It is planned from the sales pipeline instead."),
]


def _roadmap(dev_weeks, da_weeks):
    st.markdown("##### Roadmap and scope")
    with st.expander("Roadmap"):
        st.caption("Sized for a small team: one contractor and one analyst, with the MDM team owning the rules. Each "
                   "phase starts only when the previous one hits its targets. The year-1 cost above covers Phases 1 "
                   "and 2; Phase 3 is priced with an SAP partner once Phase 1–2 results are in.")
        for col, (title, when, items, who, gate) in zip(st.columns(3), ROADMAP):
            with col.container(border=True, height="stretch"):
                st.markdown(f"**{title}**  \n*{when}*")
                st.markdown("\n".join(f"- {i}" for i in items))
                st.markdown(f"**Who:** {who.format(dev=dev_weeks, da=da_weeks)}")
                st.markdown(f"**Move on when:** {gate}")
        st.markdown("**Moving people off email (Phase 1):** the MDM mailbox auto-replies with a link to the form. "
                    "After a cut-over date, requests sent by email are not processed. The form sits as a tab in each "
                    "team's Teams channel, and BU heads get a monthly report of the share of requests that came "
                    "through it.")
    with st.expander("Not in version 1"):
        st.table(pd.DataFrame(NOT_IN_V1, columns=["Not building", "Reason"]).set_index("Not building"))
