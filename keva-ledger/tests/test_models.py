from __future__ import annotations

import pytest

from keva_ledger.models import SPEND_CATEGORIES, Month, State


def test_plan_reads_the_camelcase_json(plan):
    assert plan.salary == 14000
    assert plan.car_total == 54000
    assert plan.sprint_end == "2027-04"
    assert plan.contract_end == "2031-03"


def test_baseline_month_loads_with_every_spend_category(august):
    assert august.m == "2026-08"
    assert august.bank == 2994
    assert set(august.spend) == set(SPEND_CATEGORIES)


def test_months_are_sorted_and_latest_is_the_newest():
    state = State.from_json(
        {
            "plan": _plan_json(),
            "months": [_month_json("2026-12"), _month_json("2026-08"), _month_json("2026-10")],
        }
    )
    assert [m.m for m in state.months] == ["2026-08", "2026-10", "2026-12"]
    assert state.latest.m == "2026-12"
    assert state.previous is not None
    assert state.previous.m == "2026-10"


def test_a_single_month_has_no_previous_and_a_bad_month_is_rejected(state):
    assert state.previous is None
    with pytest.raises(ValueError):
        Month.from_json({**_month_json("2026-13"), "m": "2026-13"})


def _plan_json() -> dict:
    return {
        "salary": 14000, "living": 2500, "fuel": 241, "service": 400, "insFund": 611,
        "carTotal": 54000, "carMonthly": 7100, "grant": 18500, "pikadon": 27100,
        "analystSprint": 2500, "analystFull": 9000, "satellite": 600, "cashAlloc": 648,
        "emergencyTarget": 11500, "hovaYear": 2470, "hovaN": 8, "makifYear": 4857,
        "makifN": 3, "sprintStart": "2026-12", "sprintEnd": "2027-04",
        "contractEnd": "2031-03",
        "realReturn": 0.06, "satCap": 0.1, "spendTarget": 2500,
    }


def _month_json(m: str) -> dict:
    return {
        "m": m, "bank": 3000, "analyst": 24000, "blink": 800, "crypto": 1100,
        "carRem": 54000, "insPot": 0, "spend": {"food": 1000, "transfers": 300},
    }
