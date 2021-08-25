from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from time import perf_counter

import requests

from checker_core import ProxyPool, build_session, evaluate_response, normalize_username


DEFAULT_INPUT = "usernames.txt"
DEFAULT_PROXIES = "proxies.txt"
DEFAULT_OUTPUT = "available.txt"


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def unique_normalized_usernames(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for row in rows:
        value = normalize_username(row)
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def check_username(username: str, proxy_pool: ProxyPool, timeout: float) -> tuple[str, bool, str]:
    session = build_session()
    proxies = proxy_pool.next()
    url = f"https://shoppy.gg/@{username}"

    try:
        response = session.get(url, timeout=timeout, proxies=proxies, allow_redirects=True)
    except requests.RequestException as exc:
        return username, False, f"request_error:{type(exc).__name__}"

    result = evaluate_response(username, response)
    return username, result.available, result.reason


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fast Shoppy.gg username availability checker (supports @username format)."
    )
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT, help="Path to usernames list.")
    parser.add_argument("-p", "--proxies", default=DEFAULT_PROXIES, help="Path to proxy list.")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="Output file for available usernames.")
    parser.add_argument("-t", "--threads", type=int, default=64, help="Number of worker threads.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds.")
    parser.add_argument(
        "--no-proxies",
        action="store_true",
        help="Ignore proxy file and check directly.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    proxy_path = Path(args.proxies)
    output_path = Path(args.output)

    usernames = unique_normalized_usernames(read_lines(input_path))
    if not usernames:
        print(f"[x] No usernames found in {input_path}")
        return

    proxies = [] if args.no_proxies else read_lines(proxy_path)
    proxy_pool = ProxyPool(proxies)

    print(f"[*] Loaded {len(usernames)} usernames")
    print(f"[*] Loaded {len(proxies)} proxies" if proxies else "[*] Running without proxies")
    print(f"[*] Checking with {args.threads} threads\n")

    available_lock = Lock()
    print_lock = Lock()
    available: list[str] = []
    checked = 0

    start = perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, args.threads)) as executor:
        futures = [executor.submit(check_username, username, proxy_pool, args.timeout) for username in usernames]
        total = len(futures)

        for future in as_completed(futures):
            username, is_available, reason = future.result()
            checked += 1

            if is_available:
                with available_lock:
                    available.append(username)
                state = "AVAILABLE"
            else:
                state = "TAKEN/UNKNOWN"

            with print_lock:
                print(f"[{checked}/{total}] @{username} -> {state} ({reason})")

    available_sorted = sorted(set(available))
    output_path.write_text("\n".join(available_sorted), encoding="utf-8")

    elapsed = perf_counter() - start
    print("\n" + "=" * 60)
    print(f"Checked:   {len(usernames)}")
    print(f"Available: {len(available_sorted)}")
    print(f"Saved to:  {output_path}")
    print(f"Time:      {elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
