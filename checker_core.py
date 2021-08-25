from __future__ import annotations

from dataclasses import dataclass
from itertools import cycle
from threading import Lock
from typing import Iterator, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


SHIPPY_BASE_URL = "https://shoppy.gg/@{}"


@dataclass
class CheckResult:
    username: str
    available: bool
    status_code: int
    reason: str


class ProxyPool:
    def __init__(self, proxies: list[str]) -> None:
        cleaned = [p.strip() for p in proxies if p and p.strip()]
        self._iter: Optional[Iterator[str]] = cycle(cleaned) if cleaned else None
        self._lock = Lock()

    def next(self) -> Optional[dict[str, str]]:
        if self._iter is None:
            return None

        with self._lock:
            proxy = next(self._iter)

        if "://" not in proxy:
            proxy = f"http://{proxy}"
        return {"http": proxy, "https": proxy}


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.4,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=200, pool_maxsize=200)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )
    return session


def normalize_username(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""

    if "shoppy.gg/" in value:
        value = value.split("shoppy.gg/", 1)[1]

    value = value.strip("/")
    if value.startswith("@"):
        value = value[1:]
    return value.strip()


def evaluate_response(username: str, response: requests.Response) -> CheckResult:
    text = response.text.lower()
    status = response.status_code

    if status == 404:
        return CheckResult(username, True, status, "404_not_found")

    if status in (429, 500, 502, 503, 504):
        return CheckResult(username, False, status, "temporary_server_or_rate_limit")

    if status != 200:
        return CheckResult(username, False, status, "unexpected_status")

    not_found_markers = (
        "page could not be found",
        "user not found",
        "error 404",
        "this page doesn't exist",
    )
    if any(marker in text for marker in not_found_markers):
        return CheckResult(username, True, status, "body_not_found_marker")

    return CheckResult(username, False, status, "profile_exists")
