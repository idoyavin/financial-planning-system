"""One dictionary holding every published number.

The HTTP layer and the CLI both render from this, so a figure shown on the
page and a figure printed in the terminal cannot drift apart.
"""

from __future__ import annotations

from typing import Any

from . import budget, car, insurance, portfolio, projection, spending
from .dates import ym_label, ym_long
from .models import State


def summary(state: State) -> dict[str, Any]:
    """Every headline figure, computed from the latest logged month."""
    latest = state.latest
    plan = state.plan
    nxt = insurance.next_due(latest.m, plan)

    return {
        "updated": state.updated,
        "month": latest.m,
        "month_label": ym_long(latest.m),
        "months_logged": len(state.months),
        "net_worth": portfolio.net_worth(latest),
        "net_worth_change": portfolio.net_worth_change(latest, state.previous),
        "invested": portfolio.invested(latest),
        "satellite_share": portfolio.satellite_share(latest),
        "satellite_over_cap": portfolio.over_cap(latest, plan),
        "satellite_trim": portfolio.trim_to_cap(latest, plan),
        "car_remaining": latest.car_rem,
        "car_payments_left": car.payments_remaining(latest, plan),
        "car_fraction_paid": car.fraction_paid(latest, plan),
        "car_payoff_month": car.payoff_month(latest, plan),
        "grant_outstanding": car.grant_outstanding(latest, plan),
        "spend_total": spending.spend_total(latest),
        "spend_core": spending.spend_core(latest),
        "spend_target": plan.spend_target,
        "spend_variance": spending.variance(latest, plan),
        "insurance_pot": latest.ins_pot,
        "insurance_next": (
            {"month": nxt.ym, "label": ym_label(nxt.ym), "total": nxt.due.total}
            if nxt
            else None
        ),
        "insurance_coverage": insurance.coverage(latest.ins_pot, nxt),
        "insurance_twelve_month_total": insurance.twelve_month_total(latest.m, plan),
        "projection": projection.project(latest, plan),
        "tasks_done": sum(1 for t in state.tasks if t.done),
        "tasks_total": len(state.tasks),
    }


def full(state: State) -> dict[str, Any]:
    """The summary plus every table the dashboard draws."""
    latest = state.latest
    plan = state.plan
    scen = projection.scenarios(latest, plan)

    return {
        **summary(state),
        "months": [
            {
                "month": m.m,
                "label": ym_label(m.m),
                "bank": m.bank,
                "analyst": m.analyst,
                "blink": m.blink,
                "crypto": m.crypto,
                "net_worth": portfolio.net_worth(m),
                "note": m.note,
            }
            for m in state.months
        ],
        "holdings": [
            {
                "account": h.account,
                "kind": h.kind,
                "value": h.value,
                "share": h.share,
                "holdings": h.holdings,
            }
            for h in portfolio.holdings(latest, state.tickers)
        ],
        "spending": [
            {
                "key": c.key,
                "label": c.label,
                "amount": c.amount,
                "share": c.share,
                "counts_to_target": c.counts_to_target,
            }
            for c in spending.breakdown(latest)
        ],
        "insurance_schedule": [
            {"month": ym, "label": ym_label(ym), "makif": d.makif, "hova": d.hova, "total": d.total}
            for ym, d in insurance.schedule(latest.m, plan)
        ],
        "projection_curve": [
            {"month": p.ym, "label": ym_label(p.ym), "value": p.value}
            for p in projection.curve(latest, plan)
        ],
        "scenarios": {
            "conservative": scen.conservative,
            "central": scen.central,
            "optimistic": scen.optimistic,
        },
        "budgets": {
            phase: {
                "phase": b.phase,
                "lines": [{"label": ln.label, "amount": ln.amount} for ln in b.lines],
                "unallocated": b.unallocated,
                "invested": b.invested,
            }
            for phase, b in (
                ("sprint", budget.sprint_budget(plan)),
                ("post_car", budget.post_car_budget(plan)),
            )
        },
        "tasks": [
            {"id": t.id, "text": t.text, "detail": t.detail, "done": t.done} for t in state.tasks
        ],
        "watchlist": state.tickers.get("watch", []),
    }
