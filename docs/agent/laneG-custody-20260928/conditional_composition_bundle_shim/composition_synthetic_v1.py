"""Loader shim for the missing `composition_synthetic_v1` module.

SUCCESSOR ARTIFACT -- Lane G custody, 2026-09-28. Creates nothing new
scientifically; it only repairs an import-path packaging defect.

THE DEFECT
----------
The portable bundle `chat_local_evidence/jepa_conditional_composition_cpu_20260928/`
(inside `JEPA_CHAT_LOCAL_ONLY_EVIDENCE_20260928.zip`,
sha256 83ab489570ffd863a6a9c9e54ebc85cd84e0c769948f15e27427a7d3137da873)
lists `composition_synthetic_v1.py` in its own `SHA256_MANIFEST.json`
(size 7711, sha256 989702cf...) but does NOT ship the file in that directory.
The file was packaged into the SIBLING bundle directory
`chat_local_evidence/JEPA_LOCAL_COMPLETION_20260928/`.

Consequently every documented reproduction step that imports the module by
NAME fails, because the module is only reachable by PATH:

    test_new_workstream.py:8   from composition_synthetic_v1 import ...
    composition_grid_v1.py:7   from composition_synthetic_v1 import ...

THE FIX
-------
Put the directory containing this shim on PYTHONPATH (or copy this file beside
the bundle). `import composition_synthetic_v1` then resolves to this shim,
which locates the real implementation file, verifies its SHA-256 against the
bundle's own manifest, and re-exports its public namespace.

FAIL-CLOSED
-----------
If the implementation cannot be found, or is found but its SHA-256 does not
match the manifest value, this shim raises ImportError. It never silently
substitutes a different copy and never fabricates the module.

Override the search with the environment variable
`JEPA_COMPOSITION_SYNTHETIC_V1` pointing at the implementation file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import runpy
import sys
from pathlib import Path

# Digest asserted by the source bundle's own SHA256_MANIFEST.json.
EXPECTED_SHA256 = "989702cfbe78b151b410b625bf1a59cdf83577ac92827e65f0e8f08c5f0a8058"
EXPECTED_BYTES = 7711
IMPL_BASENAME = "composition_synthetic_v1.py"
SIBLING_BUNDLE = "JEPA_LOCAL_COMPLETION_20260928"
_IMPL_MODULE_NAME = "_composition_synthetic_v1_impl"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _candidates() -> list[Path]:
    """Ordered search locations for the real implementation file."""
    out: list[Path] = []
    env = os.environ.get("JEPA_COMPOSITION_SYNTHETIC_V1")
    if env:
        out.append(Path(env))
    here = Path(__file__).resolve().parent
    roots = [here, here.parent, Path.cwd(), Path.cwd().parent]
    for root in roots:
        out.append(root / SIBLING_BUNDLE / IMPL_BASENAME)
        out.append(root.parent / SIBLING_BUNDLE / IMPL_BASENAME)
    # de-duplicate, preserve order
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        key = str(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def resolve_impl() -> Path:
    """Return the verified implementation path, or raise ImportError."""
    tried: list[str] = []
    mismatched: list[str] = []
    for cand in _candidates():
        tried.append(str(cand))
        if not cand.is_file():
            continue
        digest = _sha256(cand)
        if digest != EXPECTED_SHA256:
            mismatched.append(f"{cand} sha256={digest}")
            continue
        return cand
    msg = [
        "composition_synthetic_v1 implementation not resolved (fail-closed).",
        f"expected sha256={EXPECTED_SHA256} ({EXPECTED_BYTES} bytes)",
        "searched:",
        *[f"  - {t}" for t in tried],
    ]
    if mismatched:
        msg += ["found but DIGEST MISMATCH (refused):", *[f"  - {m}" for m in mismatched]]
    msg.append(
        "Set JEPA_COMPOSITION_SYNTHETIC_V1 to the implementation file, or extract "
        f"{SIBLING_BUNDLE}/ beside the conditional-composition bundle."
    )
    raise ImportError("\n".join(msg))


IMPL_PATH = resolve_impl()

_spec = importlib.util.spec_from_file_location(_IMPL_MODULE_NAME, IMPL_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot build import spec for {IMPL_PATH}")
_impl = importlib.util.module_from_spec(_spec)
sys.modules[_IMPL_MODULE_NAME] = _impl
_spec.loader.exec_module(_impl)

# Re-export the implementation's public namespace under this module name.
_EXPORTED = [n for n in vars(_impl) if not n.startswith("_")]
globals().update({n: getattr(_impl, n) for n in _EXPORTED})
__all__ = sorted(_EXPORTED)

if __name__ == "__main__":
    # Delegate the documented CLI to the real implementation, as __main__.
    runpy.run_path(str(IMPL_PATH), run_name="__main__")
