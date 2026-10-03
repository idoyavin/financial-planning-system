"""Where the plan lands by the end of the contract.

Compounds what is invested today forward to March 2031 at a real rate,
adding the monthly contribution that applies in each month — ₪2,500 while
the sprint runs, ₪9,600 once the car is paid off. The emergency fund and
the פיקדון are added at the end as cash: they are held, not invested, so
compounding them would flatter the result.

The assumptions stay deliberately plain — no raises, no קרן השתלמות, no
pension, satellite contributions valued at cost. Every one is upside left
out rather than optimism built in.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dates import ym_add, ym_diff
from .models import Month, Plan


def contribution_for(ym: str, plan: Plan) -> float:
    """The monthly investment in ``ym``: sprint rate, or full rate plus satellite."""
    if ym <= plan.sprint_end:
        return plan.analyst_sprint
    return plan.analyst_full + plan.satellite


def invested_at_contract_end(month: Month, plan: Plan, rate: float | None = None) -> float:
    """Compound the invested balance forward to the contract end."""
    r = (plan.real_return if rate is None else rate) / 12
    value = month.analyst + month.blink + month.crypto
    ym = month.m
    for _ in range(max(0, ym_diff(month.m, plan.contract_end))):
        ym = ym_add(ym, 1)
        value = value * (1 + r) + contribution_for(ym, plan)
    return value


def project(month: Month, plan: Plan, rate: float | None = None) -> float:
    """Total net worth at the contract end: investments plus held cash."""
    return invested_at_contract_end(month, plan, rate) + plan.emergency_target + plan.pikadon


@dataclass(frozen=True)
class Point:
    """One point on the projection curve."""

    ym: str
    value: float


def curve(month: Month, plan: Plan, every: int = 6, rate: float | None = None) -> list[Point]:
    """The projection sampled every ``every`` months, always including the end.

    The first point is today's net worth — investments plus the bank
    balance — so the curve starts where the net-worth chart leaves off.
    """
    if every <= 0:
        raise ValueError("sampling interval must be positive")
    r = (plan.real_return if rate is None else rate) / 12
    value = month.analyst + month.blink + month.crypto
    points = [Point(month.m, value + month.bank)]

    n = max(0, ym_diff(month.m, plan.contract_end))
    ym = month.m
    for i in range(n):
        ym = ym_add(ym, 1)
        value = value * (1 + r) + contribution_for(ym, plan)
        if (i + 1) % every == 0 or i == n - 1:
            points.append(Point(ym, value + plan.emergency_target + plan.pikadon))
    return points


@dataclass(frozen=True)
class Scenarios:
    """The three rates the dashboard shows side by side."""

    conservative: float
    central: float
    optimistic: float


def scenarios(
    month: Month,
    plan: Plan,
    low: float = 0.04,
    high: float = 0.08,
) -> Scenarios:
    """Projections at 4%, the plan's own rate, and 8% real."""
    return Scenarios(
        conservative=project(month, plan, low),
        central=project(month, plan),
        optimistic=project(month, plan, high),
    )
