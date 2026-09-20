"""
Integration test for webhook authentication (QA finding #4).

Uses Flask's test client to exercise the actual before_request auth
gate in server.py — not a re-implementation of the check, the real one.
Run separately from test_guardrails.py since it needs to reload server
with different environment variables to test both modes.

Run:
    python3 -c "
    import sys, test_server_auth as t
    tests = [n for n in dir(t) if n.startswith('test_')]
    ok = 0
    for n in tests:
        getattr(t, n)(); ok += 1
    print(f'{ok}/{len(tests)} passed')
    "
"""

import importlib
import os


def _reload_server_with_env(demo_mode: str, secret: str | None = None):
    """server.py reads DEMO_MODE/WEBHOOK_SECRET at import time, so
    testing both modes requires reloading the module with different
    environment variables set first."""
    os.environ["RESOLVEAI_DEMO_MODE"] = demo_mode
    if secret is not None:
        os.environ["RESOLVEAI_WEBHOOK_SECRET"] = secret
    elif "RESOLVEAI_WEBHOOK_SECRET" in os.environ:
        del os.environ["RESOLVEAI_WEBHOOK_SECRET"]

    if "server" in globals().get("_loaded_modules", {}):
        pass
    import server as server_module
    importlib.reload(server_module)
    return server_module


def test_demo_mode_allows_unauthenticated_tool_calls():
    server_module = _reload_server_with_env("true")
    client = server_module.app.test_client()
    resp = client.post("/api/fraud/events", json={"case_id": "CASE-2001"})
    assert resp.status_code == 200, f"expected 200 in demo mode, got {resp.status_code}"
    assert resp.get_json()["ok"] is True


def test_production_mode_rejects_missing_secret():
    server_module = _reload_server_with_env("false", secret="real-secret-value")
    client = server_module.app.test_client()
    resp = client.post("/api/fraud/events", json={"case_id": "CASE-2001"})
    assert resp.status_code == 401, (
        f"expected 401 with no auth header in production mode, got {resp.status_code}"
    )
    assert resp.get_json()["reason"] == "UNAUTHORIZED"


def test_production_mode_rejects_wrong_secret():
    server_module = _reload_server_with_env("false", secret="real-secret-value")
    client = server_module.app.test_client()
    resp = client.post(
        "/api/fraud/events",
        json={"case_id": "CASE-2001"},
        headers={"X-ResolveAI-Secret": "wrong-guess"},
    )
    assert resp.status_code == 401


def test_production_mode_accepts_correct_secret():
    server_module = _reload_server_with_env("false", secret="real-secret-value")
    client = server_module.app.test_client()
    resp = client.post(
        "/api/fraud/events",
        json={"case_id": "CASE-2001"},
        headers={"X-ResolveAI-Secret": "real-secret-value"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_production_mode_still_allows_health_and_read_only_endpoints_without_auth():
    """Health checks and judge-facing read-only endpoints shouldn't
    require the webhook secret — only state-changing/case-revealing
    tool and fraud-event endpoints should."""
    server_module = _reload_server_with_env("false", secret="real-secret-value")
    client = server_module.app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    resp2 = client.get("/api/cases")
    assert resp2.status_code == 200


def test_production_mode_rejects_unauthenticated_freeze_attempt():
    """The highest-stakes endpoint must also be protected, not just the
    incident-creation one."""
    server_module = _reload_server_with_env("false", secret="real-secret-value")
    client = server_module.app.test_client()
    resp = client.post(
        "/tools/confirm_fraud_and_freeze",
        json={"call_id": "x", "customer_confirmed": True},
    )
    assert resp.status_code == 401


def test_reset_env_back_to_demo_mode():
    """Cleanup: leave the environment in demo mode so any test run
    after this file doesn't accidentally stay in production mode."""
    _reload_server_with_env("true")
