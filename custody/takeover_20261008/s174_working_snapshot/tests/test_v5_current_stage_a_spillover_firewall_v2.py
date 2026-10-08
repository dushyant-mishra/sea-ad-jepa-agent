"""Adversarial hardening of the V5 Stage-A spillover firewall.

Independent audit of the v1 firewall found four coverage gaps. None of them was
hiding a live contamination at d0909dec -- the runtime isolation genuinely holds --
but each left the invariant unprotected against reintroduction:

  1. the v1 AST extractor detected only ONE of four import forms
  2. the v1 AST check was one file deep, not transitive
  3. the v1 runtime check imported a SINGLE authority module
  4. the v1 runtime check inspected 2 of the 13 quarantined modules

This module closes all four. It imports the v1 helpers so the two files cannot
drift apart.
"""
from __future__ import annotations

import ast
import itertools
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_v5_current_stage_a_spillover_firewall_v1 import (  # noqa: E402
    CURRENT_STAGE_A_SOURCE_PATHS,
    QUARANTINED_V5_MODULES,
    ROOT,
    V5,
    _local_imports,
)


def _clean_env() -> dict:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=_clean_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


# --------------------------------------------------------------------------
# Gap 1: the static extractor must recognise every import form that can
# actually reach a quarantined module. `from sea_ad_jepa.v5 import X` matters
# especially, because the new package __getattr__ makes that form resolve.
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "source",
    [
        "from .data_first_geometry import PackedValidTokens",
        "from . import data_first_geometry",
        "from sea_ad_jepa.v5 import proposal_policy_v1",
        "import sea_ad_jepa.v5.data_first_geometry",
        "from importlib import import_module\nm = import_module('.data_first_geometry', __package__)",
    ],
    ids=["from-submodule", "from-dot-import", "absolute-from-package", "plain-import", "dynamic-import-module"],
)
def test_static_extractor_detects_every_reachable_import_form(source: str, tmp_path: Path) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text(source, encoding="utf-8")
    detected = _local_imports(probe)
    assert detected & QUARANTINED_V5_MODULES, (
        f"import form evades the firewall's static check: {source!r} -> {sorted(detected)}"
    )


# --------------------------------------------------------------------------
# Gap 2: transitive reachability, not one file deep.
# --------------------------------------------------------------------------
def _v5_import_graph() -> dict:
    return {p.stem: _local_imports(p) for p in V5.glob("*.py")}


def test_no_stage_a_module_transitively_reaches_a_quarantined_module() -> None:
    graph = _v5_import_graph()
    violations: dict = {}
    for filename in CURRENT_STAGE_A_SOURCE_PATHS:
        start = Path(filename).stem
        seen, stack = set(), [start]
        while stack:
            cur = stack.pop()
            for nxt in graph.get(cur, set()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        bad = sorted(seen & QUARANTINED_V5_MODULES)
        if bad:
            violations[filename] = bad
    assert violations == {}, f"transitive quarantined reachability: {violations}"


# --------------------------------------------------------------------------
# Gap 3 + 4: every Stage-A module, in its own clean interpreter, checked
# against all thirteen quarantined modules.
# --------------------------------------------------------------------------
_PROBE = """
import sys, json
import sea_ad_jepa.v5.{mod}
q = {q!r}
print(json.dumps(sorted(
    n.split('.')[-1] for n in sys.modules
    if n.startswith('sea_ad_jepa.v5.') and n.split('.')[-1] in q
)))
"""


@pytest.mark.parametrize("module", [Path(p).stem for p in CURRENT_STAGE_A_SOURCE_PATHS])
def test_each_stage_a_module_loads_no_quarantined_module(module: str) -> None:
    result = _run(_PROBE.format(mod=module, q=sorted(QUARANTINED_V5_MODULES)))
    if result.returncode != 0:
        pytest.skip(f"module not importable in this environment: {result.stdout.strip()[-200:]}")
    loaded = json.loads(result.stdout.strip().splitlines()[-1])
    assert loaded == [], f"{module} eagerly loaded quarantined modules: {loaded}"


def test_import_order_does_not_leak_quarantined_modules() -> None:
    mods = [Path(p).stem for p in CURRENT_STAGE_A_SOURCE_PATHS][:5]
    checked = 0
    for perm in itertools.islice(itertools.permutations(mods, 3), 8):
        body = "import sys, json\n" + "".join(f"import sea_ad_jepa.v5.{m}\n" for m in perm)
        body += (
            f"q = {sorted(QUARANTINED_V5_MODULES)!r}\n"
            "print(json.dumps(sorted(n.split('.')[-1] for n in sys.modules "
            "if n.startswith('sea_ad_jepa.v5.') and n.split('.')[-1] in q)))\n"
        )
        result = _run(body)
        if result.returncode != 0:
            continue
        loaded = json.loads(result.stdout.strip().splitlines()[-1])
        assert loaded == [], f"order {perm} leaked: {loaded}"
        checked += 1
    assert checked > 0, "no import-order permutation executed; the assertion would be vacuous"


def test_bare_package_import_loads_no_v5_submodule_at_all() -> None:
    result = _run(
        "import sys, json\n"
        "import sea_ad_jepa.v5\n"
        "print(json.dumps(sorted(n for n in sys.modules if n.startswith('sea_ad_jepa.v5.'))))\n"
    )
    assert result.returncode == 0, result.stdout
    loaded = json.loads(result.stdout.strip().splitlines()[-1])
    assert loaded == [], f"package init loaded submodules: {loaded}"
