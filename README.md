# Shoppy Username Checker

Fast and practical username checker for `shoppy.gg/@username`.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-6f42c1)
![Status](https://img.shields.io/badge/status-active-success)

This project was rebuilt to be cleaner, faster, and easier to run:
- normalizes input like `@name`, `name`, or full URLs (`https://shoppy.gg/@name`)
- uses concurrent workers for speed
- supports rotating proxies
- retries around temporary network/rate-limit errors
- writes all available usernames to `available.txt`

## Why this exists

Checking usernames one by one is annoying. This tool lets you throw in a list and get a usable result quickly without the weird setup steps.

## Quick start

```bash
python -m pip install -r requirements.txt
python shoppy_checker.py
```

## Input format

### `usernames.txt`
You can mix formats:

```txt
@ivory
ivory
https://shoppy.gg/@ivory
```

### `proxies.txt` (optional)
Leave it empty or use `--no-proxies` if you do not want proxy usage.

Supported lines:

```txt
127.0.0.1:8080
user:pass@127.0.0.1:8080
http://127.0.0.1:8080
```

## Usage

```bash
python shoppy_checker.py \
  --input usernames.txt \
  --proxies proxies.txt \
  --output available.txt \
  --threads 64 \
  --timeout 10
```

Useful options:
- `--no-proxies` -> ignore `proxies.txt`
- `--threads` -> change worker count (higher is faster but heavier)
- `--timeout` -> per-request timeout in seconds

## Output

- Console logs each checked username and result reason.
- `available.txt` contains only usernames that appear available.

## Notes

- Availability checks are based on the public profile route (`https://shoppy.gg/@username`).
- If Shoppy changes response behavior, markers can be adjusted in `checker_core.py`.

## Repo

GitHub: [4x3/shoppy-username-checker](https://github.com/4x3/shoppy-username-checker)
