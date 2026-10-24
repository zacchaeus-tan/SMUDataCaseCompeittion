"""
Request cycle time: today's email process (measured from the request history) vs the new design
(re-simulated from the SAME step-level history, changing only what the design changes).

Design levers and their stated assumptions:
  1. Smart form           -> share of bounces avoided (missing fields can't be submitted)
  2. Auto-triage          -> duplicate + completeness checks done at submission; triage wait ~0.2 day
  3. Parallel approvals   -> stage-1 approvers work at the same time: wait = slowest, not the sum
  4. Teams notification   -> share of each approver's wait that was "not seeing it" disappears
  5. Escalation           -> after the limit, the manager is pinged and it is resolved within ~1 day
  6. Generated SAP file   -> MDM final check + load within ~1 day
"""
import numpy as np
import pandas as pd


def breakdown(steps: pd.DataFrame) -> pd.DataFrame:
    s = steps.copy()
    s["days"] = s.wait_days + s.work_hours / 24
    s["stage"] = np.select([s.step.str.contains("approval"), s.step.eq("Requestor rework"),
                            s.step.eq("MDM triage")],
                           ["Waiting for approvers", "Rework (bounced back)", "MDM triage"], "Keying into SAP")
    out = s.groupby("stage").days.sum().rename("days").reset_index()
    out["share"] = out.days / out.days.sum()
    work = s.work_hours.sum() / 24
    return out.sort_values("share", ascending=False), work / s.days.sum()


def simulate(requests: pd.DataFrame, steps: pd.DataFrame, bounce_avoided=0.9, notice_cut=0.5,
             escalate_after_days=4.0, triage_days=0.2, sap_days=1.0, seed=7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for rid, g in steps.groupby("request_id"):
        approvals = g[g.step.str.contains("approval")]
        waits = approvals.wait_days.values * (1 - notice_cut)
        waits = np.where(waits > escalate_after_days, escalate_after_days + 1.0, waits)
        bounced = (g.step == "Requestor rework").any()
        keep_bounce = bounced and rng.random() > bounce_avoided
        rework = g[g.step == "Requestor rework"].wait_days.sum() if keep_bounce else 0.0
        future = triage_days + rework + (waits.max() if len(waits) else 0) + sap_days
        rows.append(dict(request_id=rid, future_days=future))
    out = requests[["request_id", "request_type", "cycle_days", "bounces"]].merge(pd.DataFrame(rows), on="request_id")
    return out


def new_customer_value(requests: pd.DataFrame, po_clean: pd.DataFrame, clusters: pd.DataFrame, days_saved: float):
    """Orders pulled forward: new customers start ordering once their record exists in SAP."""
    created = requests[(requests.request_type == "Customer") & requests.resulting_record_id.notna()
                       & (requests.resulting_record_id != "")]
    golden = dict(zip(clusters.record_id, clusters.golden_id))
    first = po_clean.groupby("customer_id").po_date.min()
    new_ids = {golden.get(r) for r in created.resulting_record_id}
    new_ids = [i for i in new_ids if i in first.index and first[i] >= "2025-07-01"]
    monthly = []
    for cid in new_ids:
        d = po_clean[po_clean.customer_id == cid]
        months = d.month.nunique()
        monthly.append(d.line_value_sgd.sum() / max(months, 1))
    per_customer = float(np.mean(monthly)) if monthly else 0.0
    per_year = len(new_ids) / 1.5  # 18-month history
    return dict(new_customers_per_year=per_year, avg_monthly_value=per_customer,
                pulled_forward_per_year=per_year * per_customer * days_saved / 30)
