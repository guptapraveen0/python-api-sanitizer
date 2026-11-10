#!/usr/bin/env python3
"""Fetch a small public test-API sample or sanitize an offline fixture."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import requests

API_URL = "https://jsonplaceholder.typicode.com/users"
SOURCE = "jsonplaceholder.typicode.com (public test API)"
DEFAULT_TIMEOUT = 5
MAX_LIMIT = 10
REPORT_DIR = Path("reports")
REPORT_PATH = REPORT_DIR / "api_summary.json"

MOCK_FIXTURE = [
    {"id": 1, "name": "Leanne Graham", "username": "Bret",
     "email": "Sincere@april.biz"},
    {"id": 2, "name": "Ervin Howell", "username": "Antonette",
     "email": "Shanna@melissa.tv"},
    {"id": 3, "name": "Clementine Bauch", "username": "Samantha",
     "email": "Nathan@yesenia.net"},
]


def parse_payload(payload: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Require a top-level list; retain dict rows and report malformed rows."""
    if not isinstance(payload, list):
        raise ValueError("Expected top-level JSON array (list).")
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"record[{index}]: expected object, got {type(item).__name__}")
        else:
            rows.append(item)
    return rows, errors


def validate_and_sanitize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, list[str]]:
    """Only expose id/name; email and all other input fields are discarded."""
    safe_records: list[dict[str, Any]] = []
    invalid = 0
    errors: list[str] = []
    for index, row in enumerate(rows):
        record_id = row.get("id")
        name = row.get("name")
        if not isinstance(record_id, int) or isinstance(record_id, bool) or not isinstance(name, str) or not name.strip():
            invalid += 1
            errors.append(f"record[{index}]: missing or invalid required field(s): id, name")
            continue
        safe_records.append({"id": record_id, "name": name.strip()})
    return safe_records, invalid, errors


def fetch_live(url: str, limit: int, timeout: float) -> tuple[Any | None, list[str]]:
    """Fetch once; never disable TLS verification and never retry."""
    errors: list[str] = []
    try:
        response = requests.get(
            url,
            params={"_limit": limit},
            timeout=timeout,
            # requests verifies TLS certificates by default; kept enabled.
        )
    except requests.exceptions.Timeout:
        return None, [f"Request timed out after {timeout:g} seconds."]
    except requests.exceptions.ConnectionError:
        return None, ["Connection failed; check host, DNS, and network connectivity."]
    except requests.exceptions.RequestException as exc:
        return None, [f"HTTP transport error: {type(exc).__name__}."]

    if response.status_code != 200:
        # Do not parse an error page as if it were a successful API response.
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            return None, [f"HTTP error: server returned status {response.status_code}."]

    try:
        return response.json(), errors
    except ValueError:
        return None, ["Invalid JSON response from API."]


def build_report(payload: Any, source: str) -> dict[str, Any]:
    rows, shape_errors = parse_payload(payload)
    records, invalid, validation_errors = validate_and_sanitize(rows)
    return {
        "source": source,
        "total_received": len(payload),
        "valid_records": len(records),
        "invalid_records": invalid + (len(shape_errors)),
        "records": records,
        "errors": shape_errors + validation_errors,
    }


def write_report(report: dict[str, Any], output: Path = REPORT_PATH) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true", help="use the built-in offline fixture")
    parser.add_argument("--fixture", type=Path, help="read JSON fixture (implies offline mode)")
    parser.add_argument("--url", default=API_URL, help="API URL (default: JSONPlaceholder users)")
    parser.add_argument("--limit", type=int, default=3, help="maximum records requested (1-10)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="request timeout in seconds")
    parser.add_argument("--output", type=Path, default=REPORT_PATH, help="report output path")
    args = parser.parse_args()

    if not 1 <= args.limit <= MAX_LIMIT:
        parser.error(f"--limit must be between 1 and {MAX_LIMIT}")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    if args.mock or args.fixture:
        try:
            if args.fixture:
                payload = json.loads(args.fixture.read_text(encoding="utf-8"))
            else:
                payload = MOCK_FIXTURE[:args.limit]
        except (OSError, ValueError) as exc:
            print(f"Fixture error: {type(exc).__name__}: {exc}")
            return 1
        source = "offline mock fixture"
        try:
            report = build_report(payload, source)
        except ValueError as exc:
            report = {
                "source": source, "total_received": 0, "valid_records": 0,
                "invalid_records": 0, "records": [], "errors": [str(exc)]
            }
    else:
        payload, fetch_errors = fetch_live(args.url, args.limit, args.timeout)
        if fetch_errors:
            report = {
                "source": SOURCE, "total_received": 0, "valid_records": 0,
                "invalid_records": 0, "records": [], "errors": fetch_errors
            }
        else:
            try:
                report = build_report(payload, SOURCE)
            except ValueError as exc:
                report = {
                    "source": SOURCE, "total_received": 0, "valid_records": 0,
                    "invalid_records": 0, "records": [], "errors": [str(exc)]
                }

    write_report(report, args.output)
    print(f"Report written: {args.output}")
    print(
        f"total_received={report['total_received']} "
        f"valid_records={report['valid_records']} "
        f"invalid_records={report['invalid_records']}"
    )
    for error in report["errors"]:
        print(f"ERROR: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
