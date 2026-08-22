"""Year-month arithmetic.

Every date in the ledger is a ``YYYY-MM`` string. Months are the natural
grain here: salary lands monthly, the car is repaid monthly, insurance
falls due in whole months. Days would be false precision.
"""

from __future__ import annotations

MONTHS_SHORT = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

MONTHS_LONG = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def parse_ym(ym: str) -> tuple[int, int]:
    """Split ``YYYY-MM`` into ``(year, month)``, rejecting anything else."""
    parts = ym.split("-")
    if len(parts) != 2:
        raise ValueError(f"expected YYYY-MM, got {ym!r}")
    year_s, month_s = parts
    if len(year_s) != 4 or len(month_s) != 2:
        raise ValueError(f"expected YYYY-MM, got {ym!r}")
    try:
        year, month = int(year_s), int(month_s)
    except ValueError:
        raise ValueError(f"expected YYYY-MM, got {ym!r}") from None
    if not 1 <= month <= 12:
        raise ValueError(f"month out of range in {ym!r}")
    return year, month


def ym_add(ym: str, k: int) -> str:
    """Return the month ``k`` months after ``ym`` (``k`` may be negative)."""
    year, month = parse_ym(ym)
    total = year * 12 + (month - 1) + k
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def ym_diff(a: str, b: str) -> int:
    """Whole months from ``a`` to ``b``. Negative when ``b`` precedes ``a``."""
    ay, am = parse_ym(a)
    by, bm = parse_ym(b)
    return (by - ay) * 12 + (bm - am)


def ym_label(ym: str) -> str:
    """Short label for axes and tables: ``Aug '26``."""
    year, month = parse_ym(ym)
    return f"{MONTHS_SHORT[month - 1]} '{str(year)[2:]}"


def ym_long(ym: str) -> str:
    """Prose label: ``August 2026``."""
    year, month = parse_ym(ym)
    return f"{MONTHS_LONG[month - 1]} {year}"


def ym_range(start: str, end: str) -> list[str]:
    """Every month from ``start`` to ``end`` inclusive; empty if end < start."""
    n = ym_diff(start, end)
    if n < 0:
        return []
    return [ym_add(start, i) for i in range(n + 1)]
