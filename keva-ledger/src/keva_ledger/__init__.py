"""Keva Ledger — a small ledger for one financial plan.

קבע: the standing order, the thing that runs every month whether or not
anyone is watching. Log a month and every figure moves with it.
"""

from __future__ import annotations

from pathlib import Path

from .models import Month, Plan, State, Task

__all__ = ["Month", "Plan", "State", "Task", "DEFAULT_STATE_PATH", "load_state", "__version__"]

__version__ = "0.1.0"

# One state file feeds the Python package, the tests and the website, so a
# month logged anywhere shows up everywhere. It lives at the repository root
# rather than inside this package because the site and finsys read it too.
DEFAULT_STATE_PATH = Path(__file__).resolve().parents[3] / "data" / "state.json"


def load_state(path: str | Path | None = None) -> State:
    """Load the ledger, defaulting to the repository's ``data/state.json``."""
    return State.load(path or DEFAULT_STATE_PATH)
