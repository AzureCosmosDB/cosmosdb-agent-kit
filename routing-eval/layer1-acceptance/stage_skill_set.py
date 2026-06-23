"""Stage an isolated skills directory for one Layer 1 arm (non-destructive).

Layer 1 compares the monolith baseline against the split candidate by controlling
WHICH skills an agent can see per run. This helper copies the relevant skill
folders into a fresh output directory. The real skills/ folder is never modified
or deleted; you point the agent runtime at the staged root for that arm.

Arms:
  --arm monolith   copy only cosmosdb-best-practices (baseline; no routing choice)
  --arm split      copy only the 4 topic skills (candidate; agent must route)

Example:
  python routing-eval/layer1-acceptance/stage_skill_set.py --arm monolith --out .tmp/skills-monolith
  python routing-eval/layer1-acceptance/stage_skill_set.py --arm split    --out .tmp/skills-split
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Reuse the skill loader / constants from the Layer 2 helper.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import common  # noqa: E402


def stage(arm: str, out_dir: Path) -> list[str]:
    if arm == "monolith":
        wanted = {common.MONOLITH_NAME}
    else:  # split
        wanted = {
            child.name
            for child in common.SKILLS_DIR.iterdir()
            if child.is_dir() and (child / "SKILL.md").exists() and child.name != common.MONOLITH_NAME
        }

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    copied = []
    for name in sorted(wanted):
        src = common.SKILLS_DIR / name
        dst = out_dir / name
        shutil.copytree(src, dst)
        copied.append(name)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage an isolated skills root for a Layer 1 arm.")
    parser.add_argument("--arm", choices=["monolith", "split"], required=True)
    parser.add_argument("--out", required=True, help="output directory for the staged skills root")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    # Safety: never allow staging on top of the real skills/ directory.
    if out_dir == common.SKILLS_DIR.resolve():
        print("Refusing to stage onto the real skills/ directory.", file=sys.stderr)
        return 1

    copied = stage(args.arm, out_dir)
    print(f"Staged arm '{args.arm}' -> {out_dir}")
    print(f"Copied {len(copied)} skill(s):")
    for name in copied:
        print(f"  {name}")
    print("\nThe real skills/ directory was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
