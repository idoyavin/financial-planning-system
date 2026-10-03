from __future__ import annotations

from keva_ledger.money import percent, shekels, shekels_exact, signed


def test_shekels_rounds_and_separates_thousands():
    assert shekels(14000) == "₪14,000"
    assert shekels(2356.6) == "₪2,357"


def test_shekels_exact_keeps_the_agorot():
    """חובה instalments come to ₪308.75 — the pot has to match the bill."""
    assert shekels_exact(2470 / 8) == "₪308.75"


def test_percent_honours_requested_digits():
    assert percent(0.0721) == "7.2%"
    assert percent(0.1, 0) == "10%"


def test_signed_marks_gains_explicitly():
    assert signed(1200) == "+₪1,200"
    assert signed(-1200) == "-₪1,200"
