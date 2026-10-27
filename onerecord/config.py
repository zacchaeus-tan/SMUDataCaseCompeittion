from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KEY = DATA / "answer_key"          # ground truth: only used to SCORE methods, never as input
SHAREPOINT = ROOT / "sharepoint"   # same rule tables that get imported into SharePoint

COUNTRIES = {"SG": "Singapore", "MY": "Malaysia", "TH": "Thailand", "ID": "Indonesia", "VN": "Vietnam"}
PRODUCTS = {"A": "IVD reagents & rapid tests", "B": "Lab consumables", "C": "Medical & lab equipment"}

# Growth measure: % change in purchase-order units, last 6 months vs a comparison window. Change this one constant:
#   "yoy"        - vs the same 6 months a year earlier (default: same seasons, so dengue season and the December
#                  budget spend cancel out)
#   "sequential" - vs the 6 months just before (simpler, but compares different seasons)
GROWTH_BASIS = "yoy"
CURRENT = ("2026-04", "2026-09")
# the comparison window (named from when it was always a year earlier)
PRIOR_YEAR = {"yoy": ("2025-04", "2025-09"), "sequential": ("2025-10", "2026-03")}[GROWTH_BASIS]
GROWTH_LABEL = {"yoy": "vs the same 6 months a year earlier",
                "sequential": "vs the 6 months before"}[GROWTH_BASIS]
