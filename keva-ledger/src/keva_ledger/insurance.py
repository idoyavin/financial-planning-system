"""The insurance sinking fund.

Two policies bill on different rhythms. חובה is spread over eight
instalments running August→March. מקיף is paid in one lump in November
2026, and from 2027 over three instalments in August, September and
October. ₪611 a month goes into a separate account so neither bill has to
be found out of a single month's salary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .dates import parse_ym, ym_add
from .models import Plan

HOVA_MONTHS = (8, 9, 10, 11, 12, 1, 2, 3)
MAKIF_MONTHS = (8, 9, 10)
MAKIF_LUMP_YEAR = 2026
MAKIF_LUMP_MONTH = 11


@dataclass(frozen=True)
class Due:
    """What falls due in a single month."""

    makif: float = 0.0
    hova: float = 0.0

    @property
    def total(self) -> float:
        return self.makif + self.hova

    def __bool__(self) -> bool:
        return self.total > 0


def due_in(ym: str, plan: Plan) -> Due:
    """The premiums falling due in ``ym``."""
    year, month = parse_ym(ym)
    hova = plan.hova_year / plan.hova_n if month in HOVA_MONTHS else 0.0

    makif = 0.0
    if year == MAKIF_LUMP_YEAR and month == MAKIF_LUMP_MONTH:
        makif = plan.makif_year
    elif year > MAKIF_LUMP_YEAR and month in MAKIF_MONTHS:
        makif = plan.makif_year / plan.makif_n

    return Due(makif=makif, hova=hova)


@dataclass(frozen=True)
class NextDue:
    """The next month carrying a bill, and what it comes to."""

    ym: str
    due: Due


def next_due(from_ym: str, plan: Plan, horizon: int = 14) -> NextDue | None:
    """The first month after ``from_ym`` with anything due, within ``horizon``."""
    for i in range(1, horizon + 1):
        ym = ym_add(from_ym, i)
        d = due_in(ym, plan)
        if d.total > 0:
            return NextDue(ym=ym, due=d)
    return None


def schedule(from_ym: str, plan: Plan, months: int = 12) -> list[tuple[str, Due]]:
    """Each of the next ``months`` months paired with what falls due."""
    return [(ym_add(from_ym, k), due_in(ym_add(from_ym, k), plan)) for k in range(1, months + 1)]


def twelve_month_total(from_ym: str, plan: Plan) -> float:
    """Everything due over the coming year."""
    return sum(d.total for _, d in schedule(from_ym, plan, 12))


def coverage(pot: float, nxt: NextDue | None) -> float:
    """Fraction of the next bill already sitting in the pot, capped at 1.

    With nothing due, the pot is trivially sufficient.
    """
    if nxt is None or nxt.due.total <= 0:
        return 1.0
    return min(1.0, pot / nxt.due.total)


def months_to_cover(pot: float, nxt: NextDue | None, plan: Plan) -> int:
    """Months of ₪611 contributions needed to close the gap on the next bill."""
    if nxt is None:
        return 0
    gap = nxt.due.total - pot
    if gap <= 0:
        return 0
    if plan.ins_fund <= 0:
        raise ValueError("insurance contribution must be positive")
    return math.ceil(gap / plan.ins_fund)
