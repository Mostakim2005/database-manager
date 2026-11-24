"""Cloudflare-tolerant, polite HTTP fetch helper for Media domain."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Any

try:
    from curl_cffi.requests import Session as CFSession  # type: ignore[import-not-found]
    HAVE_CURL_CFFI = True
except Exception:
    CFSession = None
    HAVE_CURL_CFFI = False

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def build_headers(extra: dict[str, str] | None = None, referer: str | None = None) -> dict[str, str]:
    headers = dict(DEFAULT_HEADERS)
    if referer:
        headers["Referer"] = referer
    if extra:
        headers.update(extra)
    return headers


def safe_get(
    url: str,
    headers: dict[str, str] | None = None,
    referer: str | None = None,
    timeout: float = 10.0,
    delay_sec: float = 1.0,
    impersonate: str = "chrome120",
    retries: int = 2,
) -> tuple[int, str, str] | None:
    """Return ``(status_code, text, final_url)`` or ``None`` if every attempt fails."""
    request_headers = build_headers(headers, referer)
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        if HAVE_CURL_CFFI and CFSession is not None:
            try:
                with CFSession(impersonate=impersonate) as session:
                    response = session.get(url, headers=request_headers, timeout=timeout)
                    result = (int(response.status_code), response.text, str(response.url))
                if delay_sec > 0:
                    time.sleep(delay_sec)
                return result
            except Exception as exc:
                last_error = exc

        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                result = (
                    int(getattr(response, "status", None) or 200),
                    response.read().decode(charset, errors="replace"),
                    str(response.geturl()),
                )
            if delay_sec > 0:
                time.sleep(delay_sec)
            return result
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (403, 404, 410, 451) and attempt == retries:
                return (int(exc.code), "", url)
        except Exception as exc:
            last_error = exc

        if attempt < retries and delay_sec > 0:
            time.sleep(delay_sec * attempt)

    print(f"[fetch_helper] could not fetch {url}: {last_error}")
    return None


def probe_url_status(url: str, timeout: float = 8.0, delay_sec: float = 0.5) -> dict[str, Any]:
    """Probe a single URL and return structured status metadata without throwing."""
    res = safe_get(url, timeout=timeout, delay_sec=delay_sec, retries=1)
    if res is None:
        return {"url": url, "ok": False, "status": 0, "final_url": url, "state": "unreachable"}
    status_code, body, final_url = res
    body_l = body[:4000].lower()
    region_locked = any(
        marker in body_l
        for marker in ("not available in your country", "not available in your region", "geo-blocked", "region lock")
    )
    ok = 200 <= status_code < 400 and not region_locked
    if region_locked:
        state = "region_locked"
    elif status_code in (404, 410):
        state = "broken"
    elif status_code in (403, 429):
        state = "blocked_or_rate_limited"
    elif 200 <= status_code < 400:
        state = "ok"
    else:
        state = f"http_{status_code}"
    return {
        "url": url,
        "ok": ok,
        "status": status_code,
        "final_url": final_url,
        "state": state,
    }
