"""mosaic-python task-specific checks.

The shared library (/verifier/check_*.py) already covers everything in
the rubric for Python. This file is intentionally tiny; add Python-
specific assertions here if the skill set evolves.
"""
from __future__ import annotations


def test_python_task_check_marker(sdk):
    """Sanity check so the file is picked up by pytest discovery even
    when no Python-specific assertions are added."""
    assert sdk == "python"
