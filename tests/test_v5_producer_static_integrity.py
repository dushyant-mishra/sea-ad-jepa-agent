"""Guards against the class of defect that cost a 35-minute extraction.

WHAT HAPPENED

  An availability mask was added to a FULL104 extractor by a series of
  programmatic source edits. One of them did not match its target and silently
  did nothing, so the block that built the `available` array was never
  inserted. The file still COMPILED, because the only reference to the missing
  name sat in a call executed at the very end of the script. The full run then
  extracted all thirteen operators, read and verified 8,076 blocks, and died at
  the save with `NameError: name 'available' is not defined`.

  A compile check cannot catch this. `compile()` resolves names at runtime, so
  a name that is never bound is perfectly valid syntax. A unit test on a helper
  cannot catch it either, because the defect lives on the final write path.

WHAT THESE TESTS DO

  1. UNDEFINED NAMES. A scope-aware walk over every v5 producer, flagging any
     name read but never bound in its function, the enclosing module, the
     imports or the builtins. This fails on exactly the defect above.

  2. BOUNDED-SLICE CONTRACT. Every producer whose run is measured in tens of
     minutes must expose a way to execute a small slice, so a real end-to-end
     smoke test is always possible before committing to the long run. A
     producer that can only be run at full scale cannot be rehearsed, and a
     defect on its write path is then only discoverable the expensive way.

  Both tests are written to be able to FAIL: test 1 is exercised against a
  fixture carrying the original bug, and test 2 names the flag it requires.
"""
from __future__ import annotations

import ast
import builtins
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
V5 = REPO / "scripts" / "v5"

# Producers whose full run is expensive enough that it must be rehearsable.
# The value is the set of flags, any one of which bounds the work.
COSTLY_PRODUCERS = {
    "full104_myeloid_panel_extraction_v1.py": {"--limit-operators", "--only-operators"},
    "full104_myeloid_panel_extraction_v2_decoded.py": {"--limit-operators", "--only-operators"},
    "full104_myeloid_panel_extraction_v3_masked.py": {"--limit-operators", "--only-operators"},
    "full104_level4_gene_identity_verifier_v1.py": {"--cells-per-block"},
    "full104_level4_permutation_recovery_v1.py": {"--min-nnz"},
    "full104_level4_column_decoder_v1.py": {"--verify-cells"},
}


class _Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.bound: set[str] = set()

    def binds(self, name: str) -> bool:
        s = self
        while s is not None:
            if name in s.bound:
                return True
            s = s.parent
        return False


def _bind_target(node, scope: _Scope) -> None:
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            scope.bound.add(n.id)
        elif isinstance(n, (ast.Starred, ast.Tuple, ast.List)):
            continue


def _collect_bindings(body, scope: _Scope) -> None:
    """Every way a name can come to exist in this scope."""
    for node in body:
        for n in ast.walk(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                scope.bound.add(n.name)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    _bind_target(t, scope)
            elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
                _bind_target(n.target, scope)
            elif isinstance(n, ast.NamedExpr):
                _bind_target(n.target, scope)
            elif isinstance(n, (ast.For, ast.AsyncFor)):
                _bind_target(n.target, scope)
            elif isinstance(n, (ast.comprehension,)):
                _bind_target(n.target, scope)
            elif isinstance(n, ast.withitem):
                if n.optional_vars is not None:
                    _bind_target(n.optional_vars, scope)
            elif isinstance(n, ast.ExceptHandler):
                if n.name:
                    scope.bound.add(n.name)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for al in n.names:
                    scope.bound.add((al.asname or al.name).split(".")[0])
            elif isinstance(n, (ast.Global, ast.Nonlocal)):
                scope.bound.update(n.names)


_NESTED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def _loads_in_own_scope(node):
    """Name loads belonging to THIS scope, not to any nested one.

    A nested function's parameters are bound in the nested scope, so counting
    them as loads of the enclosing scope produces false positives - which is
    what the first version of this check did, flagging `mask`, `obsv` and `s`
    in scripts that are correct. A check that cries wolf gets ignored, so it
    must not descend into nested scopes.
    """
    stack = list(ast.iter_child_nodes(node))
    while stack:
        n = stack.pop()
        if isinstance(n, _NESTED):
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            yield n
        stack.extend(ast.iter_child_nodes(n))


def _scope_for_function(node, parent: _Scope) -> _Scope:
    fs = _Scope(parent)
    a = node.args
    for arg in (a.posonlyargs + a.args + a.kwonlyargs):
        fs.bound.add(arg.arg)
    if a.vararg:
        fs.bound.add(a.vararg.arg)
    if a.kwarg:
        fs.bound.add(a.kwarg.arg)
    body = node.body if isinstance(node.body, list) else [node.body]
    _collect_bindings(body, fs)
    return fs


def _check_scope(node, scope: _Scope, bad: list) -> None:
    for n in _loads_in_own_scope(node):
        if not scope.binds(n.id):
            bad.append((n.id, n.lineno))
    # recurse into nested scopes with this scope as parent, so a closure
    # reading an enclosing local is correctly accepted
    stack = list(ast.iter_child_nodes(node))
    while stack:
        c = stack.pop()
        if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            _check_scope(c, _scope_for_function(c, scope), bad)
        elif isinstance(c, ast.ClassDef):
            cs = _Scope(scope)
            _collect_bindings(c.body, cs)
            _check_scope(c, cs, bad)
        else:
            stack.extend(ast.iter_child_nodes(c))


def undefined_names(source: str) -> list[tuple[str, int]]:
    tree = ast.parse(source)
    module = _Scope()
    module.bound.update(dir(builtins))
    module.bound.update({"__file__", "__name__", "__doc__", "__spec__"})
    _collect_bindings(tree.body, module)
    bad: list[tuple[str, int]] = []
    _check_scope(tree, module, bad)
    return bad


# --------------------------------------------------------------- the guards

def test_the_undefined_name_check_can_fail():
    """The control must fail on the real bug, or it certifies nothing."""
    buggy = (
        "import numpy as np\n"
        "def main():\n"
        "    counts = np.zeros(3)\n"
        "    np.savez('x', counts=counts, address_available=available)\n"
    )
    found = {name for name, _ in undefined_names(buggy)}
    assert "available" in found, (
        "the check did not flag the exact defect it exists for; it would have "
        "passed the extractor that died after 35 minutes")

    clean = (
        "import numpy as np\n"
        "def main():\n"
        "    counts = np.zeros(3)\n"
        "    available = np.ones(3, dtype=bool)\n"
        "    np.savez('x', counts=counts, address_available=available)\n"
    )
    assert not undefined_names(clean), "the check fires on correct source"


@pytest.mark.parametrize("path", sorted(V5.glob("*.py")), ids=lambda p: p.name)
def test_no_undefined_names_in_v5_producers(path):
    bad = undefined_names(path.read_text(encoding="utf-8"))
    assert not bad, (
        f"{path.name} reads names that are never bound: "
        + ", ".join(f"{n} (line {ln})" for n, ln in sorted(set(bad))[:10])
        + ". A programmatic source edit that silently did nothing produces "
          "exactly this, and it compiles.")


@pytest.mark.parametrize("name,flags", sorted(COSTLY_PRODUCERS.items()))
def test_costly_producers_can_be_rehearsed(name, flags):
    p = V5 / name
    if not p.exists():
        pytest.skip(f"{name} not present")
    src = p.read_text(encoding="utf-8")
    assert any(f in src for f in flags), (
        f"{name} exposes none of {sorted(flags)}, so it cannot be run on a "
        "small slice. A producer that cannot be rehearsed can only reveal a "
        "write-path defect by failing the expensive way.")
