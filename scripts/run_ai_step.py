"""
Run the AI step on the stress-test emails the rules pass to review, and save the answers.

    python scripts/run_ai_step.py

Reads OPENAI_API_KEY (and optionally OPENAI_MODEL) from the environment or from .streamlit/secrets.toml, which
git ignores. Sends each email with the app's own instructions (onerecord/classify.py: AI_PROMPT) and no correct
label, and writes data/ai_step_openai.csv with the model and date, so the Orders vs enquiries page can show the
run without a key. Only the emails the rules could not sort are sent.
"""
import datetime
import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

secrets = ROOT / ".streamlit" / "secrets.toml"
if secrets.exists():
    for name, value in tomllib.loads(secrets.read_text(encoding="utf-8")).items():
        if name in ("OPENAI_API_KEY", "OPENAI_MODEL"):
            os.environ.setdefault(name, value)
if not os.environ.get("OPENAI_API_KEY"):
    sys.exit("No OPENAI_API_KEY: add it to .streamlit/secrets.toml or the environment.")

import pandas as pd  # noqa: E402

from onerecord import ai, classify  # noqa: E402  (ai reads the model name from the environment on import)
from onerecord.config import DATA  # noqa: E402

emails = classify.classify_all(pd.read_csv(DATA / "inbound_messages_holdout.csv", dtype=str).fillna(""))
queue = emails[emails.predicted == "review"]
rows = []
for r in queue.itertuples():
    out, err = ai.structured(classify.AI_PROMPT,
                             f"Subject: {r.subject}\nAttachment: {r.attachment_name or 'none'}\n\n{r.body}",
                             classify.AI_SCHEMA, "email_label", max_tokens=300)
    if err:  # a failed call is recorded as unsure, so it would go to a person
        out = {"label": "", "confidence": "low", "reason": f"Call failed: {err}"}
    rows.append(dict(message_id=r.message_id, ai_label=out["label"], ai_confidence=out["confidence"],
                     ai_reason=out["reason"]))
    print(f"{r.message_id}: {out['label'] or '-'} ({out['confidence']})")

result = pd.DataFrame(rows).assign(model=ai.MODEL, run_date=datetime.date.today().isoformat())
result.to_csv(DATA / "ai_step_openai.csv", index=False)
print(f"Saved {len(result)} answers from {ai.MODEL} to data/ai_step_openai.csv")
