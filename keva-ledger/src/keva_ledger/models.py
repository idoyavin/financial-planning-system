"""The ledger's data model.

The JSON on disk uses the short camelCase keys the dashboard was built
around; these dataclasses give that shape names you can read, and are the
only place the two vocabularies meet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dates import parse_ym

SPEND_CATEGORIES = ("food", "transfers", "fuel", "groceries", "shopping", "other")

# Hebrew labels, as they read on the statement.
CATEGORY_LABELS = {
    "food": "אוכל בחוץ",
    "fuel": "דלק",
    "groceries": "מכולת",
    "shopping": "קניות",
    "transfers": "העברות (bit out)",
    "other": "Everything else",
}


@dataclass(frozen=True)
class Plan:
    """The standing plan: income, fixed costs, and the targets."""

    salary: float
    living: float
    fuel: float
    service: float
    ins_fund: float
    car_total: float
    car_monthly: float
    grant: float
    pikadon: float
    analyst_sprint: float
    analyst_full: float
    satellite: float
    cash_alloc: float
    emergency_target: float
    hova_year: float
    hova_n: int
    makif_year: float
    makif_n: int
    sprint_start: str
    sprint_end: str
    contract_end: str
    real_return: float
    sat_cap: float
    spend_target: float

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> Plan:
        return cls(
            salary=d["salary"],
            living=d["living"],
            fuel=d["fuel"],
            service=d["service"],
            ins_fund=d["insFund"],
            car_total=d["carTotal"],
            car_monthly=d["carMonthly"],
            grant=d["grant"],
            pikadon=d["pikadon"],
            analyst_sprint=d["analystSprint"],
            analyst_full=d["analystFull"],
            satellite=d["satellite"],
            cash_alloc=d["cashAlloc"],
            emergency_target=d["emergencyTarget"],
            hova_year=d["hovaYear"],
            hova_n=d["hovaN"],
            makif_year=d["makifYear"],
            makif_n=d["makifN"],
            sprint_start=d.get("sprintStart", "2026-12"),
            sprint_end=d["sprintEnd"],
            contract_end=d["contractEnd"],
            real_return=d["realReturn"],
            sat_cap=d["satCap"],
            spend_target=d["spendTarget"],
        )


@dataclass(frozen=True)
class Month:
    """One logged month: balances at the close, and what was spent."""

    m: str
    bank: float
    analyst: float
    blink: float
    crypto: float
    car_rem: float
    ins_pot: float
    spend: dict[str, float]
    note: str = ""

    def __post_init__(self) -> None:
        parse_ym(self.m)

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> Month:
        spend = {k: float(d.get("spend", {}).get(k, 0)) for k in SPEND_CATEGORIES}
        return cls(
            m=d["m"],
            bank=d["bank"],
            analyst=d["analyst"],
            blink=d["blink"],
            crypto=d["crypto"],
            car_rem=d["carRem"],
            ins_pot=d["insPot"],
            spend=spend,
            note=d.get("note", ""),
        )

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "m": self.m,
            "bank": self.bank,
            "analyst": self.analyst,
            "blink": self.blink,
            "crypto": self.crypto,
            "carRem": self.car_rem,
            "insPot": self.ins_pot,
            "spend": dict(self.spend),
        }
        if self.note:
            out["note"] = self.note
        return out


@dataclass(frozen=True)
class Task:
    """One item on the do-next list."""

    id: str
    text: str
    detail: str = ""
    done: bool = False

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> Task:
        return cls(id=d["id"], text=d["text"], detail=d.get("d", ""), done=bool(d.get("done")))


@dataclass
class State:
    """Everything the ledger knows, loaded from one JSON document."""

    plan: Plan
    months: list[Month]
    tickers: dict[str, list[str]] = field(default_factory=dict)
    tasks: list[Task] = field(default_factory=list)
    updated: str = ""
    version: int = 1

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> State:
        return cls(
            plan=Plan.from_json(d["plan"]),
            months=sorted(
                (Month.from_json(m) for m in d.get("months", [])),
                key=lambda r: r.m,
            ),
            tickers=d.get("tickers", {}),
            tasks=[Task.from_json(t) for t in d.get("tasks", [])],
            updated=d.get("updated", ""),
            version=d.get("v", 1),
        )

    @classmethod
    def load(cls, path: str | Path) -> State:
        with open(path, encoding="utf-8") as fh:
            return cls.from_json(json.load(fh))

    @property
    def latest(self) -> Month:
        """The most recent logged month."""
        if not self.months:
            raise ValueError("no months logged")
        return self.months[-1]

    @property
    def previous(self) -> Month | None:
        """The month before the latest, or ``None`` when only one is logged."""
        return self.months[-2] if len(self.months) > 1 else None
