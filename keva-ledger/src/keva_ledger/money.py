"""Shekel formatting.

Amounts are carried as floats because they come from bank and broker
figures that are already rounded, and every published number is rounded
again for display. Nothing here settles a payment, so cent-exact decimal
arithmetic would buy precision the inputs do not have.
"""

from __future__ import annotations

SHEKEL = "₪"


def shekels(amount: float) -> str:
    """Whole shekels with thousands separators: ``₪14,000``."""
    return f"{SHEKEL}{round(amount):,}"


def shekels_exact(amount: float) -> str:
    """Two decimal places, for bills that arrive to the agora: ``₪308.75``."""
    return f"{SHEKEL}{amount:,.2f}"


def percent(fraction: float, digits: int = 1) -> str:
    """Format a 0–1 fraction as a percentage: ``0.075`` becomes ``7.5%``."""
    return f"{fraction * 100:.{digits}f}%"


def signed(amount: float) -> str:
    """Shekels with an explicit sign, for month-on-month deltas.

    The sign leads the currency mark — ``-₪1,200`` rather than ``₪-1,200``,
    which reads as a negative currency rather than a fall.
    """
    return ("+" if amount >= 0 else "-") + shekels(abs(amount))
