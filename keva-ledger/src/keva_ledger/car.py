"""The car debt and the sprint that clears it.

₪54,000 owed to family, interest-free. The ₪18,500 מענק lands in November
and goes straight on, leaving ₪35,500 — five payments of ₪7,100 from
December, clearing at the end of April 2027. During the sprint אנליסט
runs at ₪2,500 and Blink pauses; on 1 May 2027 both step back up.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .dates import ym_add
from .models import Month, Plan


def paid_so_far(month: Month, plan: Plan) -> float:
    """How much of the original balance has been cleared."""
    return plan.car_total - month.car_rem


def fraction_paid(month: Month, plan: Plan) -> float:
    """Progress through the debt, 0–1."""
    if plan.car_total <= 0:
        return 1.0
    return paid_so_far(month, plan) / plan.car_total


def is_cleared(month: Month) -> bool:
    return month.car_rem <= 0


def grant_outstanding(month: Month, plan: Plan) -> bool:
    """True while the מענק has yet to land against the balance."""
    return month.car_rem > plan.car_total - plan.grant


def payments_remaining(month: Month, plan: Plan) -> int:
    """Instalments of ₪7,100 still to make.

    While the מענק is outstanding it is netted off first — it is already
    committed, so counting payments against the gross balance would
    overstate what is left to fund out of salary.
    """
    if is_cleared(month):
        return 0
    if plan.car_monthly <= 0:
        raise ValueError("car repayment must be positive")
    balance = month.car_rem
    if grant_outstanding(month, plan):
        balance -= plan.grant
    if balance <= 0:
        return 0
    return math.ceil(balance / plan.car_monthly)


def first_payment_month(month: Month, plan: Plan) -> str:
    """When repayment starts.

    The sprint begins in December 2026 — the months before it are for
    getting the terms in writing and letting the מענק land, not for
    paying. Months compare correctly as plain ``YYYY-MM`` strings.
    """
    return max(ym_add(month.m, 1), plan.sprint_start)


def payoff_month(month: Month, plan: Plan) -> str | None:
    """The month the last instalment clears, or ``None`` if already paid."""
    n = payments_remaining(month, plan)
    if n == 0:
        return None
    return ym_add(first_payment_month(month, plan), n - 1)


@dataclass(frozen=True)
class SprintCost:
    """What the sprint costs against clearing the debt slowly."""

    sprint_contributions: float
    slow_contributions: float

    @property
    def difference(self) -> float:
        """Positive means the sprint puts less into markets over the window."""
        return self.slow_contributions - self.sprint_contributions


def amortise(month: Month, plan: Plan) -> list[tuple[str, float, float]]:
    """The remaining schedule as ``(month, payment, balance after)`` rows."""
    rows: list[tuple[str, float, float]] = []
    balance = month.car_rem
    if grant_outstanding(month, plan):
        balance -= plan.grant
    ym = first_payment_month(month, plan)
    while balance > 0:
        payment = min(plan.car_monthly, balance)
        balance -= payment
        rows.append((ym, payment, max(0.0, balance)))
        ym = ym_add(ym, 1)
    return rows
