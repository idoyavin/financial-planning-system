"""The dashboard, served from the standard library.

No web framework: the whole surface is three GET routes, and a dependency
that has to be installed before the page renders is a dependency that can
break the page. ``make serve`` should work on a bare Python.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import load_state, report
from .dates import ym_long
from .models import State
from .money import percent, shekels, signed

HOST = "127.0.0.1"
PORT = 8000


def render_page(state: State) -> str:
    """The dashboard as a single self-contained HTML document."""
    d = report.full(state)
    plan = state.plan

    def stat(key: str, value: str, sub: str, cls: str = "") -> str:
        return (
            f'<div class="stat"><span class="k">{key}</span>'
            f'<span class="v {cls}">{value}</span><span class="s">{sub}</span></div>'
        )

    change = d["net_worth_change"]
    strip = "".join(
        [
            stat(
                "Net worth",
                shekels(d["net_worth"]),
                "first month logged" if change is None else f"{signed(change)} since last month",
            ),
            stat(
                "Car remaining",
                shekels(d["car_remaining"]),
                (
                    "paid off"
                    if d["car_remaining"] <= 0
                    else f"{d['car_payments_left']} payments of {shekels(plan.car_monthly)}"
                ),
                "amber" if d["car_remaining"] > 0 else "up",
            ),
            stat(
                "Satellite share",
                percent(d["satellite_share"]),
                (
                    f"over the {percent(plan.sat_cap, 0)} cap — trim {shekels(d['satellite_trim'])}"
                    if d["satellite_over_cap"]
                    else f"under the {percent(plan.sat_cap, 0)} cap"
                ),
                "down" if d["satellite_over_cap"] else "up",
            ),
            stat(
                "Insurance pot",
                shekels(d["insurance_pot"]),
                (
                    f"{shekels(d['insurance_next']['total'])} due {d['insurance_next']['label']}"
                    if d["insurance_next"]
                    else "nothing due this year"
                ),
                "br",
            ),
        ]
    )

    months = "".join(
        f"<tr><td>{m['label']}</td><td class='n'>{shekels(m['bank'])}</td>"
        f"<td class='n'>{shekels(m['analyst'])}</td><td class='n'>{shekels(m['blink'])}</td>"
        f"<td class='n'>{shekels(m['crypto'])}</td>"
        f"<td class='n b'>{shekels(m['net_worth'])}</td></tr>"
        for m in reversed(d["months"])
    )

    spend_rows = "".join(
        f"<tr><td>{c['label']}"
        + ("" if c["counts_to_target"] else " <span class='pill'>outside target</span>")
        + f"</td><td class='n'>{shekels(c['amount'])}</td>"
        f"<td class='n'>{percent(c['share'])}</td></tr>"
        for c in d["spending"]
    )

    ins_rows = "".join(
        f"<tr><td>{r['label']}</td><td class='n'>{shekels(r['makif']) if r['makif'] else '—'}</td>"
        f"<td class='n'>{shekels(r['hova']) if r['hova'] else '—'}</td>"
        f"<td class='n'>{shekels(r['total']) if r['total'] else '—'}</td></tr>"
        for r in d["insurance_schedule"]
    )

    holding_rows = "".join(
        f"<tr><td><b>{h['account']}</b> <span class='pill'>{h['kind']}</span></td>"
        f"<td class='t'>{', '.join(h['holdings'])}</td>"
        f"<td class='n'>{shekels(h['value'])}</td><td class='n'>{percent(h['share'])}</td></tr>"
        for h in d["holdings"]
    )

    def budget_table(key: str, caption: str) -> str:
        b = d["budgets"][key]
        rows = "".join(
            f"<tr><td>{ln['label']}</td>"
            f"<td class='n'>{'' if ln['amount'] >= 0 else '−'}"
            f"{shekels(abs(ln['amount']))}</td></tr>"
            for ln in b["lines"]
        )
        return (
            f"<div class='card'><span class='eyebrow'>{caption}</span>"
            f"<table><tbody>{rows}"
            f"<tr class='total'><td>Unallocated</td>"
            f"<td class='n'>{shekels(b['unallocated'])}</td></tr></tbody></table></div>"
        )

    tasks = "".join(
        f"<li class='{'done' if t['done'] else ''}'><b>{t['text']}</b><p>{t['detail']}</p></li>"
        for t in d["tasks"]
    )

    scen = d["scenarios"]

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Keva Ledger</title>
<style>
:root{{--ground:#F4F3EF;--surface:#fff;--line:#D9D5CB;--ink:#141821;--ink-2:#3D4552;
--muted:#5E6675;--brass:#7A5B1E;--good:#1C6E42;--warn:#9C4E0B;--bad:#9E1F1F}}
@media (prefers-color-scheme:dark){{:root{{--ground:#0F1218;--surface:#171C25;--line:#2C3542;
--ink:#E9ECF2;--ink-2:#C3C9D6;--muted:#8D97A8;--brass:#D4AC46;--good:#5DC086;
--warn:#E2A055;--bad:#EF8080}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);font-size:15px;line-height:1.55;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:32px 20px 96px}}
.n{{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums;text-align:right}}
.b{{font-weight:600}}
h1{{font-size:clamp(26px,4.5vw,38px);letter-spacing:-.02em;margin:8px 0 6px}}
h2{{font-size:19px;margin:0}}
header{{border-bottom:2px solid var(--ink);padding-bottom:18px}}
header p{{margin:0;color:var(--muted)}}
.eyebrow{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:1px;
background:var(--line);border:1px solid var(--line);margin:26px 0 40px;border-radius:3px;
overflow:hidden}}
.stat{{background:var(--surface);padding:15px 17px}}
.stat .k{{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
display:block;margin-bottom:6px}}
.stat .v{{font-family:ui-monospace,Menlo,monospace;font-size:23px;font-weight:600;display:block}}
.stat .s{{font-size:12.5px;color:var(--muted);margin-top:4px;display:block}}
.up{{color:var(--good)}}.down{{color:var(--bad)}}.amber{{color:var(--warn)}}.br{{color:var(--brass)}}
section{{margin:0 0 42px}}
.shead{{display:flex;align-items:baseline;gap:14px;margin-bottom:16px;
border-bottom:1px solid var(--line);padding-bottom:8px}}
.shead .note{{color:var(--muted);font-size:13px}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:3px;padding:16px;
overflow-x:auto}}
.grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.grid3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}}
th{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);
font-weight:500}}
tr.total td{{font-weight:700;border-bottom:none;border-top:2px solid var(--ink)}}
.pill{{font-size:10.5px;border:1px solid var(--line);border-radius:99px;padding:1px 7px;
color:var(--muted)}}
.t{{font-size:12.5px;color:var(--muted)}}
ol{{padding-left:20px;margin:0}}
ol li{{margin-bottom:14px}}
ol li p{{margin:3px 0 0;color:var(--ink-2);font-size:13.5px}}
ol li.done b{{text-decoration:line-through;color:var(--muted)}}
</style></head><body><div class="wrap">
<header><span class="eyebrow">Keva Ledger · updated {d["updated"]}</span>
<h1>From {shekels(d["net_worth"])} to {shekels(d["projection"])}</h1>
<p>Live from your own figures — {d["month_label"]}, {d["months_logged"]} month(s) logged.</p>
</header>
<div class="strip">{strip}</div>

<section><div class="shead"><h2>Net worth</h2>
<span class="note">{d["months_logged"]} month(s) logged</span></div>
<div class="card"><table><thead><tr><th>Month</th><th class="n">Bank</th>
<th class="n">אנליסט</th><th class="n">Blink</th><th class="n">Crypto</th>
<th class="n">Net worth</th></tr></thead><tbody>{months}</tbody></table></div></section>

<section><div class="shead"><h2>Car payoff</h2>
<span class="note">{shekels(plan.car_total)} total · {shekels(plan.car_monthly)}/month</span></div>
<div class="card"><p style="margin:0">
<b>{percent(d["car_fraction_paid"])}</b> paid · {shekels(d["car_remaining"])} to go ·
<b>{d["car_payments_left"]} payments</b> left, clearing
{ym_long(d["car_payoff_month"]) if d["car_payoff_month"] else "—"}.
{"The " + shekels(plan.grant) + " מענק has yet to land." if d["grant_outstanding"] else ""}
</p></div></section>

<section><div class="shead"><h2>Spending against target</h2>
<span class="note">{d["month_label"]} · target {shekels(plan.spend_target)}
excluding bit transfers</span></div>
<div class="grid2"><div class="card"><table><thead><tr><th>Category</th>
<th class="n">Spent</th><th class="n">Share</th></tr></thead><tbody>{spend_rows}
<tr class="total"><td>Total on the card</td>
<td class="n">{shekels(d["spend_total"])}</td><td></td></tr></tbody></table></div>
<div class="card"><span class="eyebrow">Core spending vs target</span>
<p style="font-size:26px;font-weight:600;margin:10px 0" class="n
{"down" if d["spend_variance"] > 0 else "up"}">{shekels(d["spend_core"])}</p>
<p style="margin:0;color:var(--ink-2)">{shekels(abs(d["spend_variance"]))}
{"over" if d["spend_variance"] > 0 else "under"} the {shekels(plan.spend_target)} target.</p>
</div></div></section>

<section><div class="shead"><h2>Insurance sinking fund</h2>
<span class="note">{shekels(plan.ins_fund)}/month · next twelve months</span></div>
<div class="card"><table><thead><tr><th>Month</th><th class="n">מקיף</th>
<th class="n">חובה</th><th class="n">Due</th></tr></thead><tbody>{ins_rows}
<tr class="total"><td>Twelve-month total</td><td></td><td></td>
<td class="n">{shekels(d["insurance_twelve_month_total"])}</td></tr></tbody></table></div></section>

<section><div class="shead"><h2>Portfolio</h2>
<span class="note">{shekels(d["invested"])} invested · satellite cap
{percent(plan.sat_cap, 0)}</span></div>
<div class="card"><table><thead><tr><th>Account</th><th>Holdings</th>
<th class="n">Value</th><th class="n">Share</th></tr></thead><tbody>{holding_rows}
<tr class="total"><td>Total invested</td><td></td>
<td class="n">{shekels(d["invested"])}</td><td></td></tr></tbody></table></div>
<div class="card" style="margin-top:16px"><span class="eyebrow">Watchlist</span>
<p class="t" style="margin:8px 0 0">{" · ".join(d["watchlist"])}</p></div></section>

<section><div class="shead"><h2>Where this lands by {ym_long(plan.contract_end)}</h2>
<span class="note">{percent(plan.real_return, 0)} real</span></div>
<div class="grid3">
<div class="card"><span class="eyebrow">Conservative — 4% real</span>
<p class="n b" style="font-size:22px;margin:7px 0 0">{shekels(scen["conservative"])}</p></div>
<div class="card" style="border-color:var(--brass)">
<span class="eyebrow br">Central — {percent(plan.real_return, 0)} real</span>
<p class="n b br" style="font-size:22px;margin:7px 0 0">{shekels(scen["central"])}</p></div>
<div class="card"><span class="eyebrow">Optimistic — 8% real</span>
<p class="n b" style="font-size:22px;margin:7px 0 0">{shekels(scen["optimistic"])}</p></div>
</div></section>

<section><div class="shead"><h2>Every month from December</h2></div>
<div class="grid2">
{budget_table("sprint", "Dec 2026 → Apr 2027 — the sprint")}
{budget_table("post_car", "May 2027 → Mar 2031 — car paid off")}
</div></section>

<section><div class="shead"><h2>What to do next</h2>
<span class="note">{d["tasks_done"]} of {d["tasks_total"]} done</span></div>
<div class="card"><ol>{tasks}</ol></div></section>

<p class="t">Served by keva-ledger · <a href="/api/summary">/api/summary</a> ·
<a href="/api/full">/api/full</a></p>
</div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    """Three GET routes: the page, and two JSON views of the same figures."""

    server_version = "keva-ledger"
    state: State

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: Any, code: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler's spelling
        route = self.path.split("?", 1)[0].rstrip("/") or "/"
        if route == "/":
            self._send(200, render_page(self.state).encode("utf-8"), "text/html; charset=utf-8")
        elif route == "/api/summary":
            self._json(report.summary(self.state))
        elif route == "/api/full":
            self._json(report.full(self.state))
        elif route == "/healthz":
            self._json({"ok": True, "months": len(self.state.months)})
        else:
            self._json({"error": "not found", "path": self.path}, code=404)

    def log_message(self, fmt: str, *args: Any) -> None:
        """Quieter than the default, which prints a timestamp banner per hit."""
        print(f"  {self.command} {self.path} → {args[1] if len(args) > 1 else ''}")


def make_server(
    state: State | None = None,
    host: str = HOST,
    port: int = PORT,
) -> ThreadingHTTPServer:
    """Build a server bound to ``host:port``. Port 0 picks a free one."""
    loaded = state if state is not None else load_state()
    handler = type("BoundHandler", (Handler,), {"state": loaded})
    return ThreadingHTTPServer((host, port), handler)


def serve(host: str = HOST, port: int = PORT) -> None:
    """Run the dashboard until interrupted."""
    httpd = make_server(host=host, port=port)
    print(f"Keva Ledger on http://{host}:{httpd.server_address[1]}")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
