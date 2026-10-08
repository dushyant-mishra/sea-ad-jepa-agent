#!/usr/bin/env python3
"""Focused golden/metamorphic tests for the repaired shared-D selector."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd

from correct_full104_phase2_shared_selection_with_refit_null import leading_supported_dimensions


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def independent_leading_prefix(dimensions: list[int], support: list[bool], rank: int) -> list[int]:
    """Second implementation; intentionally does not call the production helper."""
    lookup = {int(d): bool(value) for d, value in zip(dimensions, support)}
    result: list[int] = []
    dimension = 1
    while dimension <= rank and lookup.get(dimension, False):
        result.append(dimension)
        dimension += 1
    return result


def one_se(prefix: list[int], means: dict[int, float], ses: dict[int, float]) -> int | None:
    if not prefix:
        return None
    best = max(prefix, key=lambda d: means[d])
    threshold = means[best] - ses[best]
    return min(d for d in prefix if means[d] >= threshold)


def exercise(dimensions: list[int], support: list[bool], rank: int) -> tuple[list[int], list[int]]:
    series = pd.Series(support, index=dimensions, dtype=bool)
    return leading_supported_dimensions(series, rank), independent_leading_prefix(dimensions, support, rank)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)

    tests = []

    dimensions = list(range(1, 14))
    support = [True] * 5 + [False] + [True] * 7
    prod, independent = exercise(dimensions, support, 13)
    tests.append({"test": "gapped_support", "expected": [1, 2, 3, 4, 5], "production": prod, "independent": independent, "pass": prod == independent == [1, 2, 3, 4, 5]})

    support = [False] + [True] * 12
    prod, independent = exercise(dimensions, support, 13)
    tests.append({"test": "first_dimension_failure", "expected": [], "production": prod, "independent": independent, "pass": prod == independent == []})

    planted_rank = 7
    support = [d <= planted_rank for d in dimensions]
    prod, independent = exercise(dimensions, support, 13)
    means = {d: 0.10 + 0.01 * min(d, 5) for d in dimensions}
    ses = {d: 0.015 for d in dimensions}
    selected_prod = one_se(prod, means, ses)
    selected_independent = one_se(independent, means, ses)
    tests.append({"test": "contiguous_planted_rank_one_se", "planted_rank": planted_rank, "production_selected": selected_prod, "independent_selected": selected_independent, "pass": prod == independent == list(range(1, planted_rank + 1)) and selected_prod == selected_independent and selected_prod <= planted_rank})

    rng = np.random.default_rng(20260829)
    shuffled = rng.permutation(len(dimensions))
    prod_reordered, independent_reordered = exercise([dimensions[i] for i in shuffled], [support[i] for i in shuffled], 13)
    chunked_dimensions, chunked_support = [], []
    for start in range(0, len(dimensions), 4):
        chunked_dimensions.extend(dimensions[start:start + 4])
        chunked_support.extend(support[start:start + 4])
    prod_chunked, independent_chunked = exercise(chunked_dimensions, chunked_support, 13)
    tests.append({"test": "order_and_chunk_metamorphic", "production_reordered": prod_reordered, "production_chunked": prod_chunked, "independent_reordered": independent_reordered, "independent_chunked": independent_chunked, "pass": prod_reordered == prod_chunked == independent_reordered == independent_chunked == list(range(1, planted_rank + 1))})

    production_source = inspect.getsource(leading_supported_dimensions)
    independent_source = inspect.getsource(independent_leading_prefix)
    independence_pass = "leading_supported_dimensions(" not in independent_source and production_source != independent_source
    tests.append({"test": "implementation_independence", "production_sha256": hashlib.sha256(production_source.encode()).hexdigest(), "independent_sha256": hashlib.sha256(independent_source.encode()).hexdigest(), "pass": independence_pass})

    passed = all(item["pass"] for item in tests)
    report = {
        "schema": "shared-d-selector-harness-v2",
        "status": "PASS_SHARED_D_HARNESS_V2" if passed else "STOP_SHARED_D_HARNESS_V2",
        "result_state": "QUALIFIED" if passed else "INVALIDATED",
        "tests": tests,
        "production_selector": str(Path(inspect.getsourcefile(leading_supported_dimensions)).resolve()),
        "independent_selector": str(Path(__file__).resolve()),
        "input_hashes": {
            "production_selector_file": sha(Path(inspect.getsourcefile(leading_supported_dimensions))),
            "harness_code": sha(Path(__file__)),
        },
    }
    path = out / "SHARED_D_HARNESS_V2_TEST_REPORT.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report_sha256": sha(path)}, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
