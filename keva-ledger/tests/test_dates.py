from __future__ import annotations

import pytest

from keva_ledger.dates import parse_ym, ym_add, ym_diff, ym_label, ym_long, ym_range


def test_parse_ym_splits_year_and_month():
    assert parse_ym("2026-08") == (2026, 8)


@pytest.mark.parametrize("bad", ["2026-13", "2026-8", "August"])
def test_parse_ym_rejects_malformed_input(bad):
    with pytest.raises(ValueError):
        parse_ym(bad)


def test_ym_add_rolls_over_the_year_boundary_in_both_directions():
    assert ym_add("2026-08", 3) == "2026-11"
    assert ym_add("2026-11", 2) == "2027-01"
    assert ym_add("2026-08", 55) == "2031-03"
    assert ym_add("2027-01", -2) == "2026-11"
    assert ym_add("2027-01", -13) == "2025-12"


def test_ym_diff_counts_whole_months_in_both_directions():
    assert ym_diff("2026-08", "2031-03") == 55
    assert ym_diff("2027-01", "2026-11") == -2
    assert ym_add("2026-08", ym_diff("2026-08", "2029-02")) == "2029-02"


def test_labels_render_short_and_long():
    assert ym_label("2026-08") == "Aug '26"
    assert ym_long("2031-03") == "March 2031"


def test_ym_range_is_inclusive_and_empty_when_reversed():
    assert ym_range("2026-11", "2027-02") == ["2026-11", "2026-12", "2027-01", "2027-02"]
    assert ym_range("2027-02", "2026-11") == []


def test_month_strings_sort_chronologically():
    """The ledger compares months as plain strings — sprint_end, contract_end."""
    months = ["2027-01", "2026-09", "2026-12", "2026-08"]
    assert sorted(months) == ["2026-08", "2026-09", "2026-12", "2027-01"]
