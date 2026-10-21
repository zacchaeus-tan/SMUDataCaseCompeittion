from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KEY = DATA / "answer_key"          # ground truth: only used to SCORE methods, never as input
SHAREPOINT = ROOT / "sharepoint"   # same rule tables that get imported into SharePoint
STATE = ROOT / ".state"            # local SQLite for the workflow mock-up (git-ignored)

COUNTRIES = {"SG": "Singapore", "MY": "Malaysia", "TH": "Thailand", "ID": "Indonesia", "VN": "Vietnam"}
PRODUCTS = {"A": "IVD reagents & rapid tests", "B": "Lab consumables", "C": "Medical & lab equipment"}

# Growth measure: year-on-year units, same six months (removes seasonality)
CURRENT = ("2026-04", "2026-09")
PRIOR_YEAR = ("2025-04", "2025-09")
