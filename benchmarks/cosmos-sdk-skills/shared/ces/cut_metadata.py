import os
import json
import sys

keep_file, input_file, output_file = sys.argv[1], sys.argv[2], sys.argv[3]


# Parse agent metadata to determine if we should keep the metadata file as-is
agent_metadata_path = os.path.join(os.environ["AGENT_DIR"], "agent_metadata.json")
keep_all_keys = False
if os.path.exists(agent_metadata_path):
    print("Found agent metadata.")
    with open(agent_metadata_path) as f:
        try:
            agent_metadata = json.load(f)
            if agent_metadata.get("keep_metadata"):
                print("Keeping all metadata keys.")
                keep_all_keys = True
        except json.JSONDecodeError:
            print("Error decoding JSON from agent metadata file. Skipping.")

# Parse the metadata file
with open(input_file) as f:
    try:
        metadata = json.load(f)
    except Exception as e:
        print(f"Error reading metadata file: {e}")
        raise

if keep_all_keys:
    cut_metadata = metadata
    print("Keeping all keys from metadata file.")
else:
    # Parse the "keep" file
    if not os.path.exists(keep_file):
        print(f"Keep file not found: {keep_file}. Proceeding with default keys.")
        extra_keep_keys = []
    else:
        with open(keep_file) as f:
            try:
                extra_keep_keys = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
            except Exception as e:
                print(f"Error reading keep file: {e}")
                raise
        print(
            f"Parsed {len(extra_keep_keys)} extra keys from keep file: {extra_keep_keys}."
        )
    # Combine the keys from the keep file with the default keys
    DEFAULT_KEEP_KEYS = [
        "instance_id",
        "problem_statement",
    ]
    keep_keys = DEFAULT_KEEP_KEYS + extra_keep_keys
    print(f"Keeping {len(keep_keys)} keys from metadata file: {keep_keys}.")

    # Cut out secret keys from the metadata
    cut_metadata = {k: v for k, v in metadata.items() if k in keep_keys}
    print(f"Keeping {len(cut_metadata)} keys from metadata file: {cut_metadata}.")

# Write the cut metadata to the output file
with open(output_file, "w") as f:
    try:
        json.dump(cut_metadata, f, indent=4)
    except Exception as e:
        print(f"Error writing cut metadata file: {e}")
        raise
print(f"Cut metadata written to {output_file}.")