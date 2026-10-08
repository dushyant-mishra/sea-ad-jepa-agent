"""Make `src/` importable so test collection cannot silently run zero tests.

WHY THIS FILE EXISTS

  tests/test_regulatory_exposure_ledger_v1.py does
  `from sea_ad_jepa.regulatory.regulatory_exposure_ledger_v1 import *`.
  With a bare `pytest`, that raises ModuleNotFoundError at COLLECTION time:

      ModuleNotFoundError: No module named 'sea_ad_jepa.regulatory'
      Interrupted: 1 error during collection

  A collection error runs ZERO tests. On a runner that does not treat a
  nonzero exit as fatal, or in a summary that only counts failures, that reads
  as "no failures" while nothing was checked. The suite passes 7/7 only when
  invoked as `PYTHONPATH=src pytest`, which is an environment property rather
  than a property of the repository.

  This is the third instance of that failure class recorded in this project:
  the V29 census tests were listed as CI path triggers with no step executing
  them, and the conditional-composition portable bundle's collection error made
  four test files run nothing. Putting the path on sys.path at conftest level
  makes the bare command correct, so the suite cannot pass by not running.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
