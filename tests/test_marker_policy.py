"""Guard the opt-in marker policy in pyproject.toml.

Default runs must deselect every opt-in external marker. These tests pin
the addopts deselection expression and prove end-to-end that a marker-
annotated test is deselected by default and selectable via ``-m``, so an
accidental edit to addopts cannot silently re-enable live tests in CI.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

OPT_IN_MARKERS = (
    "external",
    "network",
    "live_llm",
    "gpu",
    "ssh",
    "lab",
    "docker",
    "browser",
)


def _addopts() -> str:
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"^addopts\s*=\s*'(.*)'\s*$", text, flags=re.MULTILINE)
    assert match, "addopts line not found in pyproject.toml"
    return match.group(1)


def test_addopts_deselects_every_opt_in_marker():
    addopts = _addopts()
    assert "--strict-markers" in addopts
    for marker in OPT_IN_MARKERS:
        assert re.search(rf"\bnot {marker}\b", addopts), (
            f"opt-in marker {marker!r} is no longer deselected by default "
            "addopts — live/external tests would run in the default CI gate"
        )


def _collect(*extra_args: str) -> str:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "tests/test_methodology_skills.py",
            *extra_args,
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout


def test_marked_live_test_deselected_by_default_and_opt_in_selectable():
    live_test = "test_methodology_skill_used_in_agent_loop"
    default_out = _collect()
    assert live_test not in default_out
    assert "deselected" in default_out
    opt_in_out = _collect("-m", "live_llm")
    assert live_test in opt_in_out
