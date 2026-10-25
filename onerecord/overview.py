"""
Numbers and plain-language actions for the Overview page. No Streamlit here: the page only lays these out.

Everything is computed from clean purchase orders (duplicate customers and items merged). Enquiries, follow-ups
and master-data setup requests never reach this data; they are only counted, for the trust strip.
"""
import pandas as pd

from .config import COUNTRIES
from .forecast import add_months, wape

ACTION_PAGES = {"retention": "actions", "stock": "forecast", "cross_sell": "actions"}


def _in(df, country):
    return df if country is None else df[df.country == country]


def last_months(months, n):
    return sorted(months)[-n:]


def volume(clean: pd.DataFrame, months, country=None) -> dict:
    d = _in(clean, country)
    d = d[d.month.isin(months)]
    return dict(units=int(d.quantity.sum()), pos=d.po_number.nunique())


def growth(g: pd.DataFrame, country=None) -> float:
    """Headline growth on the configured basis (config.GROWTH_BASIS)."""
    d = _in(g, country)
    return d.units_now.sum() / d.units_prev.sum() - 1


def momentum(clean: pd.DataFrame, country=None) -> float:
    """Last 3 months vs the same 3 months a year earlier."""
    d = _in(clean, country)
    last = sorted(d.month.unique())[-3:]
    prior = [add_months(m, -12) for m in last]
    return d[d.month.isin(last)].quantity.sum() / d[d.month.isin(prior)].quantity.sum() - 1


def next_quarter(ahead: pd.DataFrame, clean: pd.DataFrame, country=None) -> dict:
    """Forecast units for the next 3 months vs the same months a year earlier."""
    a = _in(ahead[ahead.horizon <= 3], country)
    months = sorted(a.month.unique())
    year_ago = [add_months(m, -12) for m in months]
    d = _in(clean, country)
    before = d[d.month.isin(year_ago)].quantity.sum()
    units = a.calendar_model.sum()
    return dict(units=units, change=units / before - 1 if before else None, first=months[0], last=months[-1])


def accuracy(bt: pd.DataFrame, country=None) -> dict:
    """Forecast error (WAPE) of the AI model vs today's 6-month average, Products A and B (C is too lumpy)."""
    d = _in(bt[bt["product"] != "C"], country)
    model, base = wape(d, "calendar_model"), wape(d, "baseline_ma6")
    return dict(model=model, baseline=base, change=model / base - 1)


def top_actions(drops: pd.DataFrame, xsell: pd.DataFrame, plan: pd.DataFrame, country=None) -> list:
    """Up to three actions in plain language, one of each kind: keep customers, stock up, cross-sell."""
    out = []
    where = lambda cc: COUNTRIES[cc]

    d = _in(drops, country)
    if len(d):
        by = d.groupby("country").agg(n=("id", "count"), risk=("value_at_risk_per_q", "sum"))
        cc = by.risk.idxmax()
        top = d[d.country == cc].sort_values("value_at_risk_per_q", ascending=False).iloc[0]
        n = int(by.loc[cc, "n"])
        out.append(dict(kind="retention", tag="Keep customers", tone="bad",
                        what=f"Call the {n} {where(cc)} customer{'s' if n > 1 else ''} ordering much less",
                        why=f"S${by.loc[cc, 'risk']:,.0f} a quarter at risk. Biggest: {top['name']} "
                            f"({top.change:+.0%})."))

    p = _in(plan, country)
    p = p[p.action.str.startswith("Build")].assign(extra=lambda x: x.next_3_months - x.last_3_months)
    if len(p):
        r = p.sort_values("extra", ascending=False).iloc[0]
        out.append(dict(kind="stock", tag="Stock up", tone="warn",
                        what=f"Stock up Product {r['product']} in {where(r.country)} before October",
                        why=f"{r.next_3_months:,.0f} units forecast for Oct–Dec, {r.change:+.0%} on the last "
                            f"3 months ({r.drivers}). Cover up to {r.high:,.0f}."))

    x = _in(xsell, country)
    if len(x):
        by = x.groupby(["country", "missing", "buys"]).agg(n=("id", "count"), value=("est_value_sgd_per_year", "sum"))
        (cc, miss, buys), r = by.value.idxmax(), by.loc[by.value.idxmax()]
        out.append(dict(kind="cross_sell", tag="Cross-sell", tone="good",
                        what=f"Offer Product {miss} to {int(r.n)} {where(cc)} customers who only buy {buys}",
                        why=f"Similar customers buy both. S${r.value * 0.1:,.0f} a year if 10% convert "
                            f"(S${r.value:,.0f} if all do)."))

    for a in out:
        a["page"] = ACTION_PAGES[a["kind"]]
    return out


def trust(clean: pd.DataFrame, months, triage: pd.DataFrame, clusters: pd.DataFrame, item_map: dict,
          country=None) -> dict:
    """What was counted and what was kept out, for the trust strip."""
    t = _in(triage, country)
    cl = _in(clusters, country)
    return dict(
        pos=volume(clean, months, country)["pos"],
        enquiries=int(t.predicted.isin(["enquiry", "follow_up"]).sum()),
        setups=int((t.predicted == "mdm_request").sum()),
        review=int((t.predicted == "review").sum()),
        duplicates=int((cl.record_id != cl.golden_id).sum()),
        items=len(item_map),
        mailbox=(t.received_at.min()[:7], t.received_at.max()[:7]) if len(t) else None,
    )
