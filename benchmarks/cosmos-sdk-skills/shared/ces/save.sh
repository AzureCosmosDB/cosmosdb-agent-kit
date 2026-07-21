#!/bin/bash
set -e

# Check if required arguments are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 <key> <path-to-glob-list-file> <path-to-metadata-key-list-file> <output-enc-file>"
    exit 1
fi

KEY="$1"
SECRET_FILES_LIST="$2"
KEEP_METADATA_FILE="$3"
OUTPUT_FILE="$4"

# Resolve script directory for finding companion scripts (glob_files.py, cut_metadata.py)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# On Windows, Python is a native Windows binary that doesn't understand MSYS/Unix paths
# (especially with MSYS_NO_PATHCONV=1). Convert SCRIPT_DIR for Python calls.
if [ -d "/c/Windows" ]; then
    SCRIPT_DIR_PY="$(cygpath -w "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR")"
else
    SCRIPT_DIR_PY="$SCRIPT_DIR"
fi

# Check if glob list file exists
if [ ! -f "$SECRET_FILES_LIST" ]; then
    echo "Error: Glob list file '$SECRET_FILES_LIST' not found"
    exit 1
fi

# Create temporary file for storing file list
TEMP_LIST=$(mktemp)

# Activate Python environment if available (Linux containers with conda/venv)
# On Windows, Python is already in PATH from the base image
if [ -f /opt/activate_python.sh ]; then
    . /opt/activate_python.sh
fi

# Add vendored python-pathspec to PYTHONPATH (used by glob_files.py)
if [ -d "$SCRIPT_DIR/python-pathspec" ]; then
    if [ -d "/c/Windows" ]; then
        PY_PATHSPEC="$(cygpath -w "$SCRIPT_DIR/python-pathspec" 2>/dev/null || echo "$SCRIPT_DIR/python-pathspec")"
        export PYTHONPATH="$PY_PATHSPEC${PYTHONPATH:+;$PYTHONPATH}"
    else
        export PYTHONPATH="$SCRIPT_DIR/python-pathspec${PYTHONPATH:+:$PYTHONPATH}"
    fi
fi

# Determine filesystem root for glob scanning
# On Windows (MSYS/Git Bash), "/" is the Git install dir, not the drive root.
# Use /c/ (the C: drive) when running on Windows.
if [ -d "/c/Windows" ]; then
    SCAN_ROOT="/c/"
else
    SCAN_ROOT="/"
fi

# On Windows, convert all path arguments to Windows format for Python calls
# (Python is a native Windows binary that doesn't understand /c/ paths,
#  and MSYS_NO_PATHCONV=1 prevents automatic conversion)
if [ -d "/c/Windows" ]; then
    PY_SECRET_FILES_LIST="$(cygpath -w "$SECRET_FILES_LIST")"
    PY_TEMP_LIST="$(cygpath -w "$TEMP_LIST")"
    PY_SCAN_ROOT="$(cygpath -w "$SCAN_ROOT")"
    PY_KEEP_METADATA_FILE="$(cygpath -w "$KEEP_METADATA_FILE")"
    PY_METADATA_PATH="$(cygpath -w "$METADATA_PATH")"
else
    PY_SECRET_FILES_LIST="$SECRET_FILES_LIST"
    PY_TEMP_LIST="$TEMP_LIST"
    PY_SCAN_ROOT="$SCAN_ROOT"
    PY_KEEP_METADATA_FILE="$KEEP_METADATA_FILE"
    PY_METADATA_PATH="$METADATA_PATH"
fi

python "$SCRIPT_DIR_PY/glob_files.py" "$PY_SECRET_FILES_LIST" "$PY_TEMP_LIST" "$PY_SCAN_ROOT"

# Cut secrets out of metadata file
TEMP_METADATA="$(mktemp)"
if [ -d "/c/Windows" ]; then
    PY_TEMP_METADATA="$(cygpath -w "$TEMP_METADATA")"
else
    PY_TEMP_METADATA="$TEMP_METADATA"
fi
python "$SCRIPT_DIR_PY/cut_metadata.py" "$PY_KEEP_METADATA_FILE" "$PY_METADATA_PATH" "$PY_TEMP_METADATA"

echo "Files to encrypt:"
echo "$SECRET_FILES_LIST" >> "$TEMP_LIST"
cat "$TEMP_LIST"

# Create tarball of all matched files and encrypt it, redirecting any messages to stderr
cd "$SCAN_ROOT"
tar -czf - -T "$TEMP_LIST" | openssl enc -aes-256-cbc -salt -pbkdf2 -pass "pass:$KEY" -out "$OUTPUT_FILE"

# Remove the original files
TEMP_TEMP_LIST="$(mktemp)"
head -n -1 "$TEMP_LIST" > "$TEMP_TEMP_LIST"
mv "$TEMP_TEMP_LIST" "$TEMP_LIST"
cat "$TEMP_LIST" | while IFS= read -r file; do
    rm -f "${SCAN_ROOT%/}/$file"
done
# Remove directories if they are empty
cat "$SECRET_FILES_LIST" | while IFS= read -r file; do
    if [ -d "${SCAN_ROOT%/}/$file" ]; then
        # Check if directory is empty or only contains directories
        if [ -z "$(find "${SCAN_ROOT%/}/$file" -type f)" ]; then
            rm -r "${SCAN_ROOT%/}/$file" 2>/dev/null || true
        fi
    fi
done

# Restore cut metadata
mkdir -p "$(dirname "$METADATA_PATH")"
mv "$TEMP_METADATA" "$METADATA_PATH"

# Cleanup
rm -f "$SECRET_FILES_LIST"
rm -f "$TEMP_LIST"

echo "Encryption complete."