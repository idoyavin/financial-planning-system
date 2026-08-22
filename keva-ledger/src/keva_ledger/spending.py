"""Spending against target.

bit and PAYBOX transfers leave the card and come back within days — you
front the restaurant table and friends settle up. They inflate the
statement without being consumption, so the target measures core spending
and leaves transfers outside it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import CATEGORY_LABELS, Month, Plan


def spend_total(month: Month) -> float:
    """Everything that hit the card."""
    return sum(month.spend.values())


def spend_core(month: Month) -> float:
    """The card total less bit transfers — what was actually consumed."""
    return spend_total(month) - month.spend.get("transfers", 0.0)


def variance(month: Month, plan: Plan) -> float:
    """Core spending less target. Positive is over, negative is under."""
    return spend_core(month) - plan.spend_target


def is_over_target(month: Month, plan: Plan) -> bool:
    return variance(month, plan) > 0


@dataclass(frozen=True)
class CategoryLine:
    """One row of the spending table."""

    key: str
    label: str
    amount: float
    share: float
    counts_to_target: bool


def breakdown(month: Month) -> list[CategoryLine]:
    """Categories largest first, each as a share of the card total."""
    total = spend_total(month)
    lines = [
        CategoryLine(
            key=key,
            label=CATEGORY_LABELS.get(key, key),
            amount=amount,
            share=amount / total if total else 0.0,
            counts_to_target=key != "transfers",
        )
        for key, amount in month.spend.items()
    ]
    return sorted(lines, key=lambda c: c.amount, reverse=True)


def surplus(month: Month, plan: Plan) -> float:
    """What is left of the salary after core spending — the amount free to invest."""
    return plan.salary - spend_core(month)


def rolling_core(months: list[Month], window: int = 3) -> float | None:
    """Mean core spending over the last ``window`` months.

    One month over target is noise; a run of them is a signal. Returns
    ``None`` until there are enough months to say anything.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if len(months) < window:
        return None
    recent = months[-window:]
    return sum(spend_core(m) for m in recent) / window
