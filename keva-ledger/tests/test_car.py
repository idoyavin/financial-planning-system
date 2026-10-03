from __future__ import annotations

from dataclasses import replace

from keva_ledger.car import (
    amortise,
    first_payment_month,
    fraction_paid,
    grant_outstanding,
    is_cleared,
    payments_remaining,
    payoff_month,
)


def test_nothing_is_paid_at_the_baseline(august, plan):
    assert august.car_rem == plan.car_total
    assert fraction_paid(august, plan) == 0.0
    assert not is_cleared(august)
    assert grant_outstanding(august, plan)


def test_the_grant_is_netted_off_before_counting_payments(august, plan):
    """₪54,000 less the ₪18,500 מענק is ₪35,500 — five payments of ₪7,100."""
    assert payments_remaining(august, plan) == 5
    # Repayment starts in December, not the month after the baseline.
    assert first_payment_month(august, plan) == "2026-12"
    assert payoff_month(august, plan) == "2027-04"


def test_once_the_grant_has_landed_it_is_not_netted_twice(plan, august):
    after_grant = replace(august, m="2026-11", car_rem=35500)
    assert not grant_outstanding(after_grant, plan)
    assert payments_remaining(after_grant, plan) == 5
    assert payoff_month(after_grant, plan) == "2027-04"


def test_a_cleared_debt_reports_nothing_outstanding(paid_off, plan):
    assert is_cleared(paid_off)
    assert payments_remaining(paid_off, plan) == 0
    assert payoff_month(paid_off, plan) is None
    assert fraction_paid(paid_off, plan) == 1.0


def test_the_schedule_amortises_to_exactly_zero(august, plan):
    rows = amortise(august, plan)
    assert len(rows) == payments_remaining(august, plan)
    assert rows[0][0] == "2026-12"
    assert rows[-1][0] == "2027-04"
    assert rows[-1][2] == 0
    assert sum(payment for _, payment, _ in rows) == 35500
    # The final instalment is the stub left after four full payments.
    assert rows[-1][1] == 35500 - 4 * plan.car_monthly
