import json
from pathlib import Path

REQUIRED_DETAIL_KEYS = {"input_prompt", "output_response"}
PROMPT_ACTIONS = {"CODE_ANALYSIS", "FIX", "DEBUG"}  # ← put it here (module-level or inside main)

def main():
    p = Path("logs/experiment_data.json")
    if not p.exists():
        print("OK: no logs file yet.")
        return

    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, list), "logs must be a JSON list"

    for i, e in enumerate(data):
        assert isinstance(e, dict), f"entry[{i}] must be an object"

        action = e.get("action")
        details = e.get("details")

        # Only validate prompt-related actions
        if action in PROMPT_ACTIONS:
            assert isinstance(details, dict), f"entry[{i}] details must be an object"
            missing = REQUIRED_DETAIL_KEYS - details.keys()
            assert not missing, f"entry[{i}] missing required detail keys: {missing}"

    print("OK: logs contain required fields.")

if __name__ == "__main__":
    main()
