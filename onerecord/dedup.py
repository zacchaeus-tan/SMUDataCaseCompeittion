"""
Bulk duplicate detection across SPD / QTS / QTG customer records.

Deterministic fuzzy matching (no model to train or maintain):
  1. compare records only within the same country (blocking)
  2. registration number: same -> match, different -> never match
  3. otherwise name similarity on cleaned names, backed by city / address, plus acronym check (NUH)
Matches are grouped into clusters; each cluster gets one golden record id.
"""
from itertools import combinations

import pandas as pd
from rapidfuzz import fuzz

from .normalise import address_key, initials, name_key

AUTO_MERGE = 90     # name score at/above which records in the same city are merged
REVIEW = 80         # band [REVIEW, AUTO_MERGE) goes to the MDM analyst review queue


def score_pair(a, b):
    """Return (decision, score, reason) for two customer records."""
    if a.registration_no and b.registration_no:
        if a.registration_no == b.registration_no:
            return "match", 100, "Same registration no."
        return "no", 0, "Different registration no."
    na, nb = a.name_key, b.name_key
    name = max(fuzz.ratio(na, nb), fuzz.token_sort_ratio(na, nb))  # typo-safe and word-order-safe
    addr = fuzz.token_set_ratio(a.addr_key, b.addr_key)
    same_city = a.city == b.city
    short = min((na, nb), key=len)
    longer = nb if short == na else na
    if same_city and len(short) <= 5 and " " not in short and short == initials(longer):
        return "match", 95, f"Acronym '{short.upper()}'"
    if same_city and name >= AUTO_MERGE:
        return "match", name, f"Name {name:.0f}% similar, same city"
    if same_city and name >= REVIEW and addr >= 85:
        return "match", name, f"Name {name:.0f}% + address {addr:.0f}% similar"
    if same_city and name >= REVIEW:
        return "review", name, f"Name {name:.0f}% similar, same city"
    return "no", name, ""


def find_duplicates(customers: pd.DataFrame):
    """Returns (pairs, clusters): scored candidate pairs and record_id -> golden_id mapping."""
    df = customers.fillna("").copy()
    df["name_key"] = df.customer_name.map(name_key)
    df["addr_key"] = df.address.map(address_key)
    rows = []
    for _, grp in df.groupby("country"):
        for a, b in combinations(grp.itertuples(index=False), 2):
            decision, score, reason = score_pair(a, b)
            if decision != "no":
                rows.append(dict(record_a=a.record_id, name_a=a.customer_name, entity_a=a.created_by_entity,
                                 record_b=b.record_id, name_b=b.customer_name, entity_b=b.created_by_entity,
                                 country=a.country, decision=decision, score=round(score), reason=reason))
    pairs = pd.DataFrame(rows, columns=["record_a", "name_a", "entity_a", "record_b", "name_b", "entity_b",
                                        "country", "decision", "score", "reason"])

    parent = {r: r for r in df.record_id}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in pairs[pairs.decision == "match"].itertuples():
        parent[find(p.record_a)] = find(p.record_b)

    created = dict(zip(df.record_id, df.created_date))
    groups = {}
    for r in df.record_id:
        groups.setdefault(find(r), []).append(r)
    golden = {}
    for members in groups.values():
        g = min(members, key=lambda r: (created[r], r))  # oldest record survives
        for r in members:
            golden[r] = g
    clusters = df[["record_id", "customer_name", "country", "city", "created_by_entity", "created_date",
                   "registration_no"]].copy()
    clusters["golden_id"] = clusters.record_id.map(golden)
    clusters["cluster_size"] = clusters.groupby("golden_id").record_id.transform("count")
    names = dict(zip(df.record_id, df.customer_name))
    clusters["golden_name"] = clusters.golden_id.map(names)
    return pairs, clusters


def evaluate(clusters: pd.DataFrame, truth: pd.DataFrame):
    """Pairwise precision / recall against the answer key."""
    t = dict(zip(truth.record_id, truth.true_customer_id))
    g = dict(zip(clusters.record_id, clusters.golden_id))
    tp = fp = fn = 0
    by_country = clusters.groupby("country").record_id.apply(list)
    for recs in by_country:
        for a, b in combinations(recs, 2):
            pred, true = g[a] == g[b], t[a] == t[b]
            tp += pred and true
            fp += pred and not true
            fn += true and not pred
    return dict(precision=tp / (tp + fp) if tp + fp else 1.0, recall=tp / (tp + fn) if tp + fn else 1.0,
                true_pairs=tp + fn, found_pairs=tp, false_pairs=fp)
