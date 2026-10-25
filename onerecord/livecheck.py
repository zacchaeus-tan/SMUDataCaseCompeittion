"""
The request form's live duplicate check, mirrored in Python (powerapps/gen_form.py holds the Power Fx).

Used for three things: filling the MatchKey / IDKey columns of the SharePoint master lists
(sharepoint/match_keys.py), measuring how many planted duplicates the form itself catches (the MDM ops page),
and keeping the two in step. Change both together.

  match_key  name, lower case, punctuation and legal words (Pte, Ltd, Sdn Bhd ...) removed, common abbreviations
             expanded (Hosp -> hospital), then letters and digits only: "National Univ. Hospital (S) Pte Ltd"
             -> "nationaluniversityhospitals"
  id_key     registration no. / tax ID / part no. in capitals, letters and digits only: "07.887.118.2-554.000"
             -> "078871182554000"
  similarity share of letter pairs two match keys have in common (Dice coefficient on distinct pairs)
"""
import re

LEGAL = {"pte", "ltd", "sdn", "bhd", "co", "jsc", "pt", "inc", "gmbh", "ag", "sa", "the"}
EXPAND = {"hosp": "hospital", "ctr": "centre", "center": "centre", "univ": "university", "med": "medical",
          "lab": "laboratory", "spec": "specialist", "diag": "diagnostic", "gen": "general", "comm": "community"}
PUNCT = [".", ",", "(", ")", "-", "/", "'", '"', "&", ":", ";", "#", "+"]
THRESHOLD = 0.82  # same name similarity from here up -> "Possible match" (tuned on the synthetic answer key)


def match_key(name: str) -> str:
    s = (name or "").lower()
    for ch in PUNCT:
        s = s.replace(ch, " ")
    words = [EXPAND.get(w, w) for w in s.split() if w not in LEGAL]
    return re.sub(r"[^a-z0-9]", "", "".join(words))


def id_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def pairs(key: str) -> set:
    return {key[i:i + 2] for i in range(len(key) - 1)}


def similarity(a: str, b: str) -> float:
    pa, pb = pairs(a), pairs(b)
    if not pa or not pb:
        return 0.0
    return 2 * len(pa & pb) / (len(pa) + len(pb))


def check_customer(name, country, reg_no, master, aliases=()):
    """What the form says for a new customer request: ("Blocked" | "Possible match" | "Clear", record id, score).
    `master` rows need record_id, name, country, reg_no; `aliases` maps a known name (lower case) to a record id."""
    ik = id_key(reg_no)
    if ik:
        for r in master:
            if id_key(r["reg_no"]) == ik:
                return "Blocked", r["record_id"], 1.0
    basic = " ".join(w for w in re.sub(r"[.,()\-/'\"&:;#+]", " ", (name or "").lower()).split() if w not in LEGAL)
    expanded = " ".join(EXPAND.get(w, w) for w in basic.split())
    for known in (basic, expanded):
        if known in aliases:
            return "Blocked", aliases[known], 1.0
    mk = match_key(name)
    best = max(((similarity(mk, match_key(r["name"])), r["record_id"]) for r in master if r["country"] == country),
               default=(0.0, None))
    if best[0] >= THRESHOLD:
        return "Possible match", best[1], best[0]
    return "Clear", None, best[0]


def evaluate(customers, truth, aliases=()):
    """How the live check does on planted duplicates. For each duplicate record, pretend only the original exists
    and the requestor types the duplicate's name (with and without its registration no.). For each original,
    pretend the customer is new (none of its records exist) and count false warnings."""
    true_id = dict(zip(truth.record_id, truth.true_customer_id))
    kind = dict(zip(truth.record_id, truth.dup_type))
    rows = [dict(record_id=r.record_id, name=r.customer_name, country=r.country, reg_no=r.registration_no or "")
            for r in customers.fillna("").itertuples()]
    by_true = {}
    for r in rows:
        by_true.setdefault(true_id[r["record_id"]], []).append(r)
    caught = caught_reg = dups = false_warn = originals = 0
    missed = []
    for r in rows:
        group = by_true[true_id[r["record_id"]]]
        if kind[r["record_id"]] == "original":
            originals += 1
            others = [x for x in rows if x not in group]
            false_warn += check_customer(r["name"], r["country"], "", others, {})[0] != "Clear"
            continue
        dups += 1
        orig = [x for x in group if kind[x["record_id"]] == "original"]
        master = [x for x in rows if x not in group] + orig
        hit = check_customer(r["name"], r["country"], "", master, aliases)
        ok = hit[0] != "Clear" and true_id.get(hit[1]) == true_id[r["record_id"]]
        caught += ok
        if not ok:
            missed.append(r["name"])
        reg = orig[0]["reg_no"] if orig else ""
        hit = check_customer(r["name"], r["country"], reg, master, aliases)
        caught_reg += hit[0] != "Clear" and true_id.get(hit[1]) == true_id[r["record_id"]]
    return dict(duplicates=dups, caught_name_only=caught, caught_with_reg=caught_reg, missed=missed,
                originals=originals, false_warnings=false_warn)
