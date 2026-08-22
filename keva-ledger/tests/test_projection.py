from __future__ import annotations

import pytest

from keva_ledger.portfolio import invested, net_worth
from keva_ledger.projection import (
    contribution_for,
    curve,
    invested_at_contract_end,
    project,
    scenarios,
)


def test_contributions_step_up_the_month_the_sprint_ends(plan):
    assert contribution_for("2027-04", plan) == 2500
    assert contribution_for("2027-05", plan) == 9600
    assert plan.sprint_end == "2027-04"


def test_the_projection_adds_held_cash_on_top_of_compounded_investments(august, plan):
    grown = invested_at_contract_end(august, plan)
    assert grown > invested(august)
    assert project(august, plan) == pytest.approx(grown + plan.emergency_target + plan.pikadon)


def test_a_higher_real_return_lands_higher(august, plan):
    s = scenarios(august, plan)
    assert s.conservative < s.central < s.optimistic
    # At 0% real the total is just contributions plus principal plus cash.
    flat = project(august, plan, 0.0)
    assert flat < s.conservative


def test_the_curve_starts_at_today_and_ends_at_the_contract_end(august, plan):
    pts = curve(august, plan)
    assert pts[0].ym == august.m
    assert pts[0].value == net_worth(august)
    assert pts[-1].ym == plan.contract_end
    assert pts[-1].value == pytest.approx(project(august, plan))
    assert [p.ym for p in pts] == sorted(p.ym for p in pts)
    with pytest.raises(ValueError):
        curve(august, plan, every=0)
