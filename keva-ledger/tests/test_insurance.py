from __future__ import annotations

import pytest

from keva_ledger.insurance import (
    coverage,
    due_in,
    months_to_cover,
    next_due,
    schedule,
    twelve_month_total,
)


def test_hova_is_spread_over_eight_instalments(plan):
    """August→March, ₪2,470 a year, ₪308.75 a time."""
    assert due_in("2026-09", plan).hova == pytest.approx(308.75)
    assert due_in("2027-03", plan).hova == pytest.approx(308.75)
    assert due_in("2027-04", plan).hova == 0
    assert due_in("2027-07", plan).hova == 0


def test_makif_is_a_lump_in_2026_then_thirds(plan):
    assert due_in("2026-11", plan).makif == 4857
    assert due_in("2026-08", plan).makif == 0
    assert due_in("2027-08", plan).makif == pytest.approx(4857 / 3)
    assert due_in("2027-11", plan).makif == 0


def test_november_2026_is_the_year_that_bites(plan):
    """The מקיף lump and a חובה instalment fall in the same month."""
    nov = due_in("2026-11", plan)
    assert nov.total == pytest.approx(4857 + 308.75)
    assert bool(nov)
    assert not bool(due_in("2027-06", plan))


def test_next_due_finds_the_first_month_carrying_a_bill(plan):
    nxt = next_due("2026-08", plan)
    assert nxt is not None
    assert nxt.ym == "2026-09"
    assert nxt.due.total == pytest.approx(308.75)


def test_the_twelve_months_after_baseline_total_a_full_year(plan):
    rows = schedule("2026-08", plan, 12)
    assert len(rows) == 12
    assert rows[0][0] == "2026-09"
    # Sep→Mar and the following August give eight חובה instalments; the
    # מקיף lump lands in November and the first 2027 third in August.
    assert twelve_month_total("2026-08", plan) == pytest.approx(8 * 308.75 + 4857 + 4857 / 3)


def test_an_empty_pot_is_uncovered_and_the_gap_is_counted_in_months(plan, august):
    nxt = next_due(august.m, plan)
    assert coverage(august.ins_pot, nxt) == 0.0
    assert months_to_cover(august.ins_pot, nxt, plan) == 1
    assert coverage(400, nxt) == 1.0
    assert months_to_cover(400, nxt, plan) == 0
    assert coverage(0, None) == 1.0
