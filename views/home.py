"""Overview: the strategic page. Answers first (KPIs, where growth is, what to do), evidence one click away."""
import re
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from onerecord import overview as ov
from onerecord.config import COUNTRIES, CURRENT, GROWTH_LABEL, PRIOR_YEAR

from . import common as c
from . import theme

ALL = "All countries"
FIGURE = re.compile(r"(S\$[\d,]+|[+-]?\d+%)")  # money and percentages, bolded in the action text
SHORT = {"A": "A · Reagents", "B": "B · Consumables", "C": "C · Equipment"}
GROWTH_HELP = (f"Growth = % change in purchase-order units, {CURRENT[0]} to {CURRENT[1]} {GROWTH_LABEL} "
               f"({PRIOR_YEAR[0]} to {PRIOR_YEAR[1]}). Customer orders only: enquiries, follow-ups and setup "
               "requests are not counted.")


def render():
    reg, f, q = c.regional(), c.forecasts(), c.data_quality()
    clean = reg["clean"]
    months = sorted(clean.month.unique())

    top, period, place = st.columns([3.2, 1.3, 1], vertical_alignment="bottom")
    with top:
        c.header("Overview", "Lives Group · five-country regional view")
    n = period.select_slider("Period", options=list(range(6, 13)), value=12, key="ov_window",
                             format_func=lambda k: f"Last {k} months",
                             help="Sets the window for volume and the trend chart. Growth always compares the "
                                  "same six months year on year.")
    pick = c.select(place, "Country", [ALL, *COUNTRIES], key="ov_country",
                           format_func=lambda k: k if k == ALL else f"{k} · {COUNTRIES[k]}")
    country = None if pick == ALL else pick
    window = ov.last_months(months, n)

    _kpis(clean, reg["growth"], f, window, country)

    left, right = st.columns([1.05, 1], gap="medium")
    with left, st.container(key="card-heat"):
        _heatmap(reg["growth"], country)
    with right, st.container(key="card-actions"):
        _actions(reg["compare"]["clean_drop"], reg["compare"]["clean_xsell"], f["plan"], country)

    with st.container(key="card-trend"):
        _trend(clean, f, window, country)

    t = ov.trust(clean, window, c.triage()["main"], q["clusters"], q["item_map"], country)
    _trust_strip(t, window)


def _kpis(clean, g, f, window, country):
    vol = ov.volume(clean, window, country)
    growth, mom = ov.growth(g, country), ov.momentum(clean, country)
    nq = ov.next_quarter(f["ahead"], clean, country)
    acc = ov.accuracy(f["backtest"], country)
    # Magic UI "Number Ticker" tiles: each number counts up on load, and from its old value when a filter changes
    c.kpi_row([
        c.kpi(f"PO volume, last {len(window)} months", vol["units"], suffix=" units", key="ov-volume",
              delta=f"{vol['pos']:,} purchase orders",
              help=f"{window[0]} to {window[-1]}. Customer purchase orders only."),
        c.kpi("Growth, Apr–Sep 2026", growth * 100, prefix="+" if growth >= 0 else "", suffix="%", decimals=1,
              key="ov-growth",
              delta=f"{mom:+.0%} in the last 3 months", tone=c.tone(mom),
              help=GROWTH_HELP + " The change underneath is the last 3 months on the same months a year earlier."),
        c.kpi("Forecast, Oct–Dec 2026", nq["units"], suffix=" units", key="ov-forecast",
              delta=f"{nq['change']:+.0%} on Oct–Dec 2025" if nq["change"] is not None else None,
              tone=c.tone(nq["change"]),
              help="AI calendar model: each country and product's trend plus dengue season, the hospital "
                   "year-end budget spend, the January lull and public holidays."),
        c.kpi("Forecast error, AI model", acc["model"] * 100, suffix="%", decimals=1, key="ov-error",
              delta=f"{acc['change']:+.0%} vs 6-month average ({acc['baseline']:.1%})",
              tone=c.tone(acc["change"], up_is_good=False),
              help="Average miss as a share of actual units (WAPE), forecasting 1–3 months ahead from each "
                   "month Apr–Sep 2026, Products A and B. Lower is better."),
    ], height=104)


def _heatmap(g, country):
    st.markdown("##### Where we are growing")
    m = g.pivot(index="country", columns="product", values="unit_growth").reindex(c.COUNTRY_ORDER)
    units = g.pivot(index="country", columns="product", values="units_now").reindex(c.COUNTRY_ORDER)
    fig = go.Figure(go.Heatmap(
        z=m.values, x=[SHORT[p] for p in m.columns], y=[COUNTRIES[k] for k in m.index],
        colorscale=theme.GROWTH_SCALE, zmin=-0.3, zmax=0.3, showscale=False, xgap=3, ygap=3,
        text=[[f"{v:+.0%}" for v in row] for row in m.values], texttemplate="%{text}",
        textfont=dict(size=15, color=theme.NAVY), customdata=units.values,
        hovertemplate="%{y}, %{x}<br>%{text} year on year<br>%{customdata:,} units Apr–Sep 2026<extra></extra>"))
    if country:
        row = c.COUNTRY_ORDER.index(country)
        fig.add_shape(type="rect", x0=-0.5, x1=2.5, y0=row - 0.5, y1=row + 0.5, line=dict(color=theme.NAVY, width=2.5))
    fig.update_layout(height=218, margin=dict(l=0, r=0, t=4, b=0), yaxis=dict(autorange="reversed", showgrid=False),
                      xaxis=dict(side="top", showgrid=False, ticks=""))
    c.chart(fig)
    st.caption(f"Units {GROWTH_LABEL}. Equipment (C) volumes are small: read as directional.", help=GROWTH_HELP)


def _actions(drops, xsell, plan, country):
    actions = ov.top_actions(drops, xsell, plan, country)
    st.markdown(f"##### Top {len(actions)} actions this quarter" if actions else "##### No urgent actions")
    for i, a in enumerate(actions, 1):
        # one container per action, so its evidence link sits with it (styled in app.css: st-key-act-*)
        with st.container(key=f"act-{i}"):
            # top line: number and tag on the left, the evidence link on the right
            tag, link = st.columns([1, 0.5], vertical_alignment="center")
            tag.html(f'<div class="or-action"><span class="or-num">{i}</span>'
                     f'<span class="or-tag {a["tone"]}">{escape(a["tag"])}</span></div>')
            page = c.PAGES.get(a["page"])
            if page is not None:
                link.page_link(page, label="See the evidence", icon=":material/arrow_forward:")
            why = FIGURE.sub(r"<b>\1</b>", escape(a["why"]))
            st.html(f'<div class="or-body"><div class="or-what">{escape(a["what"])}</div>'
                    f'<div class="or-why">{why}</div></div>')


def _trend(clean, f, window, country):
    st.markdown("##### Forecast vs actual · AI model against today's 6-month average")
    d = clean if country is None else clean[clean.country == country]
    actual = d[d.month.isin(window)].groupby("month").quantity.sum()
    bt = f["backtest"]
    bt = bt[(bt.horizon == 1) & ((bt.country == country) if country else True)]
    test = bt.groupby("month")[["calendar_model", "baseline_ma6"]].sum()
    ahead = f["ahead"] if country is None else f["ahead"][f["ahead"].country == country]
    nxt = ahead.groupby("month")[["calendar_model", "baseline_ma6", "low", "high"]].sum()

    fig = go.Figure()
    fig.add_scatter(x=nxt.index, y=nxt.high, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=nxt.index, y=nxt.low, mode="lines", line=dict(width=0), fill="tonexty",
                    fillcolor=theme.FORECAST_BAND, name="Likely range", hoverinfo="skip")
    fig.add_scatter(x=actual.index, y=actual.values, name="Actual orders", mode="lines+markers",
                    line=dict(color=theme.NAVY, width=2.5), marker=dict(size=7),
                    hovertemplate="%{y:,.0f} units<extra>Actual</extra>")
    base = _join(test.baseline_ma6, nxt.baseline_ma6)
    fig.add_scatter(x=base.index, y=base.values, name="6-month average (today)", mode="lines",
                    line=dict(color=theme.BASELINE, width=2, dash="dot"),
                    hovertemplate="%{y:,.0f} units<extra>6-month average</extra>")
    model = _join(test.calendar_model, nxt.calendar_model)
    fig.add_scatter(x=model.index, y=model.values, name="AI model", mode="lines+markers",
                    line=dict(color=theme.FORECAST, width=2.5, dash="dash"), marker=dict(size=7),
                    hovertemplate="%{y:,.0f} units<extra>AI model</extra>")
    fig.add_vline(x=nxt.index[0], line=dict(color=theme.MUTED, width=1, dash="dot"))
    fig.add_annotation(x=nxt.index[0], y=1, yref="paper", text="Forecast", showarrow=False, xanchor="left",
                       font=dict(size=11, color=theme.TEXT))
    fig.update_layout(height=215, margin=dict(l=0, r=0, t=6, b=0), hovermode="x unified",
                      yaxis=dict(title=None, tickformat=",.0f"), xaxis_title=None, legend=dict(y=1.06))
    c.chart(fig)
    if country and ov.accuracy(f["backtest"], country)["change"] > 0:
        st.caption(f"The AI model does worse than the 6-month average in {COUNTRIES[country]}: the drop comes from "
                   "customers ordering less, not from the calendar. Act on the customer list, not the forecast.")


def _join(*parts):
    """Back-test months followed by forecast months, as one series."""
    return pd.concat(parts).groupby(level=0).sum().sort_index()


def _trust_strip(t, window):
    mail = f"{t['mailbox'][0]} to {t['mailbox'][1]}" if t["mailbox"] else "no emails"
    st.html(
        '<div class="or-strip"><span class="or-title">What the numbers count</span>'
        f'<span><span class="or-dot" style="background:{theme.GOOD}"></span><b>{t["pos"]:,}</b> purchase orders counted '
        f'({window[0]} to {window[-1]})</span>'
        f'<span><span class="or-dot" style="background:{theme.WARN}"></span><b>{t["enquiries"]}</b> enquiries and '
        f'follow-ups left out</span>'
        f'<span><span class="or-dot" style="background:{theme.WARN}"></span><b>{t["setups"]}</b> setup requests sent '
        f'to MDM, not counted</span>'
        f'<span><span class="or-dot" style="background:{theme.PRIMARY}"></span><b>{t["duplicates"]}</b> duplicate '
        f'customer records and <b>{t["items"]}</b> duplicate item{"s" if t["items"] != 1 else ""} merged</span>'
        f'<span style="color:{theme.MUTED}">Emails: shared-mailbox sample, {mail}; {t["review"]} sent to a person '
        f'to check</span></div>')
