"""Shared helpers for the routing evaluation harness.

Loads skill metadata (name + description) straight from each skill's SKILL.md so
the harness always reflects the real, shipped descriptions rather than a stale
copy. Also loads the labeled prompt corpus and builds the model client.

No upstream secrets are read. The model client authenticates with the caller's
own token via environment variables, so this runs locally on any maintainer's
machine with Copilot / GitHub Models access.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

# Repo root is two levels up from this file: routing-eval/src/common.py
REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"

# The monolith catch-all skill. It is excluded from the "split" arm and included
# in the "all" arm so we can measure how much traffic it absorbs.
MONOLITH_NAME = "cosmosdb-best-practices"


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    directory: str


@dataclass(frozen=True)
class Prompt:
    id: str
    expected_skill: str
    prompt: str
    also_acceptable: tuple[str, ...] = ()


def _parse_frontmatter(skill_md: Path) -> dict:
    """Extract the YAML frontmatter block delimited by the first two '---' lines."""
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{skill_md} does not start with YAML frontmatter")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError(f"{skill_md} frontmatter is not terminated")
    return yaml.safe_load("\n".join(lines[1:end])) or {}


def load_skills(include_monolith: bool) -> list[Skill]:
    """Load every skill's name + description from skills/*/SKILL.md.

    Set include_monolith=False for the "split" arm (the 4 topic skills only),
    True for the "all" arm (topic skills plus the monolith catch-all).
    """
    skills: list[Skill] = []
    for child in sorted(SKILLS_DIR.iterdir()):
        skill_md = child / "SKILL.md"
        if not child.is_dir() or not skill_md.exists():
            continue
        if child.name == MONOLITH_NAME and not include_monolith:
            continue
        fm = _parse_frontmatter(skill_md)
        name = fm.get("name", child.name)
        description = (fm.get("description") or "").strip()
        skills.append(Skill(name=name, description=description, directory=child.name))
    if not skills:
        raise RuntimeError(f"No skills found under {SKILLS_DIR}")
    return skills


def load_prompts(prompts_path: Path) -> list[Prompt]:
    data = yaml.safe_load(prompts_path.read_text(encoding="utf-8")) or {}
    raw = data.get("prompts", [])
    prompts = [
        Prompt(
            id=str(item["id"]),
            expected_skill=str(item["expected_skill"]),
            prompt=str(item["prompt"]),
            also_acceptable=tuple(str(x) for x in item.get("also_acceptable", []) or []),
        )
        for item in raw
    ]
    if not prompts:
        raise RuntimeError(f"No prompts found in {prompts_path}")
    return prompts


def get_model_client():
    """Build an OpenAI-compatible client from environment variables.

    Two backends are supported, chosen automatically:

      * GitHub Models (default): OpenAI-compatible, works locally with a personal
        access token. Note its low input cap (~16k tokens), unsuitable for the
        full-monolith arm of Angle 2.
      * Azure OpenAI: used when ROUTING_EVAL_BASE_URL points at an *.azure.com
        endpoint. Supports large inputs (128k+), needed for the monolith arm.

    Environment variables:
      GITHUB_TOKEN            auth token / api key (required; never committed)
      ROUTING_EVAL_BASE_URL   default https://models.github.ai/inference
                              set to an *.azure.com endpoint to use Azure OpenAI
      ROUTING_EVAL_API_VERSION  Azure only; default 2024-10-21
      ROUTING_EVAL_MODEL      model id / Azure deployment name (or use --model)
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ROUTING_EVAL_TOKEN")
    if not token:
        raise RuntimeError(
            "Set GITHUB_TOKEN (or ROUTING_EVAL_TOKEN) to your model access token. "
            "Nothing is read from repo secrets; this is your own local credential."
        )
    base_url = os.environ.get("ROUTING_EVAL_BASE_URL", "https://models.github.ai/inference")

    if "azure.com" in base_url:
        try:
            from openai import AzureOpenAI
        except ImportError as exc:  # pragma: no cover - guidance only
            raise RuntimeError(
                "The 'openai' package is required. Install with: pip install -r routing-eval/requirements.txt"
            ) from exc
        api_version = os.environ.get("ROUTING_EVAL_API_VERSION", "2024-10-21")
        return AzureOpenAI(azure_endpoint=base_url, api_key=token, api_version=api_version)

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - guidance only
        raise RuntimeError(
            "The 'openai' package is required. Install with: pip install -r routing-eval/requirements.txt"
        ) from exc
    return OpenAI(base_url=base_url, api_key=token)


def default_model() -> str:
    return os.environ.get("ROUTING_EVAL_MODEL", "openai/gpt-4o")
