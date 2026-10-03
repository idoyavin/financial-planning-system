from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest

from keva_ledger.money import shekels
from keva_ledger.report import summary
from keva_ledger.server import make_server


@pytest.fixture
def base_url(state) -> Iterator[str]:
    """A live server on an ephemeral port, torn down with the test."""
    httpd = make_server(state=state, host="127.0.0.1", port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _get(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 — fixed localhost URL
        return resp.status, resp.read().decode("utf-8")


def test_the_dashboard_renders_the_headline_figures(base_url, state):
    status, body = _get(base_url + "/")
    assert status == 200
    assert "Keva Ledger" in body
    assert shekels(summary(state)["net_worth"]) in body
    assert "אנליסט" in body


def test_the_api_serves_the_same_numbers_as_the_page(base_url, state):
    status, body = _get(base_url + "/api/summary")
    assert status == 200
    payload = json.loads(body)
    assert payload == json.loads(json.dumps(summary(state)))
    assert payload["net_worth"] == 29203

    _, full_body = _get(base_url + "/api/full")
    full = json.loads(full_body)
    assert len(full["insurance_schedule"]) == 12
    assert full["scenarios"]["conservative"] < full["scenarios"]["optimistic"]


def test_health_is_ok_and_unknown_paths_are_404(base_url):
    status, body = _get(base_url + "/healthz")
    assert status == 200
    assert json.loads(body)["ok"] is True

    with pytest.raises(urllib.error.HTTPError) as excinfo:
        _get(base_url + "/nope")
    assert excinfo.value.code == 404
