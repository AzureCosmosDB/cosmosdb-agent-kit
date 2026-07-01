#!/usr/bin/env python3
"""
parse.py - Harbor Reward to MSBench eval.json Parser

Converts Harbor's reward output to the MSBench standard eval.json format.

Harbor Reward Formats (see: https://github.com/laude-institute/harbor):
  1. /logs/verifier/reward.txt: Plain text file with single numeric value
     Example: "1.0" or "0.85"

  2. /logs/verifier/reward.json: JSON file with metrics. Supports:
     a. Flat dict with "reward" key: {"reward": 0.85, "accuracy": 0.92}
     b. Flat dict with only numeric values: {"accuracy": 0.92, "r2": 0.78}
        (mean of all values is used as reward)
     c. Nested per-metric dicts: {"e2e": {"score": 1.0}, "unit-test": {"score": 1.0}}
        (mean of "score" values is used as reward)

MSBench Output Format:
  {
    "<instance_id>": {
      "resolved": true|false
    }
  }

Harbor checks reward.txt first, then falls back to reward.json.
See: https://github.com/laude-institute/harbor/blob/main/src/harbor/verifier/verifier.py

Harbor uses a reward-based system where:
  - reward > 0.0 => resolved = True
  - reward <= 0.0 => resolved = False
"""
import os
import json


def extract_reward_from_json(data):
    """Extract a single reward value from a reward.json dict.

    Handles three formats:
      1. Flat dict with "reward" key -> use that value directly
      2. Flat dict with only numeric values -> mean of all values
      3. Nested per-metric dicts with "score" keys -> mean of scores

    Returns:
        (float, str): Tuple of (reward_value, method_description)
                       or (None, reason) if no reward could be extracted.
    """
    if not isinstance(data, dict) or not data:
        return None, "empty or non-dict data"

    # 1. Explicit "reward" key takes priority
    if "reward" in data:
        try:
            return float(data["reward"]), "reward key"
        except (ValueError, TypeError):
            pass

    # 2. Check if all values are numeric (flat dict of metrics)
    all_numeric = all(isinstance(v, (int, float)) for v in data.values())
    if all_numeric:
        values = [float(v) for v in data.values()]
        mean = sum(values) / len(values)
        return mean, "mean of flat metrics"

    # 3. Check for nested per-metric dicts with "score" keys
    scores = []
    for key, value in data.items():
        if isinstance(value, dict) and "score" in value:
            try:
                scores.append(float(value["score"]))
            except (ValueError, TypeError):
                pass
    if scores:
        mean = sum(scores) / len(scores)
        return mean, "mean of nested scores"

    return None, "no recognized reward format"


# Environment variables
metadata_path = os.environ.get("METADATA_PATH", "/drop/metadata.json")
output_dir = os.environ.get("OUTPUT_DIR", "/output")

# Read instance_id - prefer instanceId env var (set by MSBench), fallback to metadata file
instance_id = os.environ.get("instanceId")
if not instance_id:
    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
        instance_id = metadata.get("instance_id", "unknown")
    except Exception as e:
        print(f"Warning: Could not read metadata from {metadata_path}: {e}")
        instance_id = "unknown"

# Try to parse Harbor reward file.
# Priority matches Harbor's verifier.py: reward.txt first, then reward.json.
# See: https://github.com/laude-institute/harbor/blob/main/src/harbor/verifier/verifier.py
resolved = False
reward_value = 0.0
reward_source = None
all_metrics = {}

# Check for reward.txt first (Harbor's default)
reward_txt_paths = [
    "/logs/verifier/reward.txt",
    os.path.join(output_dir, "reward.txt"),
]

for path in reward_txt_paths:
    if os.path.exists(path):
        try:
            with open(path) as f:
                content = f.read().strip()
            if content:
                reward_value = float(content)
                resolved = reward_value > 0.0
                reward_source = path
                all_metrics = {"reward": reward_value}
                print(f"Parsed reward.txt from {path}: value={reward_value}, resolved={resolved}")
                break
        except (ValueError, IOError) as e:
            print(f"Warning: Could not parse {path}: {e}")

# Fall back to reward.json if no reward.txt found
if reward_source is None:
    reward_json_paths = [
        "/logs/verifier/reward.json",
        os.path.join(output_dir, "reward.json"),
    ]

    for path in reward_json_paths:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    all_metrics = json.load(f)
                extracted, method = extract_reward_from_json(all_metrics)
                if extracted is not None:
                    reward_value = extracted
                    resolved = reward_value > 0.0
                    reward_source = path
                    print(f"Parsed reward.json from {path} via {method}: reward={reward_value}, resolved={resolved}")
                else:
                    print(f"Warning: reward.json at {path} has {method}")
                print(f"All metrics: {all_metrics}")
                break
            except (ValueError, IOError, json.JSONDecodeError) as e:
                print(f"Warning: Could not parse {path}: {e}")

if reward_source is None:
    print("Warning: No reward file found, defaulting to resolved=False")

# Write MSBench eval.json
eval_output = {
    instance_id: {
        "resolved": resolved
    }
}

eval_json_path = os.path.join(output_dir, "eval.json")
with open(eval_json_path, "w") as f:
    json.dump(eval_output, f, indent=2)

print(f"Wrote eval.json to {eval_json_path}")
