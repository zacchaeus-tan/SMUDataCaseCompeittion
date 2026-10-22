#!/usr/bin/env python3
"""
Synthetic data generator for the Lives Group MDM case (SMU DSA 2026).

Everything here is SYNTHETIC. Company, customer, vendor and people names are
fictional (except "National University Hospital", used because the brief cites it).

Standard library only. Deterministic: same SEED -> same files.

    python3 scripts/generate_data.py

Writes:
    data/                 the dataset (what the prototype / analysis uses)
    data/answer_key/      ground truth for planted patterns -- do NOT feed into models
    sharepoint/           CSV templates to create the Power Platform SharePoint lists
"""
import csv
import math
import random
import re
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 2026
rng = random.Random(SEED)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KEY = DATA / "answer_key"
SP = ROOT / "sharepoint"

START = date(2025, 4, 1)  # 18 months: Apr 2025 - Sep 2026
N_MONTHS = 18


# --------------------------------------------------------------------------- helpers
def month_start(i):
    y = START.year + (START.month - 1 + i) // 12
    m = (START.month - 1 + i) % 12 + 1
    return date(y, m, 1)


def ym(i):
    return month_start(i).strftime("%Y-%m")


def days_in_month(d):
    nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return (nxt - d).days


def lognormal(mean, sigma):
    return rng.lognormvariate(math.log(mean) - sigma ** 2 / 2, sigma)


def poisson(lam):
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, round(rng.gauss(lam, math.sqrt(lam))))
    l, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= l:
            return k
        k += 1


def fmt_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


def business_time(d):
    """A datetime on day d during office hours."""
    return datetime(d.year, d.month, d.day, rng.randint(8, 17), rng.choice([0, 15, 30, 45]))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())[:24]


# --------------------------------------------------------------------------- reference data
COUNTRIES = {
    "SG": dict(name="Singapore", n=40, suffix="Pte Ltd",
               cities=["Novena", "Tampines", "Jurong", "Bukit Timah", "Toa Payoh", "Woodlands", "Bedok",
                       "Outram", "Serangoon", "Clementi", "Yishun", "Pasir Ris"],
               streets=["Novena Rise", "Tampines Avenue 5", "Jurong West Street 41", "Bukit Timah Road",
                        "Lorong 6 Toa Payoh", "Woodlands Avenue 2", "Bedok North Road", "Outram Road"],
               people=["Wei Ling", "Rajesh Kumar", "Nur Aisyah", "Daniel Ong", "Mei Fang"]),
    "MY": dict(name="Malaysia", n=45, suffix="Sdn Bhd",
               cities=["Petaling Jaya", "Johor Bahru", "Penang", "Kuala Lumpur", "Ipoh", "Kuching",
                       "Kota Kinabalu", "Shah Alam", "Melaka", "Seremban"],
               streets=["Jalan Ampang", "Jalan Tun Razak", "Jalan Sultan Ismail", "Jalan Gasing",
                        "Persiaran Gurney", "Jalan Wong Ah Fook"],
               people=["Ahmad Faizal", "Siti Rahmah", "Kumaresan", "Li Ying", "Farah Nadia"]),
    "TH": dict(name="Thailand", n=40, suffix="Co., Ltd.",
               cities=["Bangkok", "Chiang Mai", "Phuket", "Khon Kaen", "Hat Yai", "Nonthaburi",
                       "Udon Thani", "Pattaya"],
               streets=["Sukhumvit Road", "Rama IV Road", "Phahonyothin Road", "Nimmanhaemin Road",
                        "Mittraphap Road", "Petchkasem Road"],
               people=["Somchai", "Nattaya", "Kittipong", "Pimchanok", "Anan"]),
    "ID": dict(name="Indonesia", n=45, suffix="PT",
               cities=["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Makassar", "Denpasar",
                       "Yogyakarta"],
               streets=["Jalan Jenderal Sudirman", "Jalan MH Thamrin", "Jalan Pemuda", "Jalan Diponegoro",
                        "Jalan Gatot Subroto", "Jalan Ahmad Yani"],
               people=["Budi Santoso", "Dewi Lestari", "Agus Wijaya", "Rina Kartika", "Putri Ayu"]),
    "VN": dict(name="Vietnam", n=35, suffix="Co., Ltd",
               cities=["Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong", "Can Tho", "Hue", "Nha Trang"],
               streets=["Le Loi Street", "Tran Hung Dao Street", "Nguyen Hue Boulevard", "Hai Ba Trung Street",
                        "Dien Bien Phu Street", "Ly Thuong Kiet Street"],
               people=["Nguyen Van An", "Tran Thi Mai", "Le Minh Tuan", "Pham Thu Ha", "Hoang Duc Anh"]),
}

DESCRIPTORS = ["Central", "General", "Specialist", "Family", "Community", "Women's & Children's", "Heart",
               "Eastern", "Riverside", "Sunrise", "Unity", "Harmony", "Pacific", "Lotus", "Golden",
               "Green Valley", "Medical", "Northpoint", "Lakeside", "St. Mary's", "Mercy", "Hope"]

SEGMENTS = {  # share of customers, monthly ordering probability for A/B, base monthly units by product
    "Hospital": dict(share=0.30, p_order=0.95, base={"A": 60, "B": 150, "C": 0.6}),
    "Laboratory": dict(share=0.30, p_order=0.85, base={"A": 40, "B": 100, "C": 0.3}),
    "Clinic": dict(share=0.40, p_order=0.55, base={"A": 8, "B": 25, "C": 0.05}),
}

PRODUCTS = {
    "A": dict(name="IVD reagents & rapid tests", entity="SPD"),
    "B": dict(name="Laboratory consumables", entity="QTS"),
    "C": dict(name="Medical & laboratory equipment", entity="QTG"),
}

# item_code, description, product, uom, unit_price_sgd, regulated, sku_weight
ITEMS = [
    ("A-1001", "Dengue NS1 Rapid Test Kit (25 tests)", "A", "Kit", 95, "Yes", 0.30),
    ("A-1002", "HbA1c Reagent Cartridge (10 tests)", "A", "Box", 120, "Yes", 0.20),
    ("A-1003", "Troponin I Rapid Test (20 tests)", "A", "Kit", 160, "Yes", 0.15),
    ("A-1004", "CRP Reagent Kit (100 tests)", "A", "Kit", 85, "Yes", 0.20),
    ("A-1005", "Malaria Ag Rapid Test (25 tests)", "A", "Kit", 70, "Yes", 0.15),
    ("B-2001", "Microcentrifuge Tubes 1.5 ml (500/pack)", "B", "Pack", 18, "No", 0.20),
    ("B-2002", "Filter Pipette Tips 200 ul (960/box)", "B", "Box", 42, "No", 0.25),
    ("B-2003", "Nitrile Examination Gloves M (100/box)", "B", "Box", 9, "Yes", 0.25),
    ("B-2004", "EDTA Blood Collection Tubes (100/pack)", "B", "Pack", 26, "Yes", 0.20),
    ("B-2005", "Specimen Containers 60 ml (100/pack)", "B", "Pack", 15, "No", 0.10),
    ("C-3001", "Benchtop Centrifuge 24-place", "C", "Unit", 4800, "Yes", 0.30),
    ("C-3002", "Point-of-Care Chemistry Analyser", "C", "Unit", 14500, "Yes", 0.20),
    ("C-3003", "Analyser Preventive Maintenance Kit", "C", "Kit", 950, "No", 0.35),
    ("C-3004", "Biosafety Cabinet HEPA Filter Set", "C", "Set", 1800, "No", 0.15),
]
# Duplicate item: same product as A-1001 created again under a new code by another team.
DUP_ITEM = ("A-1009", "Dengue NS1 Ag Rapid Test 25T", "A", "Kit", 95, "Yes")
DUP_ITEM_COUNTRIES, DUP_ITEM_FROM_MONTH = ("TH", "VN"), 8

# annual volume growth by country x product (stylised assumption)
GROWTH = {
    "SG": {"A": 0.04, "B": 0.02, "C": -0.10},
    "MY": {"A": 0.10, "B": 0.08, "C": 0.03},
    "TH": {"A": 0.06, "B": 0.12, "C": 0.02},
    "ID": {"A": 0.18, "B": 0.20, "C": 0.08},
    "VN": {"A": 0.28, "B": 0.22, "C": 0.15},
}
# public-holiday dips by country and year-month (Lunar New Year, Tet, Songkran, Hari Raya / Lebaran)
HOLIDAY = {
    "SG": {"2026-02": 0.90},
    "MY": {"2025-04": 0.90, "2026-02": 0.92, "2026-03": 0.88},
    "TH": {"2025-04": 0.85, "2026-04": 0.85},
    "ID": {"2025-04": 0.78, "2026-03": 0.80},
    "VN": {"2026-02": 0.70},
}
# dengue-season uplift for Product A (calendar months)
DENGUE = {"SG": ((6, 7, 8), 1.10), "MY": ((6, 7, 8, 9), 1.25), "TH": ((6, 7, 8, 9), 1.30),
          "ID": ((1, 2, 3, 4), 1.25), "VN": ((7, 8, 9, 10), 1.30)}
YEAR_END = {11: 1.05, 12: 1.15, 1: 0.95}  # hospital budget flush, January lull


def seasonal(cc, product, i):
    d = month_start(i)
    f = HOLIDAY[cc].get(ym(i), 1.0) * YEAR_END.get(d.month, 1.0)
    months, uplift = DENGUE[cc]
    if product == "A" and d.month in months:
        f *= uplift
    return f


# --------------------------------------------------------------------------- name / address variants
ABBREV = {"Hospital": "Hosp", "Centre": "Ctr", "Medical": "Med", "Laboratory": "Lab", "University": "Univ",
          "Specialist": "Spec", "Diagnostic": "Diag", "General": "Gen", "Community": "Comm",
          "Children's": "Childrens"}


def name_variant(name):
    """A plausible re-typed version of an existing name (what a requestor would enter)."""
    for _ in range(20):
        v = name
        for op in rng.sample(["abbrev", "punct", "typo", "case", "suffix", "center", "amp"], k=rng.choice([1, 2])):
            if op == "abbrev":
                keys = [k for k in ABBREV if k in v]
                if keys:
                    k = rng.choice(keys)
                    v = v.replace(k, ABBREV[k] + rng.choice([".", ""]), 1)
            elif op == "punct":
                v = (v.replace("Pte Ltd", "Pte. Ltd.").replace("Co., Ltd.", "Co Ltd").replace("Co., Ltd", "Co. Ltd")
                     .replace("Sdn Bhd", "Sdn. Bhd.").replace("St. ", "St "))
            elif op == "typo":
                words = [w for w in v.split() if len(w) > 5 and w.isalpha()]
                if words:
                    w = rng.choice(words)
                    j = rng.randrange(1, len(w) - 2)
                    v = v.replace(w, w[:j] + w[j + 1] + w[j] + w[j + 2:], 1)
            elif op == "case":
                v = v.upper()
            elif op == "suffix":
                for s in (" Pte Ltd", " Sdn Bhd", " Co., Ltd.", " Co., Ltd", "PT "):
                    if s in v:
                        v = v.replace(s, "", 1)
                        break
            elif op == "center":
                v = v.replace("Centre", "Center")
            elif op == "amp":
                v = v.replace("&", "and")
        v = re.sub(r"\s+", " ", v).strip()
        if v != name:
            return v
    return name + " (new)"


def address_variant(addr):
    v = (addr.replace("Road", "Rd").replace("Avenue", "Ave").replace("Street", "St")
         .replace("Jalan", "Jln").replace("Boulevard", "Blvd"))
    if v == addr:
        v = addr.replace(",", "", 1)
    return v


def reg_no(cc):
    if cc == "SG":
        return f"{rng.randint(1995, 2022)}{rng.randint(10000, 99999)}{rng.choice('KMNRWZ')}"
    if cc == "MY":
        return f"{rng.randint(1990, 2022)}01{rng.randint(10000000, 99999999)}"
    if cc == "TH":
        return f"0105{rng.randint(530000000, 569999999)}"
    if cc == "ID":
        return (f"{rng.randint(1, 99):02d}.{rng.randint(100, 999)}.{rng.randint(100, 999)}."
                f"{rng.randint(1, 9)}-{rng.randint(100, 999)}.000")
    return f"0{rng.randint(100000000, 999999999)}"


LEGAL = r"\b(pte|ltd|sdn|bhd|co|jsc|pt|inc|gmbh|ag|sa|the)\b"
EXPAND = {"hosp": "hospital", "ctr": "centre", "center": "centre", "univ": "university", "med": "medical",
          "lab": "laboratory", "spec": "specialist", "diag": "diagnostic", "gen": "general", "comm": "community",
          "and": "&"}


def normalise(name):
    """Name key used by the live duplicate search in Power Apps (documented in sharepoint/LISTS.md)."""
    s = name.lower().replace("&", " & ")
    s = re.sub(r"[^\w&' ]", " ", s)
    s = re.sub(LEGAL, " ", s)
    words = [EXPAND.get(w, w) for w in s.split()]
    return " ".join(words)


# --------------------------------------------------------------------------- 1. customers (true entities)
def facility_name(cc, segment, city):
    d = rng.choice(DESCRIPTORS)
    sfx = COUNTRIES[cc]["suffix"]
    if segment == "Hospital":
        base = f"Rumah Sakit {d} {city}" if cc == "ID" else f"{city} {d} Hospital"
        return base.replace("Medical Hospital", "Medical Centre")
    if segment == "Laboratory":
        base = rng.choice([f"{city} {d} Diagnostic Laboratory", f"{d} Pathology Laboratory {city}",
                           f"{d} Clinical Laboratory"])
    else:
        base = rng.choice([f"{d} Medical Clinic {city}", f"{city} {d} Polyclinic", f"{d} Family Clinic {city}"])
    base = base.replace("Medical Medical", "Medical")
    return f"PT {base}" if cc == "ID" else f"{base} {sfx}"


def pick_products(segment):
    prods = []
    a = rng.random() < 0.85
    if a:
        prods.append("A")
    if rng.random() < (0.60 if a else 0.55):
        prods.append("B")
    if rng.random() < {"Hospital": 0.50, "Laboratory": 0.35, "Clinic": 0.08}[segment]:
        prods.append("C")
    return prods or ["B"]


true_customers = []
used_names = set()
tid = 0
for cc, cfg in COUNTRIES.items():
    seg_list = []
    for seg, s in SEGMENTS.items():
        seg_list += [seg] * round(cfg["n"] * s["share"])
    seg_list = (seg_list + ["Clinic"] * cfg["n"])[:cfg["n"]]
    for seg in seg_list:
        city = rng.choice(cfg["cities"])
        name = facility_name(cc, seg, city)
        while name in used_names:
            name = facility_name(cc, seg, rng.choice(cfg["cities"]))
        used_names.add(name)
        tid += 1
        true_customers.append(dict(
            true_id=f"T{tid:03d}", country=cc, segment=seg, city=city, name=name,
            address=f"{rng.randint(1, 450)} {rng.choice(cfg['streets'])}, {city}",
            reg_no=reg_no(cc), products=pick_products(seg), size=lognormal(1.0, 0.45),
            start_month=0, churn=None, dup_migration=None, dup_split=None,
        ))

# The brief's own example, forced in as a Singapore hospital with three records.
nuh = next(c for c in true_customers if c["country"] == "SG" and c["segment"] == "Hospital")
nuh.update(name="National University Hospital", city="Kent Ridge", address="5 Lower Kent Ridge Road, Kent Ridge",
           products=["A", "B", "C"], size=2.2)

established = [c for c in true_customers if c is not nuh]
rng.shuffle(established)
n = len(established)
new_customers = established[: round(n * 0.08)]
churners = established[round(n * 0.08): round(n * 0.17)]
others = established[round(n * 0.17):]

for c in new_customers:
    c["start_month"] = rng.randint(3, 11)
for c in churners:
    c["churn"] = dict(start=rng.randint(9, 13), end_level=rng.choice([0.0, 0.1, 0.2, 0.3, 0.4]))
for c in others:
    r = rng.random()
    if r < 0.15:
        c["dup_migration"] = rng.randint(6, 14)
    elif r < 0.30 and len(c["products"]) >= 2:
        c["dup_split"] = rng.choice(c["products"][1:])
nuh["dup_migration"], nuh["dup_split"] = 9, "B"


# --------------------------------------------------------------------------- 2. customer master records (as SAP holds them)
records = []
rec_seq = 10000


def new_record(c, name, address, reg, entity, created):
    global rec_seq
    rec_seq += rng.randint(1, 9)
    cc = c["country"]
    r = dict(record_id=f"C{rec_seq}", customer_name=name, country=cc, city=c["city"], address=address,
             registration_no=reg, segment=c["segment"], created_by_entity=entity,
             created_date=created.isoformat(),
             contact_email=f"procurement@{slug(c['name'])}.example",
             payment_terms=rng.choice(["30 days", "45 days", "60 days", "90 days"]),
             credit_limit_sgd=rng.choice([20000, 50000, 100000, 250000, 500000]) if c["segment"] != "Clinic"
             else rng.choice([5000, 10000, 20000]),
             status="Active", true_id=c["true_id"])
    records.append(r)
    return r


for c in true_customers:
    primary_entity = PRODUCTS[c["products"][0]]["entity"]
    if c["start_month"]:
        created = month_start(c["start_month"]) - timedelta(days=rng.randint(3, 12))
    else:
        created = date(rng.randint(2014, 2024), rng.randint(1, 12), rng.randint(1, 28))
    c["primary"] = new_record(c, c["name"], c["address"], c["reg_no"], primary_entity, created)
    c["primary"]["dup_type"] = "original"
    if c["dup_split"]:
        ent = PRODUCTS[c["dup_split"]]["entity"]
        nm = "National Univ. Hospital (S) Pte Ltd" if c is nuh else name_variant(c["name"])
        r = new_record(c, nm, address_variant(c["address"]), c["reg_no"] if rng.random() < 0.5 else "", ent,
                       date(rng.randint(2018, 2024), rng.randint(1, 12), rng.randint(1, 28)))
        r["dup_type"] = f"entity_split (orders for Product {c['dup_split']} booked here)"
        c["split_rec"] = r
    if c["dup_migration"]:
        nm = "NUH" if c is nuh else name_variant(c["name"])
        r = new_record(c, nm, address_variant(c["address"]) if rng.random() < 0.6 else c["address"],
                       c["reg_no"] if rng.random() < 0.55 else "", primary_entity,
                       month_start(c["dup_migration"]) - timedelta(days=rng.randint(2, 10)))
        r["dup_type"] = f"migration (all new orders from {ym(c['dup_migration'])} booked here)"
        c["mig_rec"] = r

rng.shuffle(records)


def record_for(c, product, i):
    if c.get("split_rec") and product == c["dup_split"]:
        return c["split_rec"]
    if c.get("mig_rec") and i >= c["dup_migration"]:
        return c["mig_rec"]
    return c["primary"]


# --------------------------------------------------------------------------- 3. items
items = [dict(item_code=i[0], description=i[1], product=i[2], product_name=PRODUCTS[i[2]]["name"],
              owning_entity=PRODUCTS[i[2]]["entity"], uom=i[3], list_price_sgd=i[4], regulated=i[5],
              created_date=date(rng.randint(2015, 2022), rng.randint(1, 12), 1).isoformat())
         for i in ITEMS]
items.append(dict(item_code=DUP_ITEM[0], description=DUP_ITEM[1], product=DUP_ITEM[2],
                  product_name=PRODUCTS["A"]["name"], owning_entity="QTS", uom=DUP_ITEM[3],
                  list_price_sgd=DUP_ITEM[4], regulated=DUP_ITEM[5],
                  created_date=(month_start(DUP_ITEM_FROM_MONTH) - timedelta(days=9)).isoformat()))
SKUS = {p: [i for i in ITEMS if i[2] == p] for p in PRODUCTS}
PRICE_ADJ = {"SG": 1.00, "MY": 0.96, "TH": 0.95, "ID": 0.97, "VN": 0.94}


# --------------------------------------------------------------------------- 4. purchase orders
po_lines = []
po_counter = 0
PO_FORMATS = ["PO-{n}", "{n}", "P{yy}/{n}", "HPO-{n}", "PR{yy}{n}"]


def volume_factor(c, i):
    if i < c["start_month"]:
        return 0.0
    if c["churn"] and i >= c["churn"]["start"]:
        s, e = c["churn"]["start"], c["churn"]["end_level"]
        return 1 - (1 - e) * min(1.0, (i - s + 1) / (N_MONTHS - s))
    return 1.0


for c in true_customers:
    cc, seg = c["country"], c["segment"]
    fmt = rng.choice(PO_FORMATS)
    discount = rng.uniform(0.0, 0.10)
    for i in range(N_MONTHS):
        vf = volume_factor(c, i)
        if vf == 0:
            continue
        for p in c["products"]:
            lam = (SEGMENTS[seg]["base"][p] * c["size"] * (1 + GROWTH[cc][p]) ** (i / 12)
                   * seasonal(cc, p, i) * vf * lognormal(1.0, 0.20))
            if p == "C":
                units = poisson(lam)
            else:
                po_ = SEGMENTS[seg]["p_order"]
                units = poisson(lam / po_) if rng.random() < po_ else 0
            if units <= 0:
                continue
            n_pos = 2 if (seg == "Hospital" and units > 40 and rng.random() < 0.3) else 1
            per_po = [units // n_pos + (k < units % n_pos) for k in range(n_pos)]
            rec = record_for(c, p, i)
            d0 = month_start(i)
            for q in per_po:
                if q <= 0:
                    continue
                po_counter += 1
                po_date = d0 + timedelta(days=rng.randrange(days_in_month(d0)))
                po_no = fmt.format(n=f"{po_counter + 40000}", yy=f"{po_date.year % 100}")
                skus = rng.choices(SKUS[p], weights=[s[6] for s in SKUS[p]], k=min(len(SKUS[p]), rng.randint(1, 3)))
                skus = list(dict.fromkeys(skus))
                split = [1] * len(skus)
                for _ in range(q - len(skus)):
                    split[rng.choices(range(len(skus)), weights=[s[6] for s in skus])[0]] += 1
                channel = rng.choices(["email", "sales_rep", "portal"], weights=[0.7, 0.2, 0.1])[0]
                for ln, (sku, qty) in enumerate(zip(skus, split), 1):
                    if qty <= 0:
                        continue
                    code, desc = sku[0], sku[1]
                    if (code == "A-1001" and cc in DUP_ITEM_COUNTRIES and i >= DUP_ITEM_FROM_MONTH):
                        code, desc = DUP_ITEM[0], DUP_ITEM[1]
                    price = round(sku[4] * PRICE_ADJ[cc] * (1 - discount), 2)
                    po_lines.append(dict(
                        po_number=po_no, po_line=ln, po_date=po_date.isoformat(), month=ym(i),
                        customer_record_id=rec["record_id"], customer_name=rec["customer_name"],
                        country=cc, entity=PRODUCTS[p]["entity"], product=p, item_code=code,
                        item_description=desc, quantity=qty, unit_price_sgd=price,
                        line_value_sgd=round(qty * price, 2), source_channel=channel,
                        _true_id=c["true_id"]))

po_lines.sort(key=lambda r: (r["po_date"], r["po_number"], r["po_line"]))


# --------------------------------------------------------------------------- 5. vendors & cost centres
VENDOR_A = ["Helix", "Norland", "Vireo", "Castell", "Brightwater", "Kestrel", "Meridian", "Aurora", "Sentinel",
            "Orion", "Halden", "Corvid", "Altamira", "Westbrook"]
VENDOR_B = ["Diagnostics", "Labware", "BioSystems", "Medical Devices", "Scientific", "Life Sciences"]
VENDOR_SFX = [("Germany", "GmbH"), ("USA", "Inc."), ("UK", "Ltd"), ("Japan", "Co., Ltd."), ("Switzerland", "AG"),
              ("Korea", "Co., Ltd."), ("China", "Co., Ltd."), ("Singapore", "Pte Ltd")]
vendors, vseen = [], set()
for k in range(30):
    base = f"{rng.choice(VENDOR_A)} {rng.choice(VENDOR_B)}"
    while base in vseen:
        base = f"{rng.choice(VENDOR_A)} {rng.choice(VENDOR_B)}"
    vseen.add(base)
    ctry, sfx = rng.choice(VENDOR_SFX)
    p = rng.choice("ABC")
    vendors.append(dict(vendor_id=f"V{2001 + k}", vendor_name=f"{base} {sfx}", country=ctry,
                        product_supplied=p, created_by_entity=PRODUCTS[p]["entity"],
                        created_date=date(rng.randint(2014, 2025), rng.randint(1, 12), 1).isoformat(),
                        payment_terms=rng.choice(["30 days", "60 days", "90 days", "Advance"]),
                        bank_name=rng.choice(["Deutsche Bank", "Citibank", "HSBC", "MUFG", "DBS", "Standard Chartered"]),
                        bank_account=f"{rng.randint(100, 999)}-{rng.randint(100000, 999999)}-{rng.randint(0, 9)}",
                        tax_id=f"TX{rng.randint(10000000, 99999999)}", duplicate_of=""))
for k, orig in enumerate(rng.sample(vendors, 3)):
    v = dict(orig, vendor_id=f"V{2101 + k}", vendor_name=name_variant(orig["vendor_name"]),
             created_by_entity=rng.choice([e for e in ("SPD", "QTS", "QTG") if e != orig["created_by_entity"]]),
             created_date=date(2025, rng.randint(5, 12), 1).isoformat(), duplicate_of=orig["vendor_id"])
    vendors.append(v)

cost_centres = []
for ent in ("SPD", "QTS", "QTG"):
    for dept, code in [("Sales", "SAL"), ("Marketing", "MKT"), ("Regulatory Affairs", "RA"), ("Service", "SVC"),
                       ("Finance", "FIN"), ("Warehouse", "WH")]:
        if ent != "QTG" and code == "SVC":
            continue
        cost_centres.append(dict(cost_centre_code=f"{ent}-{code}", cost_centre_name=f"{ent} {dept}",
                                 entity=ent, department=dept, owner=f"{dept} Head, {ent}"))


# --------------------------------------------------------------------------- 6. MDM request history (today's email process)
REQUESTORS = {"SPD": ["Amy Tan (Product Manager)", "Jason Koh (Product Manager)", "Siti Rahmah (Regional Sales)"],
              "QTS": ["Kelvin Lim (Procurement)", "Nadia Hassan (Regional Sales)", "Marcus Lee (Regional Sales)"],
              "QTG": ["Benjamin Goh (Service Manager)", "Tran Thi Mai (Regional Sales)", "Rachel Ng (Procurement)"]}
MISSING = {"Customer": ["Registration no. missing", "Credit terms not specified", "Billing address incomplete"],
           "Item": ["Regulatory licence no. missing", "Unit of measure missing", "HS code missing"],
           "Vendor": ["Bank details missing", "Tax ID missing", "ISO 13485 certificate missing"],
           "Cost Center": ["Cost centre owner not specified"]}


def office_hours(dt):
    """Push a timestamp into 08:30-18:00 on a weekday (people act during working hours)."""
    if dt.hour >= 18:
        dt = datetime(dt.year, dt.month, dt.day) + timedelta(days=1, hours=8, minutes=30 + rng.randint(0, 90))
    elif dt.hour < 8:
        dt = datetime(dt.year, dt.month, dt.day) + timedelta(hours=8, minutes=30 + rng.randint(0, 90))
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    return dt


def chain(rtype, regulated):
    if rtype == "Customer":
        return ["BU Head", "Finance", "Business Support"]
    if rtype == "Item":
        return ["BU Head"] + (["Quality/Regulatory"] if regulated else []) + ["Business Support"]
    if rtype == "Vendor":
        return ["BU Head", "Finance"] + (["Quality/Regulatory"] if regulated else []) + ["Business Support"]
    return ["Finance", "BU Head"]


requests, steps = [], []
seeded = []  # requests that explain specific master records
for c in new_customers:
    seeded.append(("Customer", c["primary"], month_start(c["start_month"]) - timedelta(days=rng.randint(18, 30)), False))
for c in true_customers:
    if c.get("mig_rec"):
        seeded.append(("Customer", c["mig_rec"], date.fromisoformat(c["mig_rec"]["created_date"]) - timedelta(days=rng.randint(12, 22)), True))
seeded.append(("Item", {"record_id": DUP_ITEM[0], "customer_name": DUP_ITEM[1], "country": "TH",
                        "created_by_entity": "QTS"},
               month_start(DUP_ITEM_FROM_MONTH) - timedelta(days=24), True))
random_req = []
for _ in range(150 - len(seeded)):
    rtype = rng.choices(["Customer", "Item", "Vendor", "Cost Center"], weights=[0.40, 0.32, 0.16, 0.12])[0]
    d = START + timedelta(days=rng.randrange((month_start(N_MONTHS) - START).days - 20))
    random_req.append((rtype, None, d, rtype in ("Customer", "Item") and rng.random() < 0.10))

all_req = sorted(seeded + random_req, key=lambda x: x[2])
for k, (rtype, rec, d, created_dup) in enumerate(all_req, 1):
    rid = f"MDM-{k:04d}"
    ent = rec["created_by_entity"] if rec else rng.choice(["SPD", "QTS", "QTG"])
    requestor = rng.choice(REQUESTORS[ent])
    regulated = rtype == "Item" and rng.random() < 0.7 or rtype == "Vendor" and rng.random() < 0.5
    while d.weekday() >= 5:
        d += timedelta(days=1)
    t = business_time(d)
    submitted = t
    bounces, touch, reasons = 0, 0.0, []
    seq = 0

    def step(name, role, wait_days, work_h, outcome):
        global_t = step.t
        start = global_t
        end = office_hours(start + timedelta(days=wait_days, hours=work_h))
        wait_days = (end - start).total_seconds() / 86400 - work_h / 24
        step.n += 1
        steps.append(dict(request_id=rid, step_no=step.n, step=name, actor_role=role, received_at=fmt_dt(start),
                          completed_at=fmt_dt(end), wait_days=round(wait_days, 2), work_hours=round(work_h, 2),
                          outcome=outcome))
        step.t = end
        return work_h
    step.t, step.n = t, 0

    incomplete = rng.random() < 0.42
    touch += step("MDM triage", "MDM Analyst", lognormal(1.6, 0.6), rng.uniform(0.1, 0.3),
                  "Returned - incomplete" if incomplete else "Forwarded to approvers")
    while incomplete:
        bounces += 1
        reasons.append(rng.choice(MISSING[rtype]))
        touch += step("Requestor rework", "Requestor", lognormal(4.0, 0.6), rng.uniform(0.2, 0.5), "Resubmitted")
        incomplete = rng.random() < 0.15
        touch += step("MDM triage", "MDM Analyst", lognormal(1.2, 0.5), rng.uniform(0.1, 0.3),
                      "Returned - incomplete" if incomplete else "Forwarded to approvers")
    for role in chain(rtype, regulated):
        clar = rng.random() < 0.15
        wait = rng.uniform(0.1, 1.0) + lognormal(2.6, 0.55) + (lognormal(2.0, 0.5) if clar else 0)
        touch += step(f"{role} approval", role, wait, rng.uniform(0.1, 0.5),
                      "Approved after clarification" if clar else "Approved")
    touch += step("Create record in SAP B1", "MDM Analyst", lognormal(1.4, 0.5), rng.uniform(0.25, 0.6),
                  "Created in SAP B1")
    done = step.t
    if rec and rtype == "Customer":
        target = rec["record_id"]
        rec["created_date"] = done.date().isoformat()
    elif rec:
        target = rec["record_id"]
    else:
        target = ""
    requests.append(dict(
        request_id=rid, request_type=rtype, entity=ent, requestor=requestor,
        subject=(rec["customer_name"] if rec else ""),
        submitted_at=fmt_dt(submitted), sap_created_at=fmt_dt(done),
        cycle_days=round((done - submitted).total_seconds() / 86400, 1), touch_hours=round(touch, 2),
        bounces=bounces, bounce_reasons="; ".join(reasons), approvers_required=len(chain(rtype, regulated)),
        resulting_record_id=target, created_duplicate="Yes" if created_dup else "No"))


# --------------------------------------------------------------------------- 7. inbound messages (Apr - Sep 2026)
L = {  # local-language snippets
    "ID": dict(po="Mohon dikirimkan pesanan berikut sesuai PO terlampir.",
               enq="Mohon informasi harga dan ketersediaan untuk produk berikut.",
               fu="Mohon update status pengiriman untuk PO kami.", greet="Dengan hormat,", bye="Terima kasih,"),
    "MY": dict(po="Sila hantar pesanan berikut seperti dalam PO yang dilampirkan.",
               enq="Boleh berikan sebut harga untuk item berikut?",
               fu="Mohon kemas kini status penghantaran untuk PO kami.", greet="Tuan/Puan,", bye="Terima kasih,"),
    "VN": dict(po="Vui lòng giao các mặt hàng sau theo đơn đặt hàng đính kèm.",
               enq="Vui lòng báo giá và tình trạng hàng cho sản phẩm sau.",
               fu="Xin cập nhật tình trạng giao hàng cho đơn hàng của chúng tôi.", greet="Kính gửi,", bye="Trân trọng,"),
    "TH": dict(po="กรุณาจัดส่งสินค้าตามใบสั่งซื้อที่แนบมา",
               enq="ขอใบเสนอราคาและสถานะสินค้าสำหรับรายการต่อไปนี้",
               fu="ขอทราบสถานะการจัดส่งของใบสั่งซื้อของเรา", greet="เรียน ทีมงาน", bye="ขอบคุณครับ/ค่ะ"),
}

msgs = []
recent = [r for r in po_lines if r["month"] >= ym(12)]
pos = {}
for r in recent:
    pos.setdefault(r["po_number"], []).append(r)
email_pos = [v for v in pos.values() if v[0]["source_channel"] == "email"]
rng.shuffle(email_pos)
rec_by_id = {r["record_id"]: r for r in records}


def sender(cc):
    return rng.choice(COUNTRIES[cc]["people"])


def lines_text(lines):
    return "\n".join(f"- {l['quantity']} x {l['item_description']} ({l['item_code']})" for l in lines)


def mailbox(cc):
    return f"sales.{cc.lower()}@livesgroup.example"


def add_msg(label, cc, rec, subject, body, attach="", po=""):
    t = business_time(month_start(rng.randint(12, N_MONTHS - 1)) + timedelta(days=rng.randrange(28)))
    if po:
        t = business_time(date.fromisoformat(pos[po][0]["po_date"]))
    msgs.append(dict(received_at=fmt_dt(t), from_address=rec["contact_email"] if rec else "",
                     from_name="", to_mailbox=mailbox(cc), country=cc, subject=subject, body=body,
                     attachment_name=attach, true_label=label, linked_po_number=po,
                     linked_record_id=rec["record_id"] if rec else ""))
    return msgs[-1]


for lines in email_pos[:300]:
    h = lines[0]
    cc, rec = h["country"], rec_by_id[h["customer_record_id"]]
    who, po, q = sender(cc), h["po_number"], f"Q-{rng.randint(24000, 26999)}"
    local = cc != "SG" and rng.random() < 0.3
    if local:
        loc = L[cc]
        body = f"{loc['greet']}\n\n{loc['po']}\n{lines_text(lines)}\n\nPO: {po}\n\n{loc['bye']}\n{who}"
        subj = rng.choice([f"PO {po}", f"{po}", f"Order {po}"])
        att = f"PO_{po}.pdf"
    else:
        style = rng.random()
        if style < 0.5:
            subj = rng.choice([f"Purchase Order {po}", f"PO {po} - {rec['customer_name']}", f"New order: {po}"])
            body = (f"Dear Lives Group team,\n\nPlease find attached our purchase order {po}. Kindly arrange "
                    f"delivery of:\n{lines_text(lines)}\n\nDeliver to: {rec['address']}\n\nRegards,\n{who}\n"
                    f"Procurement, {rec['customer_name']}")
            att = f"PO_{po}.pdf"
        elif style < 0.8:  # tricky: no "purchase order" wording
            subj = rng.choice([f"Re: Quotation {q} - confirmed", "Please supply", f"Monthly requirement {h['month']}"])
            body = (f"Hi,\n\nAs per your quotation {q}, please supply the following:\n{lines_text(lines)}\n\n"
                    f"Please confirm the delivery date.\n\nThanks,\n{who}")
            att = f"Quotation_{q}_signed.pdf"
        else:  # tricky: order plus a question
            subj = rng.choice([f"Order + question on expiry ({po})", f"Our order {po}"])
            body = (f"Hello,\n\nWe'd like to place our order for this month:\n{lines_text(lines)}\n\nOur PO ref is {po}. "
                    f"Can you also confirm whether the new lot has a longer expiry date?\n\nThanks,\n{who}")
            att = ""
    m = add_msg("purchase_order", cc, rec, subj, body, att, po)
    m["from_name"] = who

active_recs = [r for r in records if r["customer_name"]]
for _ in range(230):
    rec = rng.choice(active_recs)
    cc, who = rec["country"], sender(rec["country"])
    item = rng.choice(ITEMS)
    if cc != "SG" and rng.random() < 0.3:
        loc = L[cc]
        subj, body = rng.choice(["Enquiry", "RFQ", item[1]]), f"{loc['greet']}\n\n{loc['enq']}\n- {item[1]}\n\n{loc['bye']}\n{who}"
    else:
        subj, body = rng.choice([
            (f"Price enquiry - {item[1]}", f"Dear team,\n\nCould you please send a quotation for {rng.choice([10, 20, 50, 100])} "
                                           f"units of {item[1]}? We are comparing suppliers for next quarter.\n\nRegards,\n{who}"),
            (f"Availability of {item[1]}", f"Hi,\n\nIs {item[1]} currently in stock? What is the lead time to {rec['city']}?\n\nThanks,\n{who}"),
            ("Planning next quarter's order", f"Hello,\n\nWe are planning to order {item[1]} next quarter. Could you share your "
                                              f"best price and minimum order quantity?\n\nBest,\n{who}"),
            ("Request for product information", f"Dear Sir/Madam,\n\nPlease send the product brochure and IFU for {item[1]}.\n\n{who}"),
            (f"Alternative to {item[0]}?", f"Hi,\n\nDo you have a cheaper alternative to {item[1]}? Our budget has been reduced "
                                           f"this year.\n\nRegards,\n{who}"),
        ])
    add_msg("enquiry", cc, rec, subj, body)["from_name"] = who

for _ in range(70):
    lines = rng.choice(list(pos.values()))
    h = lines[0]
    cc, rec, who, po = h["country"], rec_by_id[h["customer_record_id"]], sender(h["country"]), h["po_number"]
    if cc != "SG" and rng.random() < 0.3:
        loc = L[cc]
        subj, body = f"RE: PO {po}", f"{loc['greet']}\n\n{loc['fu']} ({po})\n\n{loc['bye']}\n{who}"
    else:
        subj, body = rng.choice([
            (f"RE: PO {po} - delivery status", f"Hi,\n\nWe placed PO {po} two weeks ago and have not received the goods. "
                                               f"Could you update us?\n\n{who}"),
            (f"Invoice query for {po}", f"Dear team,\n\nThe invoice for PO {po} shows the wrong quantity. Please check.\n\n{who}"),
            ("Any update?", f"Hi,\n\nJust following up on my previous email about our order {po}.\n\nThanks,\n{who}"),
        ])
    m = add_msg("follow_up", cc, rec, subj, body)
    m.update(from_name=who, linked_po_number=po)

for _ in range(60):
    if rng.random() < 0.7:  # internal setup request sent to the wrong (sales) mailbox or MDM mailbox
        ent = rng.choice(["SPD", "QTS", "QTG"])
        who = rng.choice(REQUESTORS[ent]).split(" (")[0]
        cc = rng.choice(list(COUNTRIES))
        tc = rng.choice([c for c in true_customers if c["country"] == cc])
        subj, body = rng.choice([
            (f"New customer setup - {tc['name']}", f"Hi MDM team,\n\nPlease set up {tc['name']} as a new customer under {ent}. "
                                                   f"Details in the attached spreadsheet (copied from my last request).\n\nThanks,\n{who}"),
            ("Request: new item code", f"Hi,\n\nI need a new item code for {rng.choice(ITEMS)[1]} - shipment arriving next week. "
                                       f"Not sure if QA sign-off is needed.\n\n{who}"),
            (f"New vendor registration - {rng.choice(vendors)['vendor_name']}",
             f"Hi team,\n\nPlease register this supplier. Bank details are in the attachment.\n\n{who}"),
        ])
        m = add_msg("mdm_request", cc, None, subj, body, "request_details.xlsx")
        m.update(from_address=f"{slug(who)}@livesgroup.example", from_name=who,
                 to_mailbox=rng.choice([mailbox(cc), "mdm@livesgroup.example"]))
    else:  # customer asks for a master-data change
        rec = rng.choice(active_recs)
        who = sender(rec["country"])
        m = add_msg("mdm_request", rec["country"], rec, "Change of billing address",
                    f"Dear team,\n\nPlease note our new billing address effective next month: "
                    f"{rng.randint(1, 300)} {rng.choice(COUNTRIES[rec['country']]['streets'])}, {rec['city']}. "
                    f"Kindly update your records.\n\nRegards,\n{who}")
        m["from_name"] = who

msgs.sort(key=lambda m: m["received_at"])
for k, m in enumerate(msgs, 1):
    m["message_id"] = f"MSG-{k:05d}"


# --------------------------------------------------------------------------- 8. write dataset
write_csv(DATA / "customer_master.csv", sorted(records, key=lambda r: r["record_id"]),
          ["record_id", "customer_name", "country", "city", "address", "registration_no", "segment",
           "created_by_entity", "created_date", "contact_email", "payment_terms", "credit_limit_sgd", "status"])
write_csv(DATA / "item_master.csv", items,
          ["item_code", "description", "product", "product_name", "owning_entity", "uom", "list_price_sgd",
           "regulated", "created_date"])
write_csv(DATA / "vendor_master.csv", vendors,
          ["vendor_id", "vendor_name", "country", "product_supplied", "created_by_entity", "created_date",
           "payment_terms", "bank_name", "bank_account", "tax_id"])
write_csv(DATA / "cost_centres.csv", cost_centres,
          ["cost_centre_code", "cost_centre_name", "entity", "department", "owner"])
write_csv(DATA / "purchase_orders.csv", po_lines,
          ["po_number", "po_line", "po_date", "month", "customer_record_id", "customer_name", "country", "entity",
           "product", "item_code", "item_description", "quantity", "unit_price_sgd", "line_value_sgd",
           "source_channel"])
write_csv(DATA / "mdm_requests_history.csv", requests,
          ["request_id", "request_type", "entity", "requestor", "subject", "submitted_at", "sap_created_at",
           "cycle_days", "touch_hours", "bounces", "bounce_reasons", "approvers_required", "resulting_record_id"])
write_csv(DATA / "mdm_request_steps.csv", steps,
          ["request_id", "step_no", "step", "actor_role", "received_at", "completed_at", "wait_days",
           "work_hours", "outcome"])
write_csv(DATA / "inbound_messages.csv", msgs,
          ["message_id", "received_at", "from_address", "from_name", "to_mailbox", "country", "subject", "body",
           "attachment_name"])

# answer keys
write_csv(KEY / "customer_record_truth.csv",
          [dict(record_id=r["record_id"], true_customer_id=r["true_id"], dup_type=r["dup_type"]) for r in
           sorted(records, key=lambda r: r["record_id"])],
          ["record_id", "true_customer_id", "dup_type"])
write_csv(KEY / "true_customers.csv",
          [dict(true_customer_id=c["true_id"], canonical_name=c["name"], country=c["country"], segment=c["segment"],
                products_bought="+".join(c["products"]),
                pattern=("new customer from " + ym(c["start_month"])) if c["start_month"] else
                ("true drop-off from " + ym(c["churn"]["start"]) + f" to {int(c['churn']['end_level'] * 100)}% of normal")
                if c["churn"] else "",
                cross_sell_gap="A not B" if ("A" in c["products"] and "B" not in c["products"]) else
                ("B not A" if ("B" in c["products"] and "A" not in c["products"]) else ""))
           for c in true_customers],
          ["true_customer_id", "canonical_name", "country", "segment", "products_bought", "pattern", "cross_sell_gap"])
write_csv(KEY / "inbound_message_labels.csv",
          [dict(message_id=m["message_id"], true_label=m["true_label"], linked_po_number=m["linked_po_number"],
                linked_record_id=m["linked_record_id"]) for m in msgs],
          ["message_id", "true_label", "linked_po_number", "linked_record_id"])
write_csv(KEY / "duplicate_items_vendors.csv",
          [dict(kind="item", id=DUP_ITEM[0], duplicate_of="A-1001",
                note=f"Orders for A-1001 in {'/'.join(DUP_ITEM_COUNTRIES)} booked under {DUP_ITEM[0]} from {ym(DUP_ITEM_FROM_MONTH)}")]
          + [dict(kind="vendor", id=v["vendor_id"], duplicate_of=v["duplicate_of"], note="") for v in vendors if v["duplicate_of"]],
          ["kind", "id", "duplicate_of", "note"])
write_csv(KEY / "mdm_requests_flags.csv",
          [dict(request_id=r["request_id"], created_duplicate=r["created_duplicate"]) for r in requests],
          ["request_id", "created_duplicate"])


# --------------------------------------------------------------------------- 9. SharePoint list templates
write_csv(SP / "BusinessUnits.csv",
          [dict(Title="SPD", BusinessUnitName="SPD (IVD reagents & rapid tests)", Products="A", Active="Yes"),
           dict(Title="QTS", BusinessUnitName="QTS (lab consumables)", Products="B", Active="Yes"),
           dict(Title="QTG", BusinessUnitName="QTG (medical & lab equipment)", Products="C", Active="Yes")],
          ["Title", "BusinessUnitName", "Products", "Active"])

ROLES = [  # role, entity, persona, email, escalate-to, time zone (IANA) of where the person sits
    ("Requestor", "Any", "Amy (requestor persona)", "<teammate-1 SMU email>", "", "Asia/Singapore"),
    ("BU Head", "SPD", "SPD BU Head", "<teammate-2 SMU email>", "<teammate-4 SMU email>", "Asia/Singapore"),
    ("BU Head", "QTS", "QTS BU Head", "<teammate-2 SMU email>", "<teammate-4 SMU email>", "Asia/Kuala_Lumpur"),
    ("BU Head", "QTG", "QTG BU Head", "<teammate-2 SMU email>", "<teammate-4 SMU email>", "Asia/Bangkok"),
    ("Finance", "Any", "Wei Jie (Finance Manager)", "<teammate-3 SMU email>", "<teammate-4 SMU email>", "Asia/Singapore"),
    ("Quality/Regulatory", "Any", "QA/RA Lead", "<teammate-2 SMU email>", "<teammate-4 SMU email>", "Asia/Jakarta"),
    ("Business Support", "Any", "Business Support", "<teammate-3 SMU email>", "<teammate-4 SMU email>", "Asia/Ho_Chi_Minh"),
    ("MDM Analyst", "Any", "Priya (MDM Analyst)", "<teammate-4 SMU email>", "", "Asia/Singapore"),
]
write_csv(SP / "Roles.csv", [dict(Title=f"{r[0]} - {r[1]}", Role=r[0], Entity=r[1], PersonName=r[2],
                                  PersonEmail=r[3], EscalateTo=r[4], TimeZone=r[5]) for r in ROLES],
          ["Title", "Role", "Entity", "PersonName", "PersonEmail", "EscalateTo", "TimeZone"])

RULES = [
    ("Customer", "", "", "BU Head", 1), ("Customer", "", "", "Finance", 1), ("Customer", "", "", "Business Support", 1),
    ("Item", "", "", "BU Head", 1), ("Item", "IsRegulated", "Yes", "Quality/Regulatory", 1),
    ("Item", "", "", "Business Support", 1),
    ("Vendor", "", "", "BU Head", 1), ("Vendor", "", "", "Finance", 1),
    ("Vendor", "SuppliesRegulatedGoods", "Yes", "Quality/Regulatory", 1), ("Vendor", "", "", "Business Support", 1),
    ("Cost Center", "", "", "Finance", 1), ("Cost Center", "", "", "BU Head", 1),
    ("Any", "", "", "MDM Analyst", 2),
]
write_csv(SP / "RoutingRules.csv",
          [dict(Title=f"R{k:02d}", RequestType=r[0], Entity="Any", ConditionField=r[1], ConditionValue=r[2],
                ApproverRole=r[3], Stage=r[4], SLADays=1 if r[4] == 2 else 2, EscalateAfterDays="" if r[4] == 2 else 4,
                Active="Yes") for k, r in enumerate(RULES, 1)],
          ["Title", "RequestType", "Entity", "ConditionField", "ConditionValue", "ApproverRole", "Stage", "SLADays",
           "EscalateAfterDays", "Active"])

FIELDS = [
    ("Customer", "CustomerName", "Customer legal name", "Text", "Always", "", "", "No", "All", "Exact legal name as on registration"),
    ("Customer", "Country", "Country", "Choice", "Always", "", "", "No", "All", "SG / MY / TH / ID / VN"),
    ("Customer", "RegistrationNo", "Company registration no.", "Text", "Always", "", "", "No", "All", "UEN / SSM / tax ID"),
    ("Customer", "BillingAddress", "Billing address", "Text", "Always", "", "", "No", "All", ""),
    ("Customer", "ContactEmail", "Purchasing contact email", "Text", "Always", "", "", "No", "All", ""),
    ("Customer", "Segment", "Customer segment", "Choice", "Always", "", "", "No", "All", "Hospital / Laboratory / Clinic"),
    ("Customer", "PaymentTerms", "Payment terms", "Choice", "Always", "", "", "Yes", "Finance;MDM Analyst", "Stored in SensitiveDetails"),
    ("Customer", "CreditLimit", "Credit limit (SGD)", "Number", "Always", "", "", "Yes", "Finance;MDM Analyst", "Stored in SensitiveDetails"),
    ("Item", "ItemDescription", "Item description", "Text", "Always", "", "", "No", "All", ""),
    ("Item", "ProductFamily", "Product family", "Choice", "Always", "", "", "No", "All", "A / B / C"),
    ("Item", "UnitOfMeasure", "Unit of measure", "Choice", "Always", "", "", "No", "All", "Kit / Box / Pack / Unit / Set"),
    ("Item", "HSCode", "HS code", "Text", "Always", "", "", "No", "All", "Needed for import"),
    ("Item", "IsRegulated", "Is this a regulated medical device / IVD?", "Yes/No", "Always", "", "", "No", "All", "Adds Quality/Regulatory approval if Yes"),
    ("Item", "RegulatoryLicenceNo", "Regulatory licence no.", "Text", "Conditional", "IsRegulated", "Yes", "No", "All", "HSA / MDA / Thai FDA / BPOM / DAV"),
    ("Item", "ShelfLifeMonths", "Shelf life (months)", "Number", "Conditional", "ProductFamily", "A", "No", "All", "Reagents only"),
    ("Vendor", "VendorName", "Vendor legal name", "Text", "Always", "", "", "No", "All", ""),
    ("Vendor", "Country", "Vendor country", "Text", "Always", "", "", "No", "All", ""),
    ("Vendor", "TaxID", "Tax ID", "Text", "Always", "", "", "No", "All", ""),
    ("Vendor", "SuppliesRegulatedGoods", "Supplies regulated goods?", "Yes/No", "Always", "", "", "No", "All", "Adds Quality/Regulatory approval if Yes"),
    ("Vendor", "ISO13485CertNo", "ISO 13485 certificate no.", "Text", "Conditional", "SuppliesRegulatedGoods", "Yes", "No", "All", ""),
    ("Vendor", "BankName", "Bank name", "Text", "Always", "", "", "Yes", "Finance;MDM Analyst", "Stored in SensitiveDetails"),
    ("Vendor", "BankAccount", "Bank account no.", "Text", "Always", "", "", "Yes", "Finance;MDM Analyst", "Stored in SensitiveDetails"),
    ("Vendor", "PaymentTerms", "Payment terms", "Choice", "Always", "", "", "Yes", "Finance;MDM Analyst", "Stored in SensitiveDetails"),
    ("Cost Center", "CostCenterName", "Cost centre name", "Text", "Always", "", "", "No", "All", ""),
    ("Cost Center", "Department", "Department", "Choice", "Always", "", "", "No", "All", ""),
    ("Cost Center", "Owner", "Cost centre owner", "Person", "Always", "", "", "No", "All", ""),
    ("Cost Center", "BudgetYear", "Budget year", "Number", "Always", "", "", "No", "All", ""),
]
write_csv(SP / "RequiredFields.csv",
          [dict(Title=f"{f[0]}.{f[1]}", RequestType=f[0], FieldName=f[1], DisplayLabel=f[2], FieldType=f[3],
                Required=f[4], ConditionField=f[5], ConditionValue=f[6], Sensitive=f[7], VisibleToRoles=f[8],
                HelpText=f[9]) for f in FIELDS],
          ["Title", "RequestType", "FieldName", "DisplayLabel", "FieldType", "Required", "ConditionField",
           "ConditionValue", "Sensitive", "VisibleToRoles", "HelpText"])

write_csv(SP / "CustomerMaster.csv",
          [dict(Title=r["record_id"], CustomerName=r["customer_name"], NormalizedName=normalise(r["customer_name"]),
                Country=r["country"], City=r["city"], Address=r["address"], RegistrationNo=r["registration_no"],
                Segment=r["segment"], CreatedByEntity=r["created_by_entity"])
           for r in sorted(records, key=lambda r: r["record_id"])],
          ["Title", "CustomerName", "NormalizedName", "Country", "City", "Address", "RegistrationNo", "Segment",
           "CreatedByEntity"])
write_csv(SP / "ItemMaster.csv",
          [dict(Title=i["item_code"], Description=i["description"], NormalizedName=normalise(i["description"]),
                ProductFamily=i["product"], OwningEntity=i["owning_entity"], UOM=i["uom"], Regulated=i["regulated"])
           for i in items],
          ["Title", "Description", "NormalizedName", "ProductFamily", "OwningEntity", "UOM", "Regulated"])
write_csv(SP / "Aliases.csv",
          [dict(Title="nuh", CanonicalName="National University Hospital", RecordID=nuh["primary"]["record_id"]),
           dict(Title="national univ hospital", CanonicalName="National University Hospital",
                RecordID=nuh["primary"]["record_id"])],
          ["Title", "CanonicalName", "RecordID"])
write_csv(SP / "Requests.csv", [],
          ["Title", "RequestType", "Entity", "Country", "Requestor", "Status", "CurrentStage", "SubmittedAt",
           "CompletedAt", "CustomerName", "RegistrationNo", "BillingAddress", "ContactEmail", "Segment",
           "ItemDescription", "ProductFamily", "UnitOfMeasure", "HSCode", "IsRegulated", "RegulatoryLicenceNo",
           "ShelfLifeMonths", "VendorName", "TaxID", "SuppliesRegulatedGoods", "ISO13485CertNo", "CostCenterName",
           "Department", "Owner", "BudgetYear", "DuplicateCheck", "PossibleMatchID", "SAPCode"])
write_csv(SP / "SensitiveDetails.csv", [],
          ["Title", "RequestID", "PaymentTerms", "CreditLimit", "BankName", "BankAccount"])
write_csv(SP / "ApprovalLog.csv", [],
          ["Title", "RequestID", "Timestamp", "Actor", "ActorRole", "Action", "Detail", "FieldChanged", "OldValue",
           "NewValue"])


# --------------------------------------------------------------------------- 10. sanity summary
def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"


dups = [r for r in records if r["dup_type"] != "original"]
print(f"True customers: {len(true_customers)}   customer master records: {len(records)}   "
      f"duplicate records: {len(dups)} ({pct(len(dups), len(records))})")
print(f"PO lines: {len(po_lines)}   POs: {len({r['po_number'] for r in po_lines})}   "
      f"items: {len(items)}   vendors: {len(vendors)}   cost centres: {len(cost_centres)}")
print(f"Inbound messages: {len(msgs)}  " + "  ".join(
    f"{lab}={sum(m['true_label'] == lab for m in msgs)}" for lab in ("purchase_order", "enquiry", "follow_up", "mdm_request")))
cyc = sorted(r["cycle_days"] for r in requests)
print(f"MDM requests: {len(requests)}   median cycle {cyc[len(cyc) // 2]} days   mean "
      f"{sum(cyc) / len(cyc):.1f}   bounced {pct(sum(r['bounces'] > 0 for r in requests), len(requests))}   "
      f"touch time {100 * sum(r['touch_hours'] for r in requests) / 24 / sum(cyc):.1f}% of elapsed")

print("\nUnits, last 6 months (Apr-Sep 2026) vs prior 6 (Oct 2025-Mar 2026) -- seasonal, see YoY in README:")
print("      " + "".join(f"{p:>16}" for p in PRODUCTS))
for cc in COUNTRIES:
    row = []
    for p in PRODUCTS:
        last = sum(r["quantity"] for r in po_lines if r["country"] == cc and r["product"] == p and r["month"] >= ym(12))
        prev = sum(r["quantity"] for r in po_lines if r["country"] == cc and r["product"] == p and ym(6) <= r["month"] < ym(12))
        row.append(f"{last:>7} ({(last / prev - 1) * 100:+4.0f}%)" if prev else f"{last:>7}   (n/a)")
    print(f"  {cc}  " + "".join(f"{x:>16}" for x in row))
