# Keva Ledger

קבע — the standing order. The thing that runs every month whether or not
anyone is watching.

A small ledger for one financial plan: log a month, and every figure,
schedule and projection moves with it. No database, no framework — one
JSON document in `data/state.json` and a dashboard served from the
standard library.

## Getting started

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

make test     # 47 tests
make serve    # http://127.0.0.1:8000
```

`make test` works without the venv too, against any ambient pytest. The
package itself has no runtime dependencies, so `make serve` runs on a bare
Python 3.10+.

## What it computes

| Module | What it answers |
| --- | --- |
| `portfolio` | Net worth, invested capital, and the satellite share against its 10% cap |
| `car` | What is left on the ₪54,000, how many payments, and when it clears |
| `insurance` | When מקיף and חובה fall due, and whether the sinking fund covers the next bill |
| `spending` | Core spending against the ₪2,500 target, with bit transfers excluded |
| `projection` | Where the plan lands by March 2031 at 4%, 6% and 8% real |
| `budget` | The monthly standing order, before and after the car is paid off |

Two decisions are worth knowing about, because they change the numbers:

**Transfers sit outside the spending target.** bit and PAYBOX payments
leave the card and come back within days — you front the table, friends
settle up. They inflate the statement without being consumption.

**The satellite cap is measured against invested capital, not net worth.**
Otherwise a fat bank balance quietly licenses a bigger speculative
position, which is exactly backwards.

## Commands

```sh
make summary   # headline figures in the terminal
make json      # every computed figure as JSON
make serve     # the dashboard
make lint      # ruff
make test      # pytest
```

The server exposes `/`, `/api/summary`, `/api/full` and `/healthz`. The
page and the API render from the same `report.py` dictionary, so a figure
on the page and a figure in the JSON cannot drift apart.

## Logging a month

Add an entry to `months` in `data/state.json`:

```json
{
  "m": "2026-09",
  "bank": 3400, "analyst": 25100, "blink": 800, "crypto": 1150,
  "carRem": 54000, "insPot": 611,
  "spend": {"food": 1100, "transfers": 240, "fuel": 241,
            "groceries": 160, "shopping": 90, "other": 200}
}
```

Months sort themselves; the newest is the one every headline figure is
computed from.

## Assumptions

The projection stays deliberately plain: no raises, no קרן השתלמות, no
pension counted, satellite contributions valued at cost, and the
emergency fund and פיקדון added as cash rather than compounded. Every one
of those is upside left out rather than optimism built in.
