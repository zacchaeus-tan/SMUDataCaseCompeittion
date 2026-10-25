"""
Inbound message triage: purchase order vs enquiry vs follow-up vs master-data request.

Deliberately rule-based (no trained model to maintain). Rules are evidence, not keywords lists:
an actionable ORDER names specific items WITH quantities; an enquiry asks about price / stock / info;
a follow-up refers to an existing order without adding new lines; internal senders and
"update your records" requests are master-data work. Anything ambiguous goes to a human review queue
(in production: an off-the-shelf AI prompt first, then review).
"""
import re

import pandas as pd

INTERNAL_DOMAIN = "@livesgroup.example"

ITEM_LINE = re.compile(r"^\s*-\s*\d+\s*x\s+.+", re.M)  # "- 16 x Dengue NS1 ..."
SIGNALS = {
    "purchase_order": [r"purchase order", r"please supply", r"place (our|an|the) order", r"\bpo\b.*attached",
                       r"sesuai po", r"po yang dilampirkan", r"đơn đặt hàng", r"ใบสั่งซื้อที่แนบ"],
    "enquiry": [r"quotation for", r"\bquote\b", r"price", r"in stock", r"lead time", r"brochure", r"\bifu\b",
                r"alternative", r"planning to order", r"minimum order", r"harga", r"sebut harga", r"báo giá",
                r"ใบเสนอราคา"],
    "follow_up": [r"follow(ing)? up", r"delivery status", r"not received", r"any update", r"invoice",
                  r"status pengiriman", r"kemas kini status", r"cập nhật tình trạng", r"สถานะการจัดส่ง"],
    "mdm_request": [r"set up .* customer", r"new customer", r"item code", r"register .* supplier",
                    r"supplier registration", r"vendor registration", r"update your records",
                    r"billing address"],
}
LABELS = {"purchase_order": "Purchase order", "enquiry": "Enquiry", "follow_up": "Follow-up",
          "mdm_request": "Master-data request", "review": "Needs review"}


def classify(subject: str, body: str, attachment: str = "", sender: str = ""):
    text = f"{subject}\n{body}".lower()
    hits = {lab: [p for p in pats if re.search(p, text)] for lab, pats in SIGNALS.items()}
    lines = len(ITEM_LINE.findall(body or ""))
    att = (attachment or "").lower()

    if sender.lower().endswith(INTERNAL_DOMAIN) or hits["mdm_request"]:
        return "mdm_request", "high", "Internal sender" if sender.lower().endswith(INTERNAL_DOMAIN) else \
            f"Master-data change: '{hits['mdm_request'][0]}'"
    if lines and (hits["purchase_order"] or att.startswith("po") or "signed" in att):
        return "purchase_order", "high", f"{lines} item line(s) with quantities + order evidence"
    if lines:
        return "purchase_order", "medium", f"{lines} item line(s) with quantities"
    if hits["follow_up"] and not hits["enquiry"]:
        return "follow_up", "high", f"Refers to existing order: '{hits['follow_up'][0]}'"
    if hits["enquiry"] and not hits["follow_up"]:
        return "enquiry", "high", f"Asks about '{hits['enquiry'][0]}', no quantities ordered"
    if hits["purchase_order"]:
        return "review", "low", "Order wording but no item quantities"
    return "review", "low", "No clear signal"


def classify_all(msgs: pd.DataFrame) -> pd.DataFrame:
    out = msgs.copy()
    res = [classify(r.subject, r.body, r.attachment_name, r.from_address)
           for r in msgs.fillna("").itertuples(index=False)]
    out["predicted"], out["confidence"], out["reason"] = zip(*res)
    return out


# --------------------------------------------------------------------------- optional AI step (stage 2)
# Only messages the rules could not decide are sent. Prototype uses OpenAI; production would run the same
# plain-English prompt through Power Automate's AI prompt action. No training, no model to maintain.
# Kept generic on purpose: no examples taken from the stress-test emails, so testing on them is a fair test.
# This exact wording was used for the recorded runs in data/ai_step_openai.csv and data/ai_step_chatgpt.csv.
AI_PROMPT = """You sort emails arriving in the shared sales mailbox of a medical-supplies distributor in Southeast Asia.
Emails may be in English, Malay, Bahasa Indonesia, Thai or Vietnamese.

Give each email exactly one label:
- purchase_order: the customer is buying now
- enquiry: the customer is asking a question or not yet committing to buy
- follow_up: about an order that was already placed
- mdm_request: asking to create or change customer, supplier or product records

Also give a confidence: high, or low if you are genuinely unsure."""

AI_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": ["purchase_order", "enquiry", "follow_up", "mdm_request"]},
        "confidence": {"type": "string", "enum": ["high", "low"]},
        "reason": {"type": "string"},
    },
    "required": ["label", "confidence", "reason"],
    "additionalProperties": False,
}


def ai_available() -> bool:
    from . import ai
    return ai.available()


def ai_classify(subject: str, body: str, attachment: str = ""):
    """Returns (label, confidence, reason). Low confidence or any failure -> stays in human review."""
    from . import ai

    out, err = ai.structured(AI_PROMPT, f"Subject: {subject}\nAttachment: {attachment or 'none'}\n\n{body}",
                             AI_SCHEMA, "email_label", max_tokens=300)
    if err:
        return "review", "low", err
    if out["confidence"] == "low":
        return "review", "low", f"AI unsure (leans {LABELS[out['label']]}): {out['reason']}"
    return out["label"], "ai", f"AI: {out['reason']}"
