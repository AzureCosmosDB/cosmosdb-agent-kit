from pathspec import PathSpec
import sys
import os
import json

# Read patterns from glob list file
with open(sys.argv[1]) as f:
    patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
patterns.append("!/save.sh")
patterns.append("!/restore.sh")
print("Patterns:", patterns)

# Create gitignore-style spec
spec = PathSpec.from_lines("gitwildmatch", patterns)

# Determine scan root: use argv[3] if provided, else "/"
scan_root = sys.argv[3] if len(sys.argv) > 3 else "/"

# Linux kernel virtual filesystems: pathspec.match_tree() walks every
# child, and inside /proc/sys/... there are sysctl pseudo-files whose
# d_type lies (a non-directory marked as a directory), which makes
# os.scandir blow up with NotADirectoryError. We also have no reason
# to scan /sys, /dev, /run, /boot when looking for benchmark secrets.
# These names are pruned only at the top of the scan root.
SKIP_TOP_LEVEL = {"proc", "sys", "dev", "run", "boot"}


def _iter_files(root: str):
    """Walk root with os.walk, tolerate fs errors, prune kernel pseudo-FS."""
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(
        root, followlinks=False, onerror=lambda e: print(f"[glob_files] ignoring {e}", file=sys.stderr)
    ):
        if dirpath == root:
            dirnames[:] = [d for d in dirnames if d not in SKIP_TOP_LEVEL]
        for fn in filenames:
            yield os.path.relpath(os.path.join(dirpath, fn), root)


with open(sys.argv[2], "w", newline="\n") as of:
    for rel in _iter_files(scan_root):
        # gitwildmatch patterns like "/tests" anchor at the scan root,
        # which is what `spec.match_file("tests/foo.py")` already enforces.
        if spec.match_file(rel):
            print(rel.replace("\\", "/"), file=of)
