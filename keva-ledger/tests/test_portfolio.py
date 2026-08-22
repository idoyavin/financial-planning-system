from __future__ import annotations

from dataclasses import replace

import pytest

from keva_ledger.portfolio import (
    holdings,
    invested,
    net_worth,
    net_worth_change,
    over_cap,
    satellite_share,
    trim_to_cap,
)


def test_net_worth_and_invested_differ_by_the_bank_balance(august):
    assert net_worth(august) == 2994 + 24323 + 786 + 1100
    assert invested(august) == 24323 + 786 + 1100
    assert net_worth(august) - invested(august) == august.bank


def test_satellite_share_measures_against_invested_not_net_worth(august, plan):
    """A fat bank balance must not license a bigger speculative position."""
    share = satellite_share(august)
    assert share == (786 + 1100) / (24323 + 786 + 1100)
    # Measuring against invested is the stricter of the two readings.
    assert share > (786 + 1100) / net_worth(august)
    assert not over_cap(august, plan)


def test_satellite_over_the_cap_is_flagged_and_sized(august, plan):
    hot = replace(august, blink=4000, crypto=3000)
    assert over_cap(hot, plan)
    trim = trim_to_cap(hot, plan)
    trimmed = replace(hot, blink=hot.blink - trim, analyst=hot.analyst + trim)
    assert satellite_share(trimmed) <= plan.sat_cap + 1e-9


def test_nothing_to_trim_when_under_the_cap(august, plan):
    assert trim_to_cap(august, plan) == 0.0


def test_holdings_split_core_from_satellite_and_shares_sum_to_one(august, state):
    rows = holdings(august, state.tickers)
    assert [h.account for h in rows] == ["אנליסט", "Blink", "Crypto"]
    assert [h.kind for h in rows] == ["core", "satellite", "satellite"]
    assert sum(h.share for h in rows) == pytest.approx(1.0)
    assert net_worth_change(august, None) is None
