from __future__ import annotations

from dataclasses import replace

from keva_ledger.spending import (
    breakdown,
    is_over_target,
    rolling_core,
    spend_core,
    spend_total,
    surplus,
    variance,
)


def test_transfers_are_excluded_from_core_spending(august):
    """bit payments leave the card and come back within days."""
    assert spend_total(august) == 1321 + 387 + 241 + 124 + 107 + 244
    assert spend_core(august) == spend_total(august) - 387
    assert spend_core(august) == 2037


def test_august_came_in_under_target(august, plan):
    assert variance(august, plan) == 2037 - 2500
    assert not is_over_target(august, plan)
    assert surplus(august, plan) == 14000 - 2037


def test_going_over_target_is_flagged(august, plan):
    blowout = replace(august, spend={**august.spend, "shopping": 1500})
    assert is_over_target(blowout, plan)
    assert variance(blowout, plan) > 0


def test_breakdown_is_ordered_and_marks_what_sits_outside_the_target(august):
    rows = breakdown(august)
    assert [r.amount for r in rows] == sorted((r.amount for r in rows), reverse=True)
    assert rows[0].key == "food"
    assert {r.key for r in rows if not r.counts_to_target} == {"transfers"}
    assert rolling_core([august], window=3) is None
