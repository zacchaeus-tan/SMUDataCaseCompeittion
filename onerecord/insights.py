"""
Regional business view: growth, drop-off and cross-sell, computed on CLEAN data
(duplicate customers merged to golden records, duplicate item codes merged).

Country x product totals are not changed by duplicates -- every order is still counted once.
What duplicates distort is everything measured PER CUSTOMER: how many customers we have,
who is "dropping off", and who "only buys A". That is where the clean-up pays off.
"""
import re
from itertools import combinations

import pandas as pd
from rapidfuzz import fuzz

from .config import CURRENT, PRIOR_YEAR

RECENT = ("2026-07", "2026-09")          # drop-off window
RECENT_PRIOR = ("2025-07", "2025-09")    # same months a year earlier
BASELINE = ("2025-10", "2026-06")        # customer's own recent run-rate (3 quarters)
LOOKBACK_12M = ("2025-10", "2026-09")
DROP_THRESHOLD = 0.40                    # units down >= 40% vs last year AND vs own recent average
MIN_QUARTER_UNITS = 30                   # ignore very small, irregular buyers


def _between(df, rng):
    return df[(df.month >= rng[0]) & (df.month <= rng[1])]


def item_duplicates(items: pd.DataFrame, threshold=85):
    """Same product family + near-identical description -> the older code survives."""
    key = lambda s: re.sub(r"[^\w ]", " ", s.lower())
    out = {}
    for a, b in combinations(items.itertuples(index=False), 2):
        if a.product == b.product and fuzz.token_set_ratio(key(a.description), key(b.description)) >= threshold:
            keep, drop = sorted([a, b], key=lambda r: r.created_date)
            out[drop.item_code] = keep.item_code
    return out


def clean_orders(po: pd.DataFrame, clusters: pd.DataFrame, item_map: dict) -> pd.DataFrame:
    df = po.copy()
    golden = dict(zip(clusters.record_id, clusters.golden_id))
    names = dict(zip(clusters.golden_id, clusters.golden_name))
    df["customer_id"] = df.customer_record_id.map(golden)
    df["customer"] = df.customer_id.map(names)
    df["item_code"] = df.item_code.replace(item_map)
    return df


def growth_table(df: pd.DataFrame) -> pd.DataFrame:
    """Year-on-year growth by country x product (same 6 months, so seasonality cancels)."""
    cur, prev = _between(df, CURRENT), _between(df, PRIOR_YEAR)
    agg = lambda d, s: d.groupby(["country", "product"]).agg(**{f"units_{s}": ("quantity", "sum"),
                                                              f"value_{s}": ("line_value_sgd", "sum"),
                                                              f"customers_{s}": ("customer_id", "nunique")})
    t = agg(cur, "now").join(agg(prev, "prev")).fillna(0).reset_index()
    t["unit_growth"] = t.units_now / t.units_prev - 1
    t["value_growth"] = t.value_now / t.value_prev - 1
    m_now, m_prev = _between(df, RECENT), _between(df, RECENT_PRIOR)
    mom = (m_now.groupby(["country", "product"]).quantity.sum() /
           m_prev.groupby(["country", "product"]).quantity.sum() - 1).rename("momentum_3m")
    return t.merge(mom.reset_index(), on=["country", "product"], how="left")


def monthly(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["country", "product", "month"]).quantity.sum().reset_index()


def drop_offs(df: pd.DataFrame, id_col="customer_id", name_col="customer") -> pd.DataFrame:
    """Established customers whose last quarter fell >= 40% both vs the same quarter last year
    (so seasonality cancels) and vs their own average quarter since Oct 2025 (so one-off spikes don't count)."""
    q = lambda rng: _between(df, rng).groupby(id_col).quantity.sum()
    t = pd.DataFrame({"units_last_q": q(RECENT), "units_same_q_last_year": q(RECENT_PRIOR),
                      "avg_q_since_oct": q(BASELINE) / 3}).fillna(0)
    keep = ((t.units_same_q_last_year >= MIN_QUARTER_UNITS)
            & (t.units_last_q <= (1 - DROP_THRESHOLD) * t.units_same_q_last_year)
            & (t.units_last_q <= (1 - DROP_THRESHOLD) * t.avg_q_since_oct))
    t = t[keep].copy()
    t["change"] = t.units_last_q / t.units_same_q_last_year - 1
    info = df.drop_duplicates(id_col).set_index(id_col)[[name_col, "country"]]
    value = _between(df, RECENT_PRIOR).groupby(id_col).line_value_sgd.sum()
    t = t.join(info)
    t["value_at_risk_per_q"] = (value.reindex(t.index) * -t.change).round(0)
    t["last_order"] = df.groupby(id_col).po_date.max().reindex(t.index)
    t = t.sort_values("value_at_risk_per_q", ascending=False)
    return t.reset_index().rename(columns={id_col: "id", name_col: "name"})


def cross_sell(df: pd.DataFrame, customers: pd.DataFrame, id_col="customer_id", name_col="customer",
               min_peer_share=0.5) -> pd.DataFrame:
    """Customers buying A but not B (or B not A) while most similar customers buy both.
    Opportunity = their volume of the product they buy x the median ratio peers show."""
    d = _between(df, LOOKBACK_12M)
    seg = dict(zip(customers.record_id, customers.segment))
    piv = d.pivot_table(index=id_col, columns="product", values="quantity", aggfunc="sum", fill_value=0)
    for p in "ABC":
        if p not in piv:
            piv[p] = 0
    rec_for = d.drop_duplicates(id_col).set_index(id_col)
    piv["segment"] = rec_for.customer_record_id.map(seg).reindex(piv.index) if "customer_record_id" in rec_for else None
    piv["country"] = rec_for.country.reindex(piv.index)
    piv["name"] = rec_for[name_col].reindex(piv.index)
    price = d.groupby("product").apply(lambda g: g.line_value_sgd.sum() / g.quantity.sum(), include_groups=False)
    rows = []
    for have, miss in (("A", "B"), ("B", "A")):
        for segname, grp in piv.groupby("segment"):
            buyers = grp[grp[have] > 0]
            both = buyers[buyers[miss] > 0]
            if len(buyers) < 5 or len(both) / len(buyers) < min_peer_share:
                continue
            ratio = (both[miss] / both[have]).median()
            for cid, r in buyers[buyers[miss] == 0].iterrows():
                units = r[have] * ratio
                rows.append(dict(id=cid, name=r["name"], country=r.country, segment=segname, buys=have,
                                 missing=miss, peers_buying_both=f"{len(both)}/{len(buyers)}",
                                 est_units_per_year=round(units), est_value_sgd_per_year=round(units * price[miss])))
    return pd.DataFrame(rows).sort_values("est_value_sgd_per_year", ascending=False) if rows else pd.DataFrame()


def raw_vs_clean(df: pd.DataFrame, customers: pd.DataFrame) -> dict:
    """What the same analyses say on the raw SAP records vs on the cleaned golden records."""
    raw = df.copy()
    raw["rid"], raw["rname"] = raw.customer_record_id, raw.customer_name
    return dict(
        raw_customers=raw.rid.nunique(), clean_customers=df.customer_id.nunique(),
        raw_drop=drop_offs(raw, "rid", "rname"), clean_drop=drop_offs(df),
        raw_xsell=cross_sell(raw, customers, "rid", "rname"), clean_xsell=cross_sell(df, customers),
    )
