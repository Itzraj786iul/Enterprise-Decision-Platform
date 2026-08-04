#!/usr/bin/env python3
"""
Post-deploy verification for the Enterprise Decision Platform API.

Usage:
  python scripts/check_deployment.py --base-url https://edp-api.onrender.com
  python scripts/check_deployment.py --base-url https://edp-api.onrender.com --token "$JWT"
  python scripts/check_deployment.py --base-url http://localhost:8000 --skip-auth

Exit codes:
  0 = all checks passed
  1 = one or more checks failed
  2 = invalid arguments / network unreachable
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    status_code: int | None = None


@dataclass
class Report:
    results: list[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    @property
    def passed(self) -> bool:
        return all(r.ok for r in self.results)


def _request(
    url: str,
    *,
    method: str = "GET",
    token: str | None = None,
    timeout: float = 15.0,
    insecure: bool = False,
) -> tuple[int, dict[str, str], bytes]:
    headers = {"Accept": "application/json, text/plain, */*", "User-Agent": "edp-check-deployment/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, method=method, headers=headers)
    context = None
    if insecure:
        context = ssl._create_unverified_context()  # noqa: S323 — optional for local/dev only
    with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:  # noqa: S310
        body = resp.read()
        # http.client headers are case-insensitive; normalize to str dict
        hdrs = {k.lower(): v for k, v in resp.headers.items()}
        return int(resp.status), hdrs, body


def _safe_json(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def check_endpoint(
    report: Report,
    *,
    name: str,
    url: str,
    token: str | None = None,
    expect_status: tuple[int, ...] = (200,),
    require_headers: tuple[str, ...] = (),
    body_contains: tuple[str, ...] = (),
    json_path_ok: Any | None = None,
    insecure: bool = False,
) -> tuple[int | None, dict[str, str], bytes]:
    try:
        status, headers, body = _request(url, token=token, insecure=insecure)
    except urllib.error.HTTPError as exc:
        err_body = exc.read() if exc.fp else b""
        report.add(
            CheckResult(
                name=name,
                ok=exc.code in expect_status,
                detail=f"HTTP {exc.code}: {err_body[:200]!r}",
                status_code=exc.code,
            )
        )
        hdrs = {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])}
        return exc.code, hdrs, err_body
    except Exception as exc:  # noqa: BLE001 — surface connectivity failures
        report.add(CheckResult(name=name, ok=False, detail=f"{type(exc).__name__}: {exc}"))
        return None, {}, b""

    ok = status in expect_status
    details: list[str] = [f"status={status}"]
    for header in require_headers:
        if header.lower() not in headers:
            ok = False
            details.append(f"missing header {header}")
        else:
            details.append(f"{header}={headers[header.lower()]}")
    text = body.decode("utf-8", errors="replace")
    for needle in body_contains:
        if needle not in text:
            ok = False
            details.append(f"body missing {needle!r}")
    if json_path_ok is not None:
        payload = _safe_json(body)
        if not callable(json_path_ok) or not json_path_ok(payload):
            ok = False
            details.append("JSON assertion failed")
    report.add(CheckResult(name=name, ok=ok, detail="; ".join(details), status_code=status))
    return status, headers, body


def run_checks(
    base_url: str,
    *,
    token: str | None,
    skip_auth: bool,
    insecure: bool,
) -> Report:
    base = base_url.rstrip("/")
    report = Report()

    # Health
    status, headers, body = check_endpoint(
        report,
        name="health",
        url=f"{base}/health",
        require_headers=("x-request-id", "x-response-time-ms"),
        insecure=insecure,
        json_path_ok=lambda p: isinstance(p, dict) and p.get("status") == "ok",
    )
    version = None
    payload = _safe_json(body)
    if isinstance(payload, dict):
        version = payload.get("version")
        report.add(
            CheckResult(
                name="version",
                ok=bool(version),
                detail=f"version={version!r} environment={payload.get('environment')!r}",
            )
        )

    # Readiness
    check_endpoint(
        report,
        name="readiness",
        url=f"{base}/readiness",
        insecure=insecure,
        json_path_ok=lambda p: isinstance(p, dict) and p.get("status") in {"ok", "degraded"},
    )

    # Database
    check_endpoint(
        report,
        name="database",
        url=f"{base}/database",
        expect_status=(200, 503),
        insecure=insecure,
        json_path_ok=lambda p: isinstance(p, dict) and "components" in p,
    )

    # Metrics
    check_endpoint(
        report,
        name="metrics",
        url=f"{base}/metrics",
        insecure=insecure,
        body_contains=("edp_",),
    )

    # Platform API (public)
    check_endpoint(
        report,
        name="api_platform_features",
        url=f"{base}/api/v1/platform/features",
        insecure=insecure,
        json_path_ok=lambda p: isinstance(p, dict) and isinstance(p.get("features"), list),
    )

    # Auth me
    check_endpoint(
        report,
        name="api_auth_me",
        url=f"{base}/api/v1/auth/me",
        token=token,
        insecure=insecure,
        json_path_ok=lambda p: isinstance(p, dict) and "is_authenticated" in p,
    )

    # Protected analytics sample (dashboard overview)
    if skip_auth:
        report.add(
            CheckResult(
                name="api_dashboard_overview",
                ok=True,
                detail="skipped (--skip-auth)",
            )
        )
    elif token:
        check_endpoint(
            report,
            name="api_dashboard_overview",
            url=f"{base}/api/v1/dashboard/overview",
            token=token,
            expect_status=(200, 503),  # 503 if views missing; auth must not 401/403
            insecure=insecure,
        )
    else:
        # Expect 401 when production auth is on and no token
        check_endpoint(
            report,
            name="api_dashboard_overview_unauthenticated",
            url=f"{base}/api/v1/dashboard/overview",
            expect_status=(200, 401),
            insecure=insecure,
        )
        report.add(
            CheckResult(
                name="api_dashboard_overview",
                ok=True,
                detail="no token provided — unauthenticated probe only; pass --token for full check",
            )
        )

    # Response header presence on a second public call
    check_endpoint(
        report,
        name="response_headers",
        url=f"{base}/liveness",
        require_headers=("x-request-id", "x-response-time-ms", "x-content-type-options"),
        insecure=insecure,
    )

    # OpenAPI — may be disabled in production
    try:
        st, _, _ = _request(f"{base}/openapi.json", insecure=insecure)
        report.add(
            CheckResult(
                name="openapi",
                ok=True,
                detail=f"openapi.json status={st} (disabled/404 is OK in production)",
                status_code=st,
            )
        )
    except urllib.error.HTTPError as exc:
        report.add(
            CheckResult(
                name="openapi",
                ok=exc.code in {401, 403, 404},
                detail=f"HTTP {exc.code} (expected if docs disabled in production)",
                status_code=exc.code,
            )
        )
    except Exception as exc:  # noqa: BLE001
        report.add(CheckResult(name="openapi", ok=False, detail=str(exc)))

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EDP production deployment verification")
    parser.add_argument(
        "--base-url",
        required=True,
        help="API origin, e.g. https://edp-api.onrender.com",
    )
    parser.add_argument("--token", default=None, help="Bearer JWT for protected routes")
    parser.add_argument(
        "--skip-auth",
        action="store_true",
        help="Skip protected analytics route checks",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (local/dev only)",
    )
    args = parser.parse_args(argv)

    print(f"Checking deployment at {args.base_url}")
    report = run_checks(
        args.base_url,
        token=args.token,
        skip_auth=args.skip_auth,
        insecure=args.insecure,
    )

    width = max(len(r.name) for r in report.results) if report.results else 10
    for result in report.results:
        mark = "PASS" if result.ok else "FAIL"
        print(f"  [{mark}] {result.name.ljust(width)}  {result.detail}")

    failed = [r for r in report.results if not r.ok]
    print()
    if failed:
        print(f"FAILED: {len(failed)} check(s)")
        return 1
    print("OK: all deployment checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(2) from None
