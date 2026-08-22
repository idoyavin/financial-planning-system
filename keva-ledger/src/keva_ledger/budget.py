"""The monthly standing order, in both phases.

December 2026 → April 2027 the car comes first. From May 2027 the ₪7,100
stops and אנליסט steps up to ₪9,000 with ₪600 back to Blink — the same
day, so the freed money never gets a month to find other uses.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Plan

SPRINT = "sprint"
POST_CAR = "post-car"


@dataclass(frozen=True)
class Line:
    """One line of the monthly budget. Outflows are negative."""

    label: str
    amount: float


@dataclass(frozen=True)
class Budget:
    """A month's allocation, and whatever it fails to allocate."""

    phase: str
    lines: list[Line]

    @property
    def income(self) -> float:
        return sum(line.amount for line in self.lines if line.amount > 0)

    @property
    def outflow(self) -> float:
        """Total committed, as a positive number."""
        return -sum(line.amount for line in self.lines if line.amount < 0)

    @property
    def unallocated(self) -> float:
        """What the plan does not speak for — the slack in the month."""
        return sum(line.amount for line in self.lines)

    @property
    def invested(self) -> float:
        """What goes into markets this month."""
        return sum(
            -line.amount
            for line in self.lines
            if line.amount < 0 and line.label in ("אנליסט", "Blink")
        )


def phase_for(ym: str, plan: Plan) -> str:
    """Which side of the sprint ``ym`` falls on."""
    return SPRINT if ym <= plan.sprint_end else POST_CAR


def fixed_costs(plan: Plan) -> float:
    """Living, fuel, service and the insurance fund — the unavoidable floor."""
    return plan.living + plan.fuel + plan.service + plan.ins_fund


def budget_for(ym: str, plan: Plan) -> Budget:
    """The standing order for ``ym``."""
    phase = phase_for(ym, plan)
    in_sprint = phase == SPRINT

    lines = [
        Line("Net salary", plan.salary),
        Line("Living", -plan.living),
        Line("דלק", -plan.fuel),
        Line("טסט, service, repairs", -plan.service),
        Line("Insurance sinking fund", -plan.ins_fund),
        Line("Car repayment", -(plan.car_monthly if in_sprint else 0.0)),
        Line("אנליסט", -(plan.analyst_sprint if in_sprint else plan.analyst_full)),
        Line("Blink", -(0.0 if in_sprint else plan.satellite)),
        Line("Cash / irregulars", -plan.cash_alloc),
    ]
    return Budget(phase=phase, lines=lines)


def sprint_budget(plan: Plan) -> Budget:
    """The December→April allocation."""
    return budget_for(plan.sprint_end, plan)


def post_car_budget(plan: Plan) -> Budget:
    """The allocation from May 2027 onward."""
    from .dates import ym_add

    return budget_for(ym_add(plan.sprint_end, 1), plan)
