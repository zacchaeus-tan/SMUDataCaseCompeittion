from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KEY = DATA / "answer_key"          # ground truth: only used to SCORE methods, never as input
SHAREPOINT = ROOT / "sharepoint"   # same rule tables that get imported into SharePoint

COUNTRIES = {"SG": "Singapore", "MY": "Malaysia", "TH": "Thailand", "ID": "Indonesia", "VN": "Vietnam"}
# The live OneRecord Power App (the request workflow), embedded in the Streamlit "Requests" pages
POWER_APP_URL = ("https://apps.powerapps.com/play/e/default-c98a79ca-5a9a-4791-a243-f06afd67464d/a/"
                 "967cb70c-0e04-409d-8b53-60f87ab250ea?tenantId=c98a79ca-5a9a-4791-a243-f06afd67464d")

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
