"""Regional business view: growth, forecasting, sales actions, inbound triage, data quality, business case."""
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from onerecord import advisor, classify, insights, process
from onerecord.config import COUNTRIES, CURRENT, GROWTH_LABEL, PRIOR_YEAR, PRODUCTS

from . import common as c
from . import theme

COLORS = theme.PRODUCT
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
    c.header("Country deep-dive", headline)

    tot_now, tot_prev = g.units_now.sum(), g.units_prev.sum()
    val_now, val_prev = g.value_now.sum(), g.value_prev.sum()
    best = g.loc[g[g["product"] != "C"].unit_growth.idxmax()]
    units_chg, value_chg = tot_now / tot_prev - 1, val_now / val_prev - 1
    clean = c.regional()["clean"]
    active = lambda w: clean[(clean.month >= w[0]) & (clean.month <= w[1])].customer_id.nunique()
    cust_now, cust_prev = active(CURRENT), active(PRIOR_YEAR)
    vs = f"vs {c.period(PRIOR_YEAR)}"  # every change on these cards compares with the same months a year earlier
    c.kpi_row([
        c.kpi(f"Units, {c.period(CURRENT)}", tot_now, delta=f"{c.pct(units_chg)} {vs}", tone=c.tone(units_chg)),
        c.kpi(f"Order value (SGD), {c.period(CURRENT)}", val_now / 1e6, decimals=2, suffix="M",
              delta=f"{c.pct(value_chg)} {vs}", tone=c.tone(value_chg)),
        c.kpi(f"Active customers, {c.period(CURRENT)}", cust_now, delta=f"{cust_now - cust_prev:+,} {vs}",
              tone=c.tone(cust_now - cust_prev),
              help="Customers who ordered at least once in the period, counted after merging duplicate records"),
        c.kpi("Fastest growing (A/B)", f"{COUNTRIES[best.country]}, {best['product']}",
              delta=f"{c.pct(best.unit_growth)} units {vs}", tone=c.tone(best.unit_growth),
              help="The country and product (A or B) whose units grew most. Product C is left out: its volumes "
                   "are too small for a fair comparison."),
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
        fig.update_layout(height=row_h - 16, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
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

    _country_focus()
    _by_entity()

    st.markdown("##### Monthly units by country")
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
        f"accounts need follow-up from sales (see Customers).\n"
        f"- Singapore is a mature market: growth is in single digits and equipment sales are falling. Most new "
        f"growth there will come from selling more products to existing customers.")


def _by_entity():
    """SPD, QTS and QTG side by side, and how many customers buy from more than one of them."""
    clean = c.regional()["clean"]
    st.markdown("##### By business entity")
    between = lambda w: clean[(clean.month >= w[0]) & (clean.month <= w[1])]
    now, prev = between(CURRENT), between(PRIOR_YEAR)
    t = now.groupby("entity").agg(products=("product", lambda s: ", ".join(c.PRODUCT_LABEL[p] for p in sorted(s.unique()))),
                                  units=("quantity", "sum"), value=("line_value_sgd", "sum"),
                                  customers=("customer_id", "nunique"), countries=("country", "nunique"))
    t["growth"] = (t.units / prev.groupby("entity").quantity.sum().reindex(t.index) - 1) * 100
    t["share"] = t.value / t.value.sum() * 100
    t["value"] = t.value.round()
    t = t.sort_values("value", ascending=False).reset_index()
    t = t[["entity", "products", "units", "growth", "value", "share", "customers", "countries"]]
    st.dataframe(t, hide_index=True, width="stretch", height=c.table_height(len(t)), column_config={
        "entity": st.column_config.TextColumn("Entity"),
        "products": st.column_config.TextColumn("Sells"),
        "units": st.column_config.NumberColumn("Units", format="localized"),
        "growth": st.column_config.NumberColumn("YoY", format="%+.0f%%"),
        "value": st.column_config.NumberColumn("Value (SGD)", format="localized"),
        "share": st.column_config.NumberColumn("Share of value", format="%.0f%%"),
        "customers": st.column_config.NumberColumn("Customers"),
        "countries": st.column_config.NumberColumn("Countries")})
    n = now.groupby("customer_id").entity.nunique()
    shared = n[n > 1].index
    value_share = now[now.customer_id.isin(shared)].line_value_sgd.sum() / now.line_value_sgd.sum()
    st.caption(f"Apr–Sep 2026, units {GROWTH_LABEL}. In this data each entity sells one product line, so an "
               f"entity's growth is its product's growth. The entity view matters for customers: {len(shared)} of "
               f"{len(n)} customers buy from more than one entity, and they make up {value_share:.0%} of order value. "
               f"Merging duplicate records is what lets one hospital show up as one customer across SPD, QTS and "
               f"QTG, which is where the cross-sell list on Customers comes from.")


def _country_focus():
    """One country: each product's monthly units, and the customers that order the most."""
    clean = c.regional()["clean"]
    st.markdown("##### Country focus")
    k = c.select(st, "Country", c.COUNTRY_ORDER, key="cd_country", format_func=lambda k: COUNTRIES[k])
    d = clean[clean.country == k]
    left, right = st.columns([1, 1.15], gap="medium")
    with left:
        st.markdown(f"###### Monthly units by product, {COUNTRIES[k]}")
        mm = d.groupby(["month", "product"]).quantity.sum().reset_index()
        fig = go.Figure()
        for p in PRODUCTS:
            one = mm[mm["product"] == p]
            fig.add_scatter(x=one.month, y=one.quantity, name=c.PRODUCT_LABEL[p], mode="lines+markers",
                            line=dict(color=COLORS[p], width=2.5), marker=dict(size=6),
                            hovertemplate="%{y:,.0f} units<extra>" + p + "</extra>")
            # label each line at its end: the product colours alone are hard to tell apart for colour-blind readers
            fig.add_annotation(x=one.month.iloc[-1], y=one.quantity.iloc[-1], text=f"<b>{p}</b>", showarrow=False,
                               xanchor="left", xshift=8, font=dict(color=COLORS[p], size=13))
        fig.update_layout(height=c.table_height(10) - 16, margin=dict(l=0, r=24, t=10, b=0), yaxis_title="units",
                          xaxis_title="", showlegend=False, hovermode="x unified")
        c.chart(fig)
    with right:
        st.markdown("###### Top 10 customers by order value, Apr–Sep 2026")
        between = lambda w: d[(d.month >= w[0]) & (d.month <= w[1])]
        now, prev = between(CURRENT), between(PRIOR_YEAR)
        top = now.groupby("customer").agg(value=("line_value_sgd", "sum"), units=("quantity", "sum"),
                                          products=("product", lambda s: ", ".join(sorted(s.unique()))))
        top = top.nlargest(10, "value")
        before = prev.groupby("customer").line_value_sgd.sum().reindex(top.index)
        top["growth"] = (top.value / before - 1) * 100  # blank for customers with no orders a year earlier
        top["value"] = top.value.round()
        st.dataframe(top.reset_index(), hide_index=True, width="stretch", height=c.table_height(10),
                     column_config={
                         "customer": st.column_config.TextColumn("Customer", width="large"),
                         "value": st.column_config.NumberColumn("Value (SGD)", format="localized"),
                         "units": st.column_config.NumberColumn("Units", format="localized"),
                         "products": st.column_config.TextColumn("Buys"),
                         "growth": st.column_config.NumberColumn("YoY value", format="%+.0f%%",
                                                                 help="Blank: no orders a year earlier")})
    share = top.value.sum() / now.line_value_sgd.sum()
    st.caption(f"The top 10 customers make up {share:.0%} of {COUNTRIES[k]}'s order value. Customers are counted "
               f"after merging duplicate records, so one hospital appears once across SPD, QTS and QTG.")


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
    from onerecord.forecast import mape, wape
    ab = bt[bt["product"] != "C"]
    mape_ma6, mape_model = mape(ab, "baseline_ma6"), mape(ab, "calendar_model")
    cut = 1 - wape(ab, "calendar_model") / wape(ab, "baseline_ma6")
    c.header("Forecasting", f"The calendar model cuts forecast error by {cut:.0%} compared with the 6-month average")
    c.kpi_row([
        c.kpi("Today: 6-month average", wape(ab, "baseline_ma6") * 100, decimals=1, suffix="% error"),
        c.kpi("AI calendar model", wape(ab, "calendar_model") * 100, decimals=1, suffix="% error",
              delta=f"{cut:.0%} lower than 6-month avg", tone=c.tone(-cut, up_is_good=False),
              help=f"{wape(ab, 'calendar_model'):.1%} vs {wape(ab, 'baseline_ma6'):.1%}: the model's misses are "
                   f"{cut:.0%} smaller than today's 6-month average."),
        c.kpi("Series improved", (acc[acc["product"] != "C"].Improvement > 0).sum(), suffix=" of 10",
              help="Products A and B"),
        c.kpi("MAPE, AI model", mape_model * 100, decimals=1, suffix="%",
              delta=f"{(mape_model - mape_ma6) * 100:+.1f} pts vs 6-month avg",
              tone=c.tone(mape_model - mape_ma6, up_is_good=False),
              help=f"Average % miss per month. The 6-month average's MAPE is {mape_ma6:.1%}."),
    ])
    st.caption("Error is measured as WAPE: total absolute error divided by actual units. MAPE is the average of "
               "each month's % miss, so small months count as much as big ones and it runs higher. Both cover "
               "Products A and B, forecasting 1–3 months ahead from each month Apr–Sep 2026, using only the data "
               "available at the time. The charts below forecast 6 months ahead; see how far ahead it holds at the "
               "bottom of the page.")

    with st.expander("How the model works", expanded=False):
        st.markdown(
            "The 6-month average gives every month the same weight, so it reacts late to dengue season and the "
            "December budget flush. The calendar model starts from each series' level and trend, then adjusts for "
            "events Lives Group already plans around: dengue season in each country (Product A), the hospital "
            "year-end push, the January slowdown, and public holidays such as Lunar New Year, Tet, Songkran and "
            "Hari Raya. It estimates the size of each effect from all five countries together, which is why 12–18 "
            "months of history is enough. It is re-run each month alongside an error report.")
    _seasonality(f["effects"])

    s1, s2, s3 = st.columns([2, 2, 1.3], vertical_alignment="bottom")
    country = c.select(s1, "Country", [ALL, *c.COUNTRY_ORDER], index=1 + c.COUNTRY_ORDER.index("TH"),
                           format_func=lambda k: "All countries" if k == ALL else COUNTRIES[k])
    prod = c.select(s2, "Product", list(PRODUCTS), format_func=lambda p: c.PRODUCT_LABEL[p])
    show_ma6 = s3.toggle("Show 6-month average", disabled=country == ALL,
                         help="Pick a single country to compare with the 6-month average")
    if country == ALL:
        _forecast_all(f, prod)
    else:
        _forecast_one(f, country, prod, show_ma6)

    _horizon(f["backtest_long"])

    st.markdown("##### Accuracy by series")
    st.dataframe(acc, hide_index=True, width="stretch", column_config={
        "country": COUNTRY_COL,
        "product": PRODUCT_COL,
        "MA6 error": st.column_config.NumberColumn("6-month average error", format="percent"),
        "Model error": st.column_config.NumberColumn(format="percent"),
        "Improvement": st.column_config.NumberColumn(format="percent"),
        "MA6 MAPE": st.column_config.NumberColumn("6-month average MAPE", format="percent"),
        "Model MAPE": st.column_config.NumberColumn(format="percent")})
    st.markdown(
        "The largest gains are for Product A in Indonesia, Malaysia and Thailand, where the 6-month average misses "
        "dengue season. Singapore A gets slightly worse because its dengue effect is milder than the regional "
        "estimate; a Singapore-specific effect can be added once there is more history. Vietnam B is poor under "
        "both methods because the drop comes from lost accounts, which the drop-off alerts on Customers cover. "
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


def _horizon(bt):
    """Error by how many months ahead the forecast was made, Products A and B."""
    from onerecord.forecast import wape
    st.markdown("##### How far ahead the forecast holds")
    ab = bt[bt["product"] != "C"]
    h = ab.groupby("horizon").apply(lambda g: pd.Series({"model": wape(g, "calendar_model"),
                                                         "ma6": wape(g, "baseline_ma6"),
                                                         "tests": g.origin.nunique()}), include_groups=False)
    fig = go.Figure()
    fig.add_scatter(x=h.index, y=h.ma6, name="6-month average (today)", mode="lines+markers",
                    line=dict(color=theme.BASELINE, width=2, dash="dot"),
                    hovertemplate="%{y:.1%} error<extra>6-month average</extra>")
    fig.add_scatter(x=h.index, y=h.model, name="AI calendar model", mode="lines+markers",
                    line=dict(color=theme.FORECAST, width=2.5), customdata=h.tests,
                    hovertemplate="%{y:.1%} error, %{customdata} starting months<extra>AI model</extra>")
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), yaxis=dict(tickformat=".0%", rangemode="tozero"),
                      xaxis=dict(title="months ahead", dtick=1), legend=dict(orientation="h", y=1.12))
    c.chart(fig)
    st.caption(f"Each point is the error (WAPE) of forecasts made that many months ahead, starting from each month "
               f"Jan–Sep 2026 that still has actual orders to check against: {int(h.tests.iloc[0])} starting months "
               f"for 1 month ahead, {int(h.tests.iloc[-1])} for 6 months ahead. With 18 months of history, 7–12 "
               f"months ahead can't be checked yet, so the forecast stops at 6.")


def _seasonality(effects):
    st.markdown("##### Seasonality the model learned")
    eff = pd.Series(effects).sort_values()
    fig = go.Figure(go.Bar(x=eff.values, y=eff.index, orientation="h", text=[f"{v:+.0%}" for v in eff.values],
                           textposition="outside", cliponaxis=False,
                           marker_color=[theme.GOOD if v >= 0 else theme.BAD for v in eff.values],
                           hovertemplate="%{y}: %{x:+.1%} units<extra></extra>"))
    fig.update_layout(height=40 + 30 * len(eff), margin=dict(l=0, r=40, t=10, b=0), xaxis_tickformat="+.0%",
                      xaxis_title="change in units in the months the event applies", yaxis_title="")
    c.chart(fig)
    st.caption("Estimated from all five countries together. The 6-month average has none of these, which is why "
               "it lags dengue season and the year-end budget spend.")


def _forecast_one(f, country, prod, show_ma6):
    """One country: actual orders, the back-test, and the next 6 months with a likely range."""
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
        fig.add_scatter(x=ahead.month, y=ahead.baseline_ma6, name="6-month average, next 6 months", mode="lines",
                        line=dict(color="#aaa", dash="dash"))
    fig.add_scatter(x=ahead.month, y=ahead.calendar_model, name="Calendar model, next 6 months", mode="lines+markers",
                    line=dict(color=COLORS[prod], dash="dash"))
    # legend pinned to the bottom of the figure, in the space left under the month labels, so it can't cover them
    fig.update_layout(height=440, margin=dict(l=0, r=0, t=10, b=70), yaxis_title="units",
                      legend=dict(orientation="h", x=0, y=0, yanchor="bottom", yref="container"))
    c.chart(fig)
    row = acc[(acc.country == country) & (acc["product"] == prod)].iloc[0]
    st.caption(f"{COUNTRIES[country]}, product {prod}: the 6-month average's error is {row['MA6 error']:.1%}, "
               f"the model's is {row['Model error']:.1%}.")


def _forecast_all(f, prod):
    """Every country on one chart: actual orders solid, the next 6 months' forecast dashed in the same colour."""
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
    st.caption(f"Solid lines are actual orders; dashed lines are the calendar model's forecast for the next 6 months. "
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
        st.info("The preview needs an OPENAI_API_KEY on this machine. The stock plan above works without it.")
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
                         "be checked in the data below. The preview uses OpenAI; production would run the same "
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
    c.header("Customers", f"{len(cmp['clean_drop'])} customers are ordering much less, with about "
                              f"S${cmp['clean_drop'].value_at_risk_per_q.sum():,.0f} a quarter at risk")
    raw = st.toggle("Data check: show raw SAP records (before duplicates are merged)",
                    help="Runs the same analysis on the customer records as they sit in SAP today, to show what "
                         "duplicate records do to the alerts. It checks the data; it isn't a business benchmark.")
    if raw:
        golden = c.data_quality()["clusters"].set_index("record_id").golden_id
        drop = _flag_false(cmp["raw_drop"], cmp["clean_drop"], golden)
        xsell = _flag_false(cmp["raw_xsell"], cmp["clean_xsell"], golden)
        false_drop, false_xsell = (drop.status != "Real").sum(), (xsell.status != "Real").sum()
    else:
        drop, xsell = cmp["clean_drop"], cmp["clean_xsell"]

    at_risk = drop.value_at_risk_per_q.sum()
    if raw:
        c.kpi_row([
            c.kpi("Customer records in SAP", cmp["raw_customers"]),
            c.kpi("Drop-off alerts", len(drop), delta=f"{false_drop} not real", tone="bad"),
            c.kpi("Cross-sell leads", len(xsell), delta=f"{false_xsell} not real", tone="bad"),
            c.kpi("Value at risk per quarter", at_risk, prefix="S$")])
    else:
        # each card is compared with a business benchmark; what duplicates did to the numbers is the data check below
        clean = c.regional()["clean"]
        between = lambda w: clean[(clean.month >= w[0]) & (clean.month <= w[1])]
        last_q = between(insights.RECENT)
        year_ago = between(insights.RECENT_PRIOR).groupby("customer_id").quantity.sum()
        established = int((year_ago >= insights.MIN_QUARTER_UNITS).sum())
        conv = 0.10  # same conversion rate as the business case
        c.kpi_row([
            c.kpi("Customers, Apr 2025–Sep 2026", cmp["clean_customers"],
                  delta=f"{cmp['raw_customers'] - cmp['clean_customers']} duplicate records merged",
                  help="One hospital or lab counts once, however many SAP records SPD, QTS and QTG created for it."),
            c.kpi("Drop-off alerts", len(drop), delta=f"{len(drop) / established:.0%} of established customers",
                  tone="bad", help=f"Ordered at least 40% less in Jul–Sep 2026 than in Jul–Sep 2025 and than their own "
                                   f"recent average. Established = at least {insights.MIN_QUARTER_UNITS} units in "
                                   f"Jul–Sep 2025 ({established} customers)."),
            c.kpi("Cross-sell leads", len(xsell),
                  delta=f"S${xsell.est_value_sgd_per_year.sum() * conv / 1000:,.0f}k a year if {conv:.0%} convert",
                  tone="good", help="Customers who buy A but not B (or B but not A), while most similar customers "
                                    "buy both."),
            c.kpi("Value at risk per quarter", at_risk, prefix="S$", tone="bad",
                  delta=f"{at_risk / last_q.line_value_sgd.sum():.0%} of last quarter's order value"),
        ])
        st.caption(f"Data check: on the raw SAP records, before duplicates are merged, the same rules raise "
                   f"{len(cmp['raw_drop'])} drop-off alerts and {len(cmp['raw_xsell'])} cross-sell leads. "
                   f"{len(cmp['raw_drop']) - len(drop)} and {len(cmp['raw_xsell']) - len(xsell)} more than above: "
                   f"a customer whose orders moved to a new record looks like they stopped ordering, and one hospital "
                   f"split into an A-only and a B-only record looks like a cross-sell gap. Use the switch above to "
                   f"see which ones.")
    if raw:
        st.warning(f"On raw records, {false_drop} of {len(drop)} drop-off alerts and {false_xsell} of {len(xsell)} "
                   f"cross-sell leads are false or counted twice, because the same customer has more than one record. "
                   f"Turn the switch off to see the cleaned view.")

    status = ["status"] if raw else []
    quiet = c.regional()["quiet"]
    t1, t0, t2 = st.tabs([f"Call list: dropping off ({len(drop)})", f"Early warning: gone quiet ({len(quiet)})",
                          f"Cross-sell opportunities ({len(xsell)})"])
    with t1:
        # one ranked list to work down: biggest value at risk first, with the reason it was flagged in words
        d = drop.reset_index(drop=True)
        d.insert(0, "rank", d.index + 1)
        d["why"] = [f"{now:,.0f} units in Jul–Sep vs {before:,.0f} a year earlier ({chg:+.0%})"
                    for now, before, chg in zip(d.units_last_q, d.units_same_q_last_year, d.change)]
        d["action"] = ["Call within 2 weeks" if r <= 10 else "Call this quarter" for r in d["rank"]]
        st.markdown(f"{len(d)} established customers ordered at least 40% less last quarter than in the same "
                    f"quarter last year, and than their own recent average. Value at risk is about "
                    f"S${d.value_at_risk_per_q.sum():,.0f} per quarter. Ranked by value at risk: work down from #1.")
        st.dataframe(d[["rank"] + status + ["name", "country", "why", "value_at_risk_per_q", "last_order",
                                            "action"]], hide_index=True, width="stretch",
                     column_config={
            "rank": st.column_config.NumberColumn("#", width="small"),
            "status": STATUS_COL,
            "name": st.column_config.TextColumn("Customer"),
            "country": COUNTRY_COL,
            "why": st.column_config.TextColumn("Why flagged", width="large"),
            "value_at_risk_per_q": st.column_config.NumberColumn("At risk per quarter (SGD)", format="localized"),
            "last_order": st.column_config.TextColumn("Last order"),
            "action": st.column_config.TextColumn("Next step")})
        st.markdown("**Suggested next step:** account managers call the top 10 within two weeks and record the "
                    "reason they hear (competitor, budget, service issue), so patterns by country become visible.")
    with t0:
        q = quiet.copy()
        q.insert(0, "rank", q.index + 1)
        q["why"] = [f"No order for {s} days; usually orders every {g} days"
                    for s, g in zip(q.days_since, q.usual_gap)]
        q["confirmed"] = q.id.isin(c.regional()["compare"]["clean_drop"].id).map({True: "Yes", False: ""})
        st.markdown(f"{len(q)} larger customers have gone quiet: no order for longer than 9 in 10 of their own past "
                    f"gaps between orders, and for at least 45 days. This can show up a month or two before a "
                    f"customer counts as dropping off, which needs a full quarter of lower orders.")
        st.dataframe(q[["rank", "name", "country", "why", "value_per_q", "last_order", "confirmed"]],
                     hide_index=True, width="stretch", column_config={
            "rank": st.column_config.NumberColumn("#", width="small"),
            "name": st.column_config.TextColumn("Customer"),
            "country": COUNTRY_COL,
            "why": st.column_config.TextColumn("Why flagged", width="large"),
            "value_per_q": st.column_config.NumberColumn("Usual order value per quarter (SGD)",
                                                          format="localized"),
            "last_order": st.column_config.TextColumn("Last order"),
            "confirmed": st.column_config.TextColumn("Also on call list",
                                                     help="Already dropping off on the quarter rule")})
        st.markdown("**Suggested next step:** not a call about the missed order. The account manager makes their "
                    "next routine check-in early (e.g. \"your usual kits are due, shall we hold stock?\") and "
                    "notes anything they hear, such as a lost tender or a new supplier.")
        c.assumption("only the top half of regular customers by order value is watched, so smaller buyers who "
                     "order late don't create work. Calculated on merged customer records.")
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
               "reason": "Rules reason", "true_label": "Correct label", "after_ai": "After AI step",
               "ai_reason": "AI reason"}


def _after_ai(hold, ai):
    """Each stress-test email's final label: the rules' label, else the AI's when it was sure, else a person."""
    d = hold.merge(ai, on="message_id", how="left")
    d["after_ai"] = d.ai_label.where(d.ai_confidence == "high", "review").where(d.predicted == "review",
                                                                                d.predicted)
    return d


def _score(d):
    """How one AI run did on the emails the rules passed on. Orders affected = a non-order counted as an order, or
    an order missed: the mistakes that would change the regional view's order counts."""
    q = d[d.predicted == "review"]
    sure = q[q.after_ai != "review"]
    as_order, is_order = sure.after_ai == "purchase_order", sure.true_label == "purchase_order"
    return {"Sorted by AI": len(sure), "Correct": int((sure.after_ai == sure.true_label).sum()),
            "Wrong": int((sure.after_ai != sure.true_label).sum()), "Left for a person": len(q) - len(sure),
            "Orders affected": int((as_order != is_order).sum())}


def inbound():
    t = c.triage()
    main, hold = t["main"], t["holdout"]
    runs = c.ai_step_runs()
    scores = {name: _score(_after_ai(hold, ai)) for name, ai in runs.items()}
    no_order_errors = all(s["Orders affected"] == 0 for s in scores.values())
    c.header("Orders vs enquiries",
             f"Rules sort {(main.predicted == main.true_label).mean():.0%} of the mailbox correctly"
             + (f"; on {len(hold)} messy emails, no AI run counted a non-order as an order or missed one"
                if no_order_errors else ""))
    st.caption("The regional view counts orders only. This page shows how incoming emails are sorted.")
    request = c.PAGES.get("new-request")
    if request is not None and c.allowed(request):
        st.page_link(request, label="Setup requests that arrive by email are answered with a link to the request form",
                     icon=":material/arrow_forward:")
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

    # the stress test, stage by stage: rules first, the AI step for what they pass on, a person for what's left
    by_rules = hold[hold.predicted != "review"]
    queued = len(hold) - len(by_rules)
    st.markdown(f"##### Accuracy on the mailbox sample ({len(main)} emails) and a stress test of {len(hold)} "
                f"hand-written messy emails")
    run = st.radio("AI run shown", list(runs), horizontal=True, key="ai_run",
                   help="Both runs used the same instructions (below) and got the emails without their correct labels")
    s = scores[run]
    c.kpi_row([
        c.kpi("Mailbox sample, rules", (main.predicted == main.true_label).mean() * 100, suffix="% correct",
              help="Likely optimistic: the synthetic emails follow patterns the rules were written for"),
        c.kpi("Messy emails, rules", len(by_rules), suffix=f" of {len(hold)}", tone="good",
              delta=f"{(by_rules.predicted == by_rules.true_label).mean():.0%} of those correct"),
        c.kpi("Messy emails, AI step", s["Correct"], suffix=f" of {queued} correct", key="ai-correct",
              delta=f"{s['Wrong']} wrong" if s["Wrong"] else "none wrong", tone="bad" if s["Wrong"] else "good",
              help="The emails the rules passed on, sorted by the AI run picked above"),
        c.kpi("Left for a person", s["Left for a person"], suffix=f" of {len(hold)}", key="ai-person",
              help="The AI run marked these as unsure"),
    ])
    st.dataframe(pd.DataFrame(scores).T.rename_axis("AI run").reset_index(), hide_index=True, width="stretch",
                 column_config={"Orders affected": st.column_config.NumberColumn(
                     help="A non-order counted as an order, or an order missed: the mistakes that would change the "
                          "regional view's order counts")})
    st.caption(f"Rules sort the standard emails and pass anything unclear on. The AI step reads the rest, "
               f"including Malay, Thai and Vietnamese. Both AI runs used the instructions below on the {queued} "
               f"emails the rules passed on, without their correct labels. Their mistakes mixed up enquiries and "
               f"follow-ups; neither counted a non-order as an order or missed an order, so the regional view's "
               f"order counts would be right either way. The small API model never marked itself unsure, so in "
               f"production a person should still spot-check its answers. In production this step runs on AI "
               f"Builder in Power Automate, so re-check the score in the pilot. {len(hold)} emails is a small test."
               if no_order_errors else
               f"Rules sort the standard emails and pass anything unclear on. The AI step reads the rest. Both AI "
               f"runs used the instructions below without the emails' correct labels. {len(hold)} emails is a small "
               f"test; re-check the score in the pilot.")

    st.markdown("##### Review queue (stress test)")
    view = _after_ai(hold[["message_id", "subject", "body", "predicted", "reason", "true_label"]], runs[run])
    if classify.ai_available():  # with a key, the AI step can be re-run live instead of showing the recorded run
        if st.button("Re-run the AI step live", type="primary"):
            st.session_state["ai_res"] = [
                classify.ai_classify(r.subject, r.body, r.attachment_name) if r.predicted == "review"
                else (r.predicted, r.confidence, r.reason) for r in hold.itertuples()]
        if "ai_res" in st.session_state:
            view["after_ai"], _, view["ai_reason"] = zip(*st.session_state["ai_res"])
    for col in ["predicted", "after_ai", "true_label"]:
        view[col] = view[col].map(classify.LABELS)
    # each stage's result side by side, with the correct label last to check them against
    view = view[["message_id", "subject", "body", "predicted", "reason", "after_ai", "ai_reason", "true_label"]]
    st.dataframe(view.rename(columns=REVIEW_COLS), hide_index=True, width="stretch")
    with st.expander("AI instructions (the MDM team can edit these without retraining)"):
        st.code(classify.AI_PROMPT, language="text")


# --------------------------------------------------------------------------- data quality
ESCALATE_DAYS = 4  # same default as the escalation setting on the Business case page


def _cycle_time():
    d = c.raw()
    req, steps = d["requests"], d["steps"]
    bd, _ = c.process_baseline()
    waiting = bd.set_index("stage").share.get("Waiting for approvers", 0)
    c.header("MDM ops", f"Requests take {req.cycle_days.median():.0f} days to reach SAP, and {waiting:.0%} of that "
                        f"is waiting for approvers")
    c.kpi_row([
        c.kpi("Median time to SAP", req.cycle_days.median(), decimals=1, suffix=" days"),
        c.kpi("Slowest 10%", round(req.cycle_days.quantile(.9)), suffix="+ days"),
        c.kpi("Bounced back at least once", (req.bounces > 0).mean() * 100, suffix="%", tone="bad"),
        c.kpi("Requests, 18 months", len(req), help=f"{req.submitted_at.min()[:10]} to {req.submitted_at.max()[:10]}, "
                                                     f"from the email request history"),
    ])
    st.caption("Today's email process, measured from the request history. The workflow replaces these steps; "
               "Business case simulates the same requests under OneRecord.")

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown("##### Request cycle time by type")
        t = req.groupby("request_type").cycle_days.agg(["median", "count"]).sort_values("median")
        fig = go.Figure(go.Bar(x=t["median"], y=t.index, orientation="h", marker_color=theme.PRIMARY,
                               text=[f"{m:.0f} days ({n} requests)" for m, n in zip(t["median"], t["count"])],
                               textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}: median %{x:.1f} days<extra></extra>"))
        fig.update_layout(height=230, margin=dict(l=0, r=120, t=10, b=0), xaxis_title="median days to SAP",
                          yaxis_title="")
        c.chart(fig)
    with right:
        st.markdown("##### Approval bottlenecks")
        a = steps[steps.step.str.contains("approval")]
        b = a.groupby("actor_role").agg(approvals=("request_id", "count"), median=("wait_days", "median"),
                                        late=("wait_days", lambda w: (w > ESCALATE_DAYS).mean()),
                                        total=("wait_days", "sum")).sort_values("total")
        fig = go.Figure(go.Bar(x=b.total, y=b.index, orientation="h", marker_color=theme.WARN,
                               customdata=b[["approvals", "median", "late"]].values,
                               text=[f"{l:.0%} waited over {ESCALATE_DAYS} days" for l in b.late],
                               textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}<br>%{customdata[0]} approvals, median wait %{customdata[1]:.1f} "
                                             "days<br>%{x:,.0f} days waited in total<extra></extra>"))
        fig.update_layout(height=230, margin=dict(l=0, r=150, t=10, b=0), xaxis_title="total days waited",
                          yaxis_title="")
        c.chart(fig)
    reasons = req.bounce_reasons[req.bounce_reasons != ""].str.split(";").explode().str.strip().value_counts()
    top3 = ", ".join(f"{r.lower()} ({n})" for r, n in reasons.head(3).items())
    st.caption(f"Each approver takes about {a.wait_days.median():.0f} days to respond, so the delay comes from "
               f"approvals running one after another, not from one slow approver. The most common reasons a request "
               f"bounces back: {top3}. The smart form makes these fields required.")


def quality():
    q = c.data_quality()
    cl, pairs, s = q["clusters"], q["pairs"], q["score"]
    dups = cl[cl.cluster_size > 1]
    is_dup = cl.record_id != cl.golden_id
    _cycle_time()
    st.markdown("##### Duplicates caught")
    c.kpi_row([
        c.kpi("Customer records", len(cl)),
        c.kpi("Duplicate records found", int(is_dup.sum()), delta=f"{is_dup.mean():.0%} of records", tone="bad"),
        c.kpi("Sent to human review", int((pairs.decision == "review").sum())),
        c.kpi("Duplicate item codes", len(q["item_map"])),
    ])
    st.caption(f"Checked against the synthetic answer key: precision {s['precision']:.0%}, recall {s['recall']:.0%} "
               f"({s['found_pairs']} of {s['true_pairs']} duplicate pairs). Real SAP data will be messier, which "
               f"is why borderline matches go to human review.")
    live = c.live_check()
    st.markdown("##### Two checks: one at the door, one for the backlog")
    st.markdown(
        f"- **The request form (stops new duplicates).** When a requestor types a customer, the form compares the "
        f"name with that country's records, allowing for typos, and blocks a matching registration no. or a known "
        f"short name. Tested on the {live['duplicates']} planted duplicates as if each were typed in as a new "
        f"request: **{live['caught_name_only']} of {live['duplicates']} flagged from the name alone**, "
        f"{live['caught_with_reg']} of {live['duplicates']} when the registration no. is also entered. Of "
        f"{live['originals']} genuinely new customers, {live['false_warnings']} "
        f"({live['false_warnings'] / live['originals']:.0%}) get a warning, which only asks the requestor for a "
        f"reason before submitting.\n"
        f"- **This page (cleans up the duplicates already in SAP).** The bulk matcher above compares every pair of "
        f"records across SPD, QTS and QTG. MDM confirms the groups below and downloads an SAP import file that "
        f"freezes the extra records.")
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
    _cleanup(dups, pairs, q["item_map"])
    st.markdown("##### Why it matters")
    st.markdown("Merging duplicates doesn't change country totals, because each order is still counted once. It "
                "changes the per-customer figures: how many customers there are, who appears to have stopped "
                "ordering (because their orders moved to a new record), and who appears to buy only Product A "
                "(because their B orders sit on another entity's record). Customers shows the before-and-after "
                "difference.")


def _dtw(obj_cols, rows):
    """A Data Transfer Workbench file: tab-separated, object property names then database column names, then data."""
    lines = ["\t".join(c[0] for c in obj_cols), "\t".join(c[1] for c in obj_cols)]
    lines += ["\t".join(str(v) for v in r) for r in rows]
    return "\r\n".join(lines) + "\r\n"


def _cleanup(dups, pairs, item_map):
    """MDM confirms duplicate groups and downloads SAP import files that freeze the extra records.
    Freezing (not deleting) keeps their order history in SAP while stopping anyone from using them again."""
    st.markdown("##### Clean up the duplicates already in SAP")
    st.caption("Untick a record if it isn't really a duplicate. Borderline pairs from the review queue start unticked: "
               "tick them once checked. The download freezes each ticked record in SAP B1 with a note saying which "
               "code to use instead; it doesn't delete anything, so past orders stay where they are.")
    extra = dups[dups.record_id != dups.golden_id]
    rows = pd.DataFrame({"freeze": True, "record_id": extra.record_id, "customer_name": extra.customer_name,
                         "keep": extra.golden_id, "keep_name": extra.golden_name, "why": "Matched automatically"})
    review = pairs[pairs.decision == "review"]
    if len(review):
        rows = pd.concat([rows, pd.DataFrame({
            "freeze": False, "record_id": review.record_b, "customer_name": review.name_b, "keep": review.record_a,
            "keep_name": review.name_a, "why": "Review: " + review.reason})], ignore_index=True)
    picked = st.data_editor(rows, hide_index=True, width="stretch", key="cleanup", disabled=[
        "record_id", "customer_name", "keep", "keep_name", "why"], column_config={
        "freeze": st.column_config.CheckboxColumn("Freeze"),
        "record_id": st.column_config.TextColumn("Duplicate record"),
        "customer_name": st.column_config.TextColumn("Name on it"),
        "keep": st.column_config.TextColumn("Use instead"),
        "keep_name": st.column_config.TextColumn("Kept record's name"),
        "why": st.column_config.TextColumn("Why")})
    chosen = picked[picked.freeze]
    note = lambda keep: f"Duplicate - use {keep}"  # SAP's frozen remarks field is short (30 characters)
    bp = _dtw([("RecordKey", "RecordKey"), ("CardCode", "CardCode"), ("Frozen", "frozenFor"),
               ("FrozenRemarks", "FrozenComm")],
              [(i + 1, r.record_id, "tYES", note(r.keep)) for i, r in enumerate(chosen.itertuples())])
    items = _dtw([("RecordKey", "RecordKey"), ("ItemCode", "ItemCode"), ("Frozen", "frozenFor"),
                  ("FrozenRemarks", "FrozenComm")],
                 [(i + 1, dup, "tYES", note(keep)) for i, (dup, keep) in enumerate(item_map.items())])
    remap = chosen[["record_id", "keep"]].rename(columns={"record_id": "old_code", "keep": "use_code"})
    a, b, d = st.columns(3)
    a.download_button(f"Business partners to freeze ({len(chosen)})", bp, "Cleanup_BusinessPartners_DTW.txt",
                      "text/plain", disabled=chosen.empty, width="stretch")
    b.download_button(f"Items to freeze ({len(item_map)})", items, "Cleanup_Items_DTW.txt", "text/plain",
                      disabled=not item_map, width="stretch")
    d.download_button("Old code to new code list (CSV)", remap.to_csv(index=False), "Cleanup_code_map.csv",
                      "text/csv", disabled=chosen.empty, width="stretch",
                      help="For finance and reporting: which code each frozen record's history belongs to")


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
            ("Escalate after (days)", 2, 6, 4, 1, "Calendar days before a stalled approval is escalated"),
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
        c.kpi("Median time to SAP", fut_med, decimals=1, suffix=" days",
              delta=f"{fut_med - now_med:+.1f} days vs email today", tone=c.tone(fut_med - now_med, up_is_good=False)),
        c.kpi("Slowest 10%", sim.future_days.quantile(.9), decimals=1, suffix=" days",
              delta=f"{slow_chg:+.1f} days vs email today", tone=c.tone(slow_chg, up_is_good=False)),
        c.kpi("Faster", (1 - fut_med / now_med) * 100, suffix="%"),
    ])
    long = pd.concat([sim.assign(scenario="Today (email)", days=sim.cycle_days),
                      sim.assign(scenario="OneRecord", days=sim.future_days)])
    fig = px.histogram(long, x="days", color="scenario", barmode="overlay", nbins=40, opacity=0.7,
                       color_discrete_map=SCENARIO_COLORS)
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), legend_title="")
    c.chart(fig)
    # Floor: the same design if Teams notifications and reminders changed nothing at all
    floor = process.simulate(d["requests"], d["steps"], bounce_avoided=bounce / 100, notice_cut=0,
                             escalate_after_days=esc)
    st.caption(f"Even if notifications and reminders changed nothing (approvers take exactly as long as today), "
               f"parallel approvals and the smart form alone give a median of **{floor.future_days.median():.1f} days** "
               f"(slowest 10%: {floor.future_days.quantile(.9):.1f}). That is the floor of the range; "
               f"{fut_med:.1f} days is with the settings above.")
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
            c.kpi("Median time to SAP", fut_med, decimals=1, suffix=" days",
                  delta=f"{fut_med - now_med:+.1f} days vs email today",
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
     "Power Platform contractor ({dev} weeks); MDM team sets up rules and runs the pilot; IT, one-off: the Teams "
     "site and permissions (about 2 days)",
     "Median time to SAP of 5 days or less in the pilot; at least 90% of requests through the form"),
    ("Phase 2: Use the clean data", "Months 3–6",
     ["Regional view in Power BI inside Teams",
      "Monthly forecast and stock plan replace the 6-month average spreadsheet",
      "Drop-off and cross-sell lists to account managers each month",
      "Email sorting: rules, then an AI prompt, then a person",
      "Monthly AI action brief posted to the sales channel"],
     "Data analyst ({da} weeks) builds the Power BI report, then each month runs one script that refreshes the "
     "forecast and customer lists and saves them to SharePoint, where Power BI reads them (no server to run); IT, "
     "one-off: switch on AI Builder; Sales ops owns the monthly review",
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
        st.caption("Sized for a small team: one contractor and one analyst, with the MDM team owning the rules. No IT "
                   "development team is needed: IT's part is one-off setup, and everything after that is run by the "
                   "MDM team and the analyst. Each phase starts only when the previous one hits its targets. The "
                   "year-1 cost above covers Phases 1 and 2; Phase 3 is priced with an SAP partner once Phase 1–2 "
                   "results are in.")
        c.assumption("the timings, team sizes and targets below are our estimates, to confirm with Lives Group.")
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
