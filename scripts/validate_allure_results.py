from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.urls import SMOKE_URLS_COUNT, URL_CASES
from utils.failure_taxonomy import UNCATEGORIZED_KEY, classify_failure_text

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
DESKTOP_FULLNAME_HINT = "tests.ui.test_desktop_url_matrix"
DEFAULT_REQUIRED_STEPS = "антибот,базовую,seo,контентные,js/network"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Allure results for desktop URL matrix: expected volume, required steps, "
            "Cyrillic steps, and failure taxonomy quality."
        )
    )
    parser.add_argument("--mode", choices=("smoke", "regression"), required=True)
    parser.add_argument("--env", required=True, help="Execution environment label (prod/env0/env3).")
    parser.add_argument("--results-dir", default="allure-results")
    parser.add_argument(
        "--require-steps",
        default=DEFAULT_REQUIRED_STEPS,
        help="Comma-separated lowercase substrings that must be present in step names for each desktop test.",
    )
    parser.add_argument(
        "--max-uncategorized-rate",
        type=float,
        default=0.05,
        help="Maximum allowed ratio of uncategorized failures among failed/broken desktop tests.",
    )
    parser.add_argument(
        "--summary-out",
        default="",
        help="Path to write validation summary JSON (defaults to allure-results/validation-summary-<env>-<mode>.json).",
    )
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

    desktop_candidates = [result for result in results if is_desktop_result(result)]
    if not desktop_candidates:
        print("No desktop test results found. Expected tests/ui/test_desktop_url_matrix.py results.")
        return 1

    desktop_results = filter_by_env(desktop_candidates, env=args.env)
    if not desktop_results:
        print(f"No desktop test results for env='{args.env}'.")
        return 1

    expected_min = SMOKE_URLS_COUNT if args.mode == "smoke" else len(URL_CASES)
    if len(desktop_results) < expected_min:
        print(
            "Desktop results count is too low: "
            f"got {len(desktop_results)}, expected at least {expected_min} for mode={args.mode}, env={args.env}."
        )
        return 1

    skipped = [result_name(result) for result in desktop_results if result.get("status") == "skipped"]
    if skipped:
        print("Desktop tests contain skipped cases:")
        for item in skipped:
            print(f" - {item}")
        return 1

    required_step_fragments = [item.strip().lower() for item in args.require_steps.split(",") if item.strip()]
    without_steps = []
    without_cyrillic_steps = []
    without_required_steps = []

    for result in desktop_results:
        step_names_raw = list(iter_step_names(result.get("steps", [])))
        step_names = [name.lower() for name in step_names_raw]
        if not step_names:
            without_steps.append(result_name(result))
            continue

        if not any(CYRILLIC_RE.search(step_name) for step_name in step_names_raw):
            without_cyrillic_steps.append(result_name(result))

        missing_fragments = [fragment for fragment in required_step_fragments if not any(fragment in name for name in step_names)]
        if missing_fragments:
            without_required_steps.append((result_name(result), missing_fragments))

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

    if without_required_steps:
        print("Desktop tests with missing required step packs:")
        for item, missing in without_required_steps:
            print(f" - {item}: missing={', '.join(missing)}")
        return 1

    failed_or_broken = [
        result for result in desktop_results if result.get("status") in {"failed", "broken"}
    ]
    taxonomy_counter: Counter[str] = Counter()
    failure_examples: dict[str, list[str]] = {}
    for result in failed_or_broken:
        message = status_message(result)
        category = classify_failure_text(message)
        taxonomy_counter[category] += 1
        failure_examples.setdefault(category, [])
        if len(failure_examples[category]) < 5:
            failure_examples[category].append(result_name(result))

    failures_total = len(failed_or_broken)
    uncategorized_count = taxonomy_counter.get(UNCATEGORIZED_KEY, 0)
    uncategorized_rate = (uncategorized_count / failures_total) if failures_total else 0.0
    if uncategorized_rate > args.max_uncategorized_rate:
        print(
            "Too many uncategorized failures: "
            f"{uncategorized_count}/{failures_total} ({uncategorized_rate:.2%}) > {args.max_uncategorized_rate:.2%}"
        )
        return 1

    status_counter = Counter(str(result.get("status", "unknown")) for result in desktop_results)
    summary = {
        "env": args.env,
        "mode": args.mode,
        "expected_min": expected_min,
        "desktop_results": len(desktop_results),
        "status_counts": dict(status_counter),
        "taxonomy_counts": dict(taxonomy_counter),
        "uncategorized_rate": round(uncategorized_rate, 6),
        "required_step_fragments": required_step_fragments,
        "top_failure_examples": failure_examples,
        "top_failing_urls": top_failing_urls(failed_or_broken),
    }
    summary_path = (
        Path(args.summary_out)
        if args.summary_out
        else results_dir / f"validation-summary-{args.env}-{args.mode}.json"
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "Allure validation passed: "
        f"desktop_results={len(desktop_results)}, env={args.env}, mode={args.mode}, "
        f"uncategorized_rate={uncategorized_rate:.2%}."
    )
    print(f"Summary saved to {summary_path}")
    return 0


def is_desktop_result(result: dict[str, Any]) -> bool:
    full_name = str(result.get("fullName", ""))
    if DESKTOP_FULLNAME_HINT in full_name:
        return True

    for label in result.get("labels", []):
        if label.get("name") == "tag" and label.get("value") == "desktop":
            return True

    return False


def filter_by_env(results: list[dict[str, Any]], env: str) -> list[dict[str, Any]]:
    tagged = [result for result in results if extract_env_label(result)]
    if not tagged:
        return results
    return [result for result in tagged if extract_env_label(result) == env]


def extract_env_label(result: dict[str, Any]) -> str:
    for label in result.get("labels", []):
        if label.get("name") == "test_env":
            return str(label.get("value", "")).strip().lower()
    return ""


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


def status_message(result: dict[str, Any]) -> str:
    details = result.get("statusDetails") or {}
    message = details.get("message")
    if isinstance(message, str):
        return message
    return ""


def top_failing_urls(results: list[dict[str, Any]], limit: int = 10) -> list[dict[str, int]]:
    counter: Counter[str] = Counter()
    for result in results:
        name = str(result.get("name", ""))
        case = name.split(": ", 1)[1].strip() if ": " in name else name
        if case:
            counter[case] += 1
    return [{"case": case, "count": count} for case, count in counter.most_common(limit)]


if __name__ == "__main__":
    raise SystemExit(main())
