"""Smoke test HTTP contra a API (login, clientes, propostas, dashboard).

Uso:
  FLOWCRED_SMOKE_BASE=http://127.0.0.1:8001/api/v1 \\
  FLOWCRED_SMOKE_USER=admin FLOWCRED_SMOKE_PASS=admin \\
  python -m app.scripts.smoke_flowcred
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _req(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, object | None]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
        raw = e.read().decode() if e.fp else ""
    if not raw:
        return code, None
    try:
        return code, json.loads(raw)
    except json.JSONDecodeError:
        return code, raw


def main() -> int:
    base = os.environ.get("FLOWCRED_SMOKE_BASE", "http://127.0.0.1:8001/api/v1").rstrip("/")
    user = os.environ.get("FLOWCRED_SMOKE_USER", "admin")
    password = os.environ.get("FLOWCRED_SMOKE_PASS", "admin")

    code, login = _req("POST", f"{base}/auth/login", body={"username": user, "password": password})
    if code != 200 or not isinstance(login, dict) or "access_token" not in login:
        print(f"FAIL login HTTP {code}: {login}", file=sys.stderr)
        return 1
    token = str(login["access_token"])
    print(f"OK POST /auth/login -> {code}")

    endpoints = [
        ("GET", f"{base}/auth/me"),
        ("GET", f"{base}/clients?page=1&page_size=10"),
        ("GET", f"{base}/proposals?page=1&page_size=10"),
        ("GET", f"{base}/dashboard/summary"),
    ]
    for method, url in endpoints:
        c, _ = _req(method, url, token=token)
        tag = "OK" if c == 200 else "FAIL"
        print(f"{tag} {method} {url.replace(base, '')} -> {c}")
        if c != 200:
            return 1

    c, proposals = _req("GET", f"{base}/proposals?page=1&page_size=5", token=token)
    if c != 200 or not isinstance(proposals, dict):
        print(f"FAIL proposals list {c}", file=sys.stderr)
        return 1
    items = proposals.get("items") or []
    if not items:
        print("WARN no proposals in DB (seed may be off)", file=sys.stderr)
    else:
        pid = items[0]["id"]
        for suffix in ("checklist", "history"):
            u = f"{base}/proposals/{pid}/{suffix}"
            c2, _ = _req("GET", u, token=token)
            tag = "OK" if c2 == 200 else "FAIL"
            print(f"{tag} GET /proposals/{pid}/{suffix} -> {c2}")
            if c2 != 200:
                return 1

    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
