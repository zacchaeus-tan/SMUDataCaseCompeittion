"""Add the duplicate-check columns to the master list CSVs (run after scripts/generate_data.py).

Usage: python3 sharepoint/match_keys.py

  MatchKey   cleaned-up name the request form compares with (onerecord/livecheck.match_key)
  IDKey      registration no. / part no. / tax ID without punctuation (onerecord/livecheck.id_key)
  SAPStatus  "In SAP" for records loaded from SAP; the Route and approve flow adds approved records as
             "Pending SAP import" and switches them to "In SAP" once MDM confirms the import
Safe to run again: the columns are recomputed.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from onerecord.livecheck import id_key, match_key  # noqa: E402

HERE = Path(__file__).parent
# list -> (name column, ID column); None = no key columns, only SAPStatus
LISTS = {"CustomerMaster": ("CustomerName", "RegistrationNo"), "ItemMaster": ("Description", "ManufacturerPartNo"),
         "VendorMaster": ("VendorName", "TaxID"), "CostCentres": None}


def main():
    for name, cols in LISTS.items():
        path = HERE / f"{name}.csv"
        rows = list(csv.DictReader(open(path, newline="")))
        for r in rows:
            if cols:
                r["MatchKey"], r["IDKey"] = match_key(r[cols[0]]), id_key(r[cols[1]])
            r["SAPStatus"] = r.get("SAPStatus") or "In SAP"
        fields = [f for f in rows[0] if f not in ("MatchKey", "IDKey", "SAPStatus")]
        fields += (["MatchKey", "IDKey"] if cols else []) + ["SAPStatus"]
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"{name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
