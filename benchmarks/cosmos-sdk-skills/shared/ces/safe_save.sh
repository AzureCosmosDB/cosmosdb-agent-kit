#!/bin/bash
# safe_save.sh - self-contained replacement for /save.sh.
#
# Lives at /opt/safe_save.sh so the CES backend's runtime injection of
# /save.sh + /glob_files.py cannot clobber it. The upstream CES
# /glob_files.py at the time of writing is broken (TypeError in the
# pathspec on_error callback when /var/lock is a dangling symlink),
# which makes the encryption step blow up before the agent gets to run.
#
# We replicate the same contract as the original save.sh:
#   $1  encryption key (passphrase)
#   $2  path to a newline-delimited list of /-prefixed paths to encrypt
#       (each line is a directory or file rooted at /)
#   $3  path to a newline-delimited list of metadata keys to KEEP in
#       $METADATA_PATH (everything else is stripped)
#   $4  output file for the AES-256-CBC-encrypted tar.gz of the secrets

set -e

KEY="$1"
SECRET_FILES_LIST="$2"
KEEP_METADATA_FILE="$3"
OUTPUT_FILE="$4"

if [ -z "$KEY" ] || [ -z "$SECRET_FILES_LIST" ] || [ -z "$KEEP_METADATA_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <key> <secret-files-list> <metadata-keep-list> <output-enc-file>" >&2
    exit 1
fi

if [ ! -f "$SECRET_FILES_LIST" ]; then
    echo "[safe_save] secret files list '$SECRET_FILES_LIST' not found" >&2
    exit 1
fi

# Build the file list with bash + find (no pathspec, no /proc walking).
TEMP_LIST="$(mktemp)"
trap 'rm -f "$TEMP_LIST" "${TEMP_LIST}.f"' EXIT

while IFS= read -r pat; do
    [ -z "$pat" ] && continue
    case "$pat" in \#*) continue ;; esac
    # secret_files.txt lines are /-prefixed paths. Resolve relative to /.
    target="$pat"
    if [ -e "$target" ]; then
        # Emit every regular file under (or at) $target.
        find "$target" -type f >> "$TEMP_LIST"
    else
        echo "[safe_save] skipping missing entry: $target" >&2
    fi
done < "$SECRET_FILES_LIST"

# Never encrypt the encryption machinery itself.
grep -v -E '^/(save|safe_save|restore|entry|ces_activate|glob_files\.py|cut_metadata\.py|parse\.py|secret_files\.txt|nonsecret_metadata_keys\.txt)$' "$TEMP_LIST" \
    | grep -v -E '^/opt/safe_(save|restore)\.sh$' \
    > "${TEMP_LIST}.f" || true
mv "${TEMP_LIST}.f" "$TEMP_LIST"

echo "[safe_save] Files to encrypt:"
cat "$TEMP_LIST"

# Strip non-public keys out of the task metadata, in place.
TEMP_METADATA="$(mktemp)"
python3 /cut_metadata.py "$KEEP_METADATA_FILE" "$METADATA_PATH" "$TEMP_METADATA"

# tar -T expects paths relative to its cwd; absolute paths work too on
# GNU tar with a warning. Use --absolute-names to silence and strip the
# leading slash so restore can extract back to /.
tar -czf - --absolute-names --transform 's|^/||' -T "$TEMP_LIST" \
    | openssl enc -aes-256-cbc -salt -pbkdf2 -pass "pass:$KEY" -out "$OUTPUT_FILE"

# Remove the originals so the agent cannot peek.
while IFS= read -r f; do
    rm -f "$f"
done < "$TEMP_LIST"

# Collapse now-empty secret directories so they don't dangle.
while IFS= read -r pat; do
    [ -z "$pat" ] && continue
    case "$pat" in \#*) continue ;; esac
    if [ -d "$pat" ] && [ -z "$(find "$pat" -type f 2>/dev/null)" ]; then
        rm -rf "$pat" 2>/dev/null || true
    fi
done < "$SECRET_FILES_LIST"

# Restore the cut metadata.
mkdir -p "$(dirname "$METADATA_PATH")"
mv "$TEMP_METADATA" "$METADATA_PATH"

echo "[safe_save] Encryption complete."
