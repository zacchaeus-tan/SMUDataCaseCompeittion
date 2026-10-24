"""
The one place the prototype calls an AI model (OpenAI). Used by the email sorter and the AI action brief.

Defaults to OpenAI's smallest current model with reasoning switched off, so a call costs only the prompt and the
short JSON answer. Set OPENAI_MODEL to try another model (e.g. gpt-5.4-mini if the brief needs more depth).
"""
import json
import os

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-nano")


def available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def structured(system: str, user: str, schema: dict, name: str, max_tokens: int):
    """Returns (dict, None), or (None, reason) when the call fails, is refused or is cut off."""
    import openai

    extra = {"reasoning_effort": "none"} if MODEL.startswith(("gpt-5", "o")) else {}
    try:
        response = openai.OpenAI().chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_schema", "json_schema": {"name": name, "strict": True, "schema": schema}},
            max_completion_tokens=max_tokens,
            **extra,
        )
    except openai.APIConnectionError:
        return None, "AI step unreachable (network)"
    except openai.RateLimitError:
        return None, "AI step rate-limited, try again in a minute"
    except openai.APIStatusError as e:
        return None, f"AI step error {e.status_code}"
    choice = response.choices[0]
    if choice.message.refusal:
        return None, "AI declined to answer"
    if choice.finish_reason == "length":
        return None, "AI answer was cut off"
    return json.loads(choice.message.content), None
