from __future__ import annotations

import pytest

from keva_ledger import DEFAULT_STATE_PATH, load_state
from keva_ledger.models import Month, State


@pytest.fixture
def state() -> State:
    """The real ledger, as bundled."""
    return load_state(DEFAULT_STATE_PATH)


@pytest.fixture
def plan(state: State):
    return state.plan


@pytest.fixture
def august(state: State) -> Month:
    """The August 2026 baseline month."""
    return state.latest


@pytest.fixture
def paid_off(august: Month) -> Month:
    """A hypothetical month with the car cleared and the pot funded."""
    from dataclasses import replace

    return replace(august, m="2027-05", car_rem=0, ins_pot=6000)
