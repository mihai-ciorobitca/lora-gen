from json import load as json_load, JSONDecodeError
from random import randint

def build_payload(username: str, filename: str, prompt_text: str) -> dict:
    try:
        with open("workflow-api.json", encoding="utf-8") as f:
            payload = json_load(f)
    except FileNotFoundError:
        raise RuntimeError("workflow-api.json missing on server")
    except JSONDecodeError:
        raise RuntimeError("workflow-api.json invalid JSON")

    try:
        payload["prompt"]["67"]["inputs"]["seed"] = randint(0, 2**63 - 1)
        payload["prompt"]["10"]["inputs"]["filename_prefix"] = f"{username}/{filename}"
        payload["prompt"]["3"]["inputs"]["text"] = prompt_text
    except Exception as e:
        raise RuntimeError(f"Workflow missing required nodes: {e}")

    return payload
