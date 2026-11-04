from __future__ import annotations

import ast
import json
from pathlib import Path


MATRIX = Path("results/target_discovery/unified_qualification_v1/TASK4_ATTACK_MATRIX_V1.json")


def test_attack_matrix_has_at_least_36_unique_attacks_and_no_authority_effect():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    attacks = data["attacks"]
    assert data["authority_effect"] == "NONE"
    assert data["minimum_required_attacks"] == 36
    assert len(attacks) >= 36
    assert len({row["attack_id"] for row in attacks}) == len(attacks)
    assert len({(row["test_file"], row["test_name"]) for row in attacks}) == len(attacks)


def test_every_attack_matrix_reference_points_to_executable_test_function():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    cache = {}
    for row in data["attacks"]:
        path = Path(row["test_file"])
        assert path.exists(), row
        if path not in cache:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            cache[path] = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert row["test_name"] in cache[path], row
