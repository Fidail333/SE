from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

from data.urls import SMOKE_URLS_COUNT, URL_CASES

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
DESKTOP_FULLNAME_HINT = "tests.ui.test_desktop_url_matrix"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Allure results for desktop URL matrix: expected volume, skipped cases, "
            "and Cyrillic steps presence."
        )
    )
    parser.add_argument("--mode", choices=("smoke", "regression"), required=True)
    parser.add_argument("--results-dir", default="allure-results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    result_files = sorted(results_dir.glob("*-result.json"))

    if not result_files:
        print(f"No Allure result files found in {results_dir}")
        return 1

    results = []
    for file_path in result_files:
        try:
            results.append(json.loads(file_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in {file_path}: {exc}")
            return 1

    desktop_results = [result for result in results if is_desktop_result(result)]
    if not desktop_results:
        print("No desktop test results found. Expected tests/ui/test_desktop_url_matrix.py results.")
        return 1

    expected_min = SMOKE_URLS_COUNT if args.mode == "smoke" else len(URL_CASES)
    if len(desktop_results) < expected_min:
        print(
            "Desktop results count is too low: "
            f"got {len(desktop_results)}, expected at least {expected_min} for mode={args.mode}."
        )
        return 1

    skipped = [result_name(result) for result in desktop_results if result.get("status") == "skipped"]
    if skipped:
        print("Desktop tests contain skipped cases:")
        for item in skipped:
            print(f" - {item}")
        return 1

    without_steps = []
    without_cyrillic_steps = []
    for result in desktop_results:
        step_names = list(iter_step_names(result.get("steps", [])))
        if not step_names:
            without_steps.append(result_name(result))
            continue

        if not any(CYRILLIC_RE.search(step_name or "") for step_name in step_names):
            without_cyrillic_steps.append(result_name(result))

    if without_steps:
        print("Desktop tests without steps:")
        for item in without_steps:
            print(f" - {item}")
        return 1

    if without_cyrillic_steps:
        print("Desktop tests without Cyrillic steps:")
        for item in without_cyrillic_steps:
            print(f" - {item}")
        return 1

    print(
        "Allure validation passed: "
        f"desktop_results={len(desktop_results)}, mode={args.mode}, expected_min={expected_min}."
    )
    return 0


def is_desktop_result(result: dict[str, Any]) -> bool:
    full_name = str(result.get("fullName", ""))
    if DESKTOP_FULLNAME_HINT in full_name:
        return True

    for label in result.get("labels", []):
        if label.get("name") == "tag" and label.get("value") == "desktop":
            return True

    return False


def iter_step_names(steps: Iterable[dict[str, Any]]) -> Iterable[str]:
    for step in steps:
        name = step.get("name")
        if isinstance(name, str) and name:
            yield name

        child_steps = step.get("steps", [])
        if isinstance(child_steps, list):
            yield from iter_step_names(child_steps)


def result_name(result: dict[str, Any]) -> str:
    return str(result.get("fullName") or result.get("name") or "<unknown>")


if __name__ == "__main__":
    raise SystemExit(main())
