from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_jumpserver_gui_sucks import cli_login
from mcp_jumpserver_gui_sucks.config import Settings


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        base_url="https://jumpserver.example.com",
        org_id="",
        state_dir=tmp_path,
        state_file=tmp_path / "auth-state.json",
        log_level="INFO",
        verify_tls=True,
        request_timeout_seconds=20.0,
        terminal_idle_timeout_seconds=3600.0,
        terminal_reap_interval_seconds=30.0,
        max_terminal_sessions=8,
    )


def test_sync_session_api_headers_prefers_cookie_over_stale_header(
    tmp_path: Path,
) -> None:
    flow = cli_login.JumpServerCLILogin(
        make_settings(tmp_path),
        base_url="https://jumpserver.example.com",
    )
    try:
        flow._client.headers["X-CSRFToken"] = "stale-bootstrap-token"
        flow._client.cookies.set(
            "jms_csrftoken",
            "rotated-after-login",
            domain="jumpserver.example.com",
            path="/",
        )

        headers = flow._sync_session_api_headers()

        assert headers["X-CSRFToken"] == "rotated-after-login"
        assert flow._client.headers["X-CSRFToken"] == "rotated-after-login"
        assert headers["Referer"] == "https://jumpserver.example.com/ui/"
        assert headers["Origin"] == "https://jumpserver.example.com"
    finally:
        flow.close()


def test_complete_confirmation_syncs_csrf_before_post(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    captured: dict[str, Any] = {}

    class FakeResponse:
        status_code = 200
        text = '"ok"'

        @staticmethod
        def strip() -> str:
            return "ok"

    flow = cli_login.JumpServerCLILogin(
        make_settings(tmp_path),
        base_url="https://jumpserver.example.com",
    )
    try:
        flow._client.headers["X-CSRFToken"] = "stale-bootstrap-token"
        flow._client.cookies.set(
            "jms_csrftoken",
            "rotated-after-login",
            domain="jumpserver.example.com",
            path="/",
        )

        def fake_post(url: str, **kwargs: Any) -> FakeResponse:
            captured["url"] = url
            captured["kwargs"] = kwargs
            return FakeResponse()

        monkeypatch.setattr(flow._client, "post", fake_post)

        flow.complete_confirmation(
            confirm_type="password",
            secret_key="encrypted-secret",
        )

        assert captured["url"] == cli_login.CONFIRM_API_PATH
        headers = captured["kwargs"]["headers"]
        assert headers["X-CSRFToken"] == "rotated-after-login"
        assert captured["kwargs"]["json"]["confirm_type"] == "password"
    finally:
        flow.close()
