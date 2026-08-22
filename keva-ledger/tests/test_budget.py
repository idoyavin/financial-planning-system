from __future__ import annotations

from keva_ledger.budget import (
    POST_CAR,
    SPRINT,
    fixed_costs,
    phase_for,
    post_car_budget,
    sprint_budget,
)


def test_the_phase_turns_over_on_1_may_2027(plan):
    assert phase_for("2027-04", plan) == SPRINT
    assert phase_for("2027-05", plan) == POST_CAR
    assert fixed_costs(plan) == 2500 + 241 + 400 + 611


def test_the_sprint_puts_the_car_first_and_pauses_blink(plan):
    b = sprint_budget(plan)
    lines = {ln.label: ln.amount for ln in b.lines}
    assert lines["Car repayment"] == -7100
    assert lines["אנליסט"] == -2500
    assert lines["Blink"] == 0.0
    assert b.invested == 2500
    assert b.unallocated == 14000 - fixed_costs(plan) - 7100 - 2500 - 648


def test_the_freed_car_payment_goes_straight_into_the_market(plan):
    sprint, after = sprint_budget(plan), post_car_budget(plan)
    lines = {ln.label: ln.amount for ln in after.lines}
    assert lines["Car repayment"] == 0.0
    assert lines["אנליסט"] == -9000
    assert lines["Blink"] == -600
    assert after.invested == 9600
    # The ₪7,100 does not become slack — it moves across to investment intact.
    assert after.invested - sprint.invested == 7100
    assert after.unallocated == sprint.unallocated
    assert after.income == 14000
