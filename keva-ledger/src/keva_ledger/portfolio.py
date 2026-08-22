"""Net worth and the core/satellite split.

אנליסט tracking ^SPX is the core. Blink and crypto are the satellite, and
they are capped as a share of what is invested — not of net worth — so a
fat bank balance can never quietly license a bigger speculative position.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Month, Plan


def net_worth(month: Month) -> float:
    """Bank plus every investment account."""
    return month.bank + month.analyst + month.blink + month.crypto


def invested(month: Month) -> float:
    """Everything held in markets — net worth less the bank balance."""
    return month.analyst + month.blink + month.crypto


def satellite_value(month: Month) -> float:
    """Blink plus crypto: the speculative sleeve."""
    return month.blink + month.crypto


def satellite_share(month: Month) -> float:
    """Satellite as a fraction of invested capital. Zero when nothing is invested."""
    total = invested(month)
    return satellite_value(month) / total if total else 0.0


def over_cap(month: Month, plan: Plan) -> bool:
    """True when the satellite sleeve has grown past its cap."""
    return satellite_share(month) > plan.sat_cap


def trim_to_cap(month: Month, plan: Plan) -> float:
    """Shekels to move satellite→core to return to the cap. Zero when under it.

    Selling ``x`` leaves ``sat - x`` over an unchanged total, so the amount
    that lands exactly on the cap is ``sat - cap * invested``.
    """
    excess = satellite_value(month) - plan.sat_cap * invested(month)
    return max(0.0, excess)


@dataclass(frozen=True)
class Holding:
    """One line of the portfolio table."""

    account: str
    kind: str
    value: float
    share: float
    holdings: list[str]


def holdings(month: Month, tickers: dict[str, list[str]]) -> list[Holding]:
    """The portfolio broken into its three accounts, largest share first."""
    total = invested(month)

    def share(v: float) -> float:
        return v / total if total else 0.0

    return [
        Holding("אנליסט", "core", month.analyst, share(month.analyst), ["^SPX"]),
        Holding(
            "Blink", "satellite", month.blink, share(month.blink), list(tickers.get("blink", []))
        ),
        Holding("Crypto", "satellite", month.crypto, share(month.crypto), ["BTC-USD"]),
    ]


def net_worth_change(current: Month, previous: Month | None) -> float | None:
    """Month-on-month movement in net worth, or ``None`` for the first month."""
    if previous is None:
        return None
    return net_worth(current) - net_worth(previous)
