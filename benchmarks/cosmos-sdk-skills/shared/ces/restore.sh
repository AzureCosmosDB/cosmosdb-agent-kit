#!/bin/bash
set -e

# Check if required arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <encryption-key> <encrypted-file>" >&2
    exit 1
fi

# Check if encrypted file exists
if [ ! -f "$2" ]; then
    echo "Error: $2 not found" >&2
    exit 1
fi

# Determine filesystem root (same logic as save.sh)
if [ -d "/c/Windows" ]; then
    SCAN_ROOT="/c/"
else
    SCAN_ROOT="/"
fi

# Decrypt and extract the tarball
echo "Decrypting and extracting the tarball..."
cd "$SCAN_ROOT"
if ! openssl enc -d -aes-256-cbc -salt -pbkdf2 -pass "pass:$1" -in "$2" 2>/dev/null | tar -xzvf -; then
    echo "Error: Failed to decrypt or extract files (incorrect key?)" >&2
    exit 1
fi

# Remove the encrypted file
rm "$2" 2>/dev/null
