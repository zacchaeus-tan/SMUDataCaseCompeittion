"""Name clean-up shared by the bulk matcher and the live duplicate check (mirrors sharepoint/LISTS.md)."""
import re

LEGAL = r"\b(pte|ltd|sdn|bhd|co|jsc|pt|inc|gmbh|ag|sa|the|s)\b"
EXPAND = {"hosp": "hospital", "ctr": "centre", "center": "centre", "univ": "university", "med": "medical",
          "lab": "laboratory", "spec": "specialist", "diag": "diagnostic", "gen": "general", "comm": "community",
          "and": "&", "childrens": "children's"}
ADDRESS = {"rd": "road", "ave": "avenue", "st": "street", "jln": "jalan", "blvd": "boulevard"}


def name_key(name: str) -> str:
    s = (name or "").lower().replace("&", " & ")
    s = re.sub(r"[^\w&' ]", " ", s)
    s = re.sub(LEGAL, " ", s)
    return " ".join(EXPAND.get(w, w) for w in s.split())


def address_key(addr: str) -> str:
    s = re.sub(r"[^\w ]", " ", (addr or "").lower())
    return " ".join(ADDRESS.get(w, w) for w in s.split())


def initials(key: str) -> str:
    return "".join(w[0] for w in key.split() if len(w) > 2 or w == "&")
