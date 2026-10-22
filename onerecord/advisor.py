"""
AI action brief (Phase 2): an AI prompt reads the numbers the regional view already computed (growth, the
forecast with its range and stock plan, drop-offs, cross-sell) and writes a short, prioritised list of actions
for sales and supply chain.

Production: a monthly Power Automate flow runs this prompt through the AI prompt action (AI Builder) and posts
the brief to the regional sales channel in Teams - no API key for IT to manage, no model to train.
This prototype runs the same prompt through Claude only to preview the output.

The AI never sees raw orders or customer master data, only the summary below, and it is told to cite those
numbers, so every recommendation can be checked against the dashboard.
"""
import json

import pandas as pd

SYSTEM = """You are a commercial analyst for Lives Group, a Singapore-headquartered distributor of in-vitro
diagnostics (Product A: IVD reagents and rapid tests), lab consumables (Product B) and medical & lab equipment
(Product C) across Singapore (SG), Malaysia (MY), Thailand (TH), Indonesia (ID) and Vietnam (VN).

You receive a JSON summary computed from clean master data. Write the 5 most valuable actions for the next
quarter for the regional sales and supply-chain leads.

Rules:
- Use only numbers that appear in the JSON, and quote them in "evidence". Never invent figures.
- Prefer actions that combine signals (e.g. a growing market + a drop-off list, or a stock build + cross-sell).
- Where the stock plan says "Low confidence", do not recommend stocking on the forecast alone.
- Each action names one owner and a concrete first step someone can do this month.
- Plain English for a non-technical manager. No jargon such as WAPE or regression."""

SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "country": {"type": "string", "enum": ["SG", "MY", "TH", "ID", "VN", "All"]},
                    "product": {"type": "string", "enum": ["A", "B", "C", "A+B", "All"]},
                    "owner": {"type": "string", "enum": ["Country sales lead", "Key account manager",
                                                         "Supply chain", "Marketing", "Regional management"]},
                    "first_step": {"type": "string"},
                    "evidence": {"type": "string"},
                    "expected_impact": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["title", "country", "product", "owner", "first_step", "evidence", "expected_impact",
                             "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["headline", "actions"],
    "additionalProperties": False,
}


def facts(growth: pd.DataFrame, plan: pd.DataFrame, drops: pd.DataFrame, xsell: pd.DataFrame) -> dict:
    """The compact summary the AI is allowed to see (also shown on the page, so judges can check it)."""
    r = lambda x: None if pd.isna(x) else round(float(x), 3)
    out = {
        "period": "Growth: Apr-Sep 2026 vs Apr-Sep 2025 (units). Forecast: Oct-Dec 2026.",
        "growth_by_country_product": [
            dict(country=g.country, product=g["product"], units=int(g.units_now), yoy_growth=r(g.unit_growth),
                 momentum_3m=r(g.momentum_3m), value_sgd=round(g.value_now)) for _, g in growth.iterrows()],
        "stock_plan_next_3_months": [
            dict(country=p.country, product=p["product"], last_3_months=p.last_3_months,
                 forecast=p.next_3_months, low=p.low, high=p.high, change=r(p.change),
                 calendar_drivers=p.drivers, action=p.action) for _, p in plan.iterrows()],
        "customers_dropping_off_top10": [
            dict(name=d["name"], country=d.country, change_vs_last_year=r(d.change),
                 value_at_risk_sgd_per_quarter=d.value_at_risk_per_q) for _, d in drops.head(10).iterrows()],
        "drop_off_totals_by_country": drops.groupby("country").agg(
            customers=("id", "count"), value_at_risk_sgd_per_quarter=("value_at_risk_per_q", "sum")
        ).reset_index().to_dict("records"),
        "cross_sell_by_country": xsell.groupby(["country", "missing"]).agg(
            customers=("id", "count"), potential_sgd_per_year=("est_value_sgd_per_year", "sum")
        ).reset_index().rename(columns={"missing": "product_not_bought"}).to_dict("records"),
    }
    # numpy numbers -> plain JSON numbers
    return json.loads(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


def recommend(data: dict, focus: str = ""):
    """Returns (brief dict, None) or (None, reason) when the AI step is unavailable or declines."""
    import anthropic

    ask = "Summary data:\n" + json.dumps(data, default=str)
    if focus.strip():
        ask += f"\n\nThe reader asked you to focus on: {focus.strip()}"
    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model="claude-opus-5-5",
            max_tokens=16000,
            system=SYSTEM,
            messages=[{"role": "user", "content": ask}],
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APIConnectionError:
        return None, "AI step unreachable (network)"
    except anthropic.RateLimitError:
        return None, "AI step rate-limited, try again in a minute"
    except anthropic.APIStatusError as e:
        return None, f"AI step error {e.status_code}"
    if response.stop_reason == "refusal":
        return None, "AI declined to answer"
    if response.stop_reason == "max_tokens":
        return None, "AI answer was cut off"
    text = next((b.text for b in response.content if b.type == "text"), "")
    return json.loads(text), None
