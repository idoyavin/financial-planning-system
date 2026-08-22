"""``python -m keva_ledger`` — the ledger from the terminal."""

from __future__ import annotations

import argparse
import json
import sys

from . import load_state, report
from .dates import ym_label, ym_long
from .money import percent, shekels, signed
from .server import HOST, PORT, serve


def _print_summary(path: str | None) -> None:
    state = load_state(path)
    d = report.summary(state)
    plan = state.plan

    change = d["net_worth_change"]
    print(f"Keva Ledger — {d['month_label']} (updated {d['updated']})")
    print("─" * 52)
    print(
        f"  Net worth        {shekels(d['net_worth']):>12}"
        + (f"   {signed(change)} on the month" if change is not None else "   first month")
    )
    print(f"  Invested         {shekels(d['invested']):>12}")
    print(
        f"  Satellite        {percent(d['satellite_share']):>12}"
        + (
            f"   over cap — trim {shekels(d['satellite_trim'])}"
            if d["satellite_over_cap"]
            else f"   under the {percent(plan.sat_cap, 0)} cap"
        )
    )
    print(
        f"  Car remaining    {shekels(d['car_remaining']):>12}"
        + (
            f"   {d['car_payments_left']} payments, clears "
            f"{ym_long(d['car_payoff_month'])}"
            if d["car_payoff_month"]
            else "   paid off"
        )
    )
    nxt = d["insurance_next"]
    print(
        f"  Insurance pot    {shekels(d['insurance_pot']):>12}"
        + (f"   {shekels(nxt['total'])} due {nxt['label']}" if nxt else "   nothing due")
    )
    over = d["spend_variance"] > 0
    print(
        f"  Core spending    {shekels(d['spend_core']):>12}"
        f"   {shekels(abs(d['spend_variance']))} {'over' if over else 'under'} target"
    )
    print("─" * 52)
    print(
        f"  By {ym_label(plan.contract_end)}      {shekels(d['projection']):>12}"
        f"   at {percent(plan.real_return, 0)} real"
    )
    print(f"  Tasks            {d['tasks_done']} of {d['tasks_total']} done")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="keva-ledger", description=__doc__)
    parser.add_argument("--state", help="path to a state.json (defaults to the bundled one)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("summary", help="print the headline figures (default)")
    sub.add_parser("json", help="dump every computed figure as JSON")

    serve_cmd = sub.add_parser("serve", help="run the dashboard")
    serve_cmd.add_argument("--host", default=HOST)
    serve_cmd.add_argument("--port", type=int, default=PORT)

    args = parser.parse_args(argv)

    if args.command == "serve":
        serve(host=args.host, port=args.port)
    elif args.command == "json":
        print(json.dumps(report.full(load_state(args.state)), ensure_ascii=False, indent=2))
    else:
        _print_summary(args.state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
