"""R6 red cases for the external reviewer's three code-level findings.

Written before the repairs, and each one fails against the pre-R6 code. The
findings, in the reviewer's terms:

  1. the eligible-donor runner hardcodes `at8_availability_independently_
     verified=True`, so the AT8 availability package is trusted rather than
     replayed as a parent;
  2. age/sex is loaded from a package directory and its own root file rather
     than replayed against an expected external root;
  3. the default technical-completeness replay logs "recomputing the B1
     projection root" while reading the recorded value.

The shape common to 1 and 2 is circularity: reading a package's own
`*_PACKAGE_ROOT_SHA256.txt` and passing it back as the expected root lets the
package attest to itself, so a wholly substituted package whose root file agrees
with its own bytes is accepted.

Scope: this repository's own artifacts, in temporary directories. No pathology
value, no sealed input, no numeric AT8.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_eligible_donor_production_run_v1 as runner  # noqa: E402
import t0_technical_completeness_replay_v1 as tc_replay  # noqa: E402

AT8_PKG = ROOT / "outputs" / "t0_at8_availability_20260908"
AGE_SEX_PKG = ROOT / "outputs" / "t0_age_sex_20260908"
TC_PKG = ROOT / "outputs" / "t0_technical_completeness_20260909"

# The real roots, named here so a substituted package is detectable. These are
# the values an external reviewer would carry independently of the directory.
AT8_PACKAGE_ROOT = "3f74fa833bc1838a50d92bf3f6bdb55e6eafdb10b489fbfff142a4240466fc5a"
AT8_AVAILABILITY_ROOT = "e49c4e9365513d88d3afb687e452bc126dc3d39722384bc262557f84ee43523b"
AGE_SEX_PACKAGE_ROOT = "8212191a03f09d669a383be6a541b5ce3493b32c13608a76f197a88fa18ddf9b"
AGE_SEX_ROOT = "95ed8f75a42368f3308cf794dbab3c651a4467756147a49a937c5a881e1cffff"

pytestmark = pytest.mark.skipif(
    not (AT8_PKG.is_dir() and AGE_SEX_PKG.is_dir()),
    reason="the real parent packages are absent from this checkout")


def _copy(src: Path, dst: Path) -> Path:
    shutil.copytree(src, dst)
    return dst


def _restamp_at8(pkgdir: Path) -> None:
    """Rewrite the AT8 manifest and root file so the package agrees with itself.

    This is the whole point of the finding: a substituted package that is
    internally consistent must still be refused, because its identity has to
    come from outside the directory.
    """
    rows = [["filename", "bytes", "sha256"]]
    for name in ("T0_AT8_AVAILABILITY_REGISTRY.csv",
                 "T0_AT8_AVAILABILITY_METADATA.json"):
        blob = (pkgdir / name).read_bytes()
        rows.append([name, len(blob), hashlib.sha256(blob).hexdigest()])
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for row in rows:
        writer.writerow(row)
    manifest = buf.getvalue().encode("utf-8")
    (pkgdir / "T0_AT8_AVAILABILITY_MANIFEST.csv").write_bytes(manifest)
    (pkgdir / "T0_AT8_AVAILABILITY_PACKAGE_ROOT_SHA256.txt").write_text(
        hashlib.sha256(manifest).hexdigest() + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Finding 1. The AT8 availability package must be replayed, not trusted.
# ---------------------------------------------------------------------------

def test_a_substituted_at8_package_that_agrees_with_itself_is_refused(
        tmp_path) -> None:
    """RED before R6: the loader read the package's own root file."""
    pkg = _copy(AT8_PKG, tmp_path / "at8")
    registry = pkg / "T0_AT8_AVAILABILITY_REGISTRY.csv"
    text = registry.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Flip one donor's availability, then make the package self-consistent.
    flipped = [lines[0]] + [
        (line.replace(",True", ",False") if i == 0 else line)
        for i, line in enumerate(lines[1:])]
    registry.write_text("\n".join(flipped) + "\n", encoding="utf-8")
    _restamp_at8(pkg)

    with pytest.raises(AssertionError) as excinfo:
        runner.load_at8_availability(pkg)
    message = str(excinfo.value)
    assert "EXTERNAL_ROOT" in message or "ROOT" in message


def test_the_at8_verification_flag_is_not_a_hardcoded_true(tmp_path) -> None:
    """RED before R6: the runner passed at8_..._independently_verified=True."""
    loaded = runner.load_at8_availability(AT8_PKG)
    # The loader must report what it actually verified, by root, rather than the
    # caller asserting verification on its behalf.
    assert loaded.get("independently_verified") is True
    assert loaded.get("availability_root_sha256") == AT8_AVAILABILITY_ROOT
    assert loaded.get("package_root_sha256") == AT8_PACKAGE_ROOT
    assert loaded.get("expected_roots_supplied_externally") is True


def test_the_runner_does_not_hardcode_the_verification_flag() -> None:
    """The literal the reviewer named must be gone from the runner."""
    source = (ROOT / "scripts" / "v4"
              / "t0_eligible_donor_production_run_v1.py").read_text(
                  encoding="utf-8")
    assert "at8_availability_independently_verified=True" not in source


# ---------------------------------------------------------------------------
# Finding 2. Age/sex must be replayed against an expected external root.
# ---------------------------------------------------------------------------

def test_a_substituted_age_sex_package_is_refused(tmp_path) -> None:
    """RED before R6: presence booleans came from an unreplayed registry."""
    pkg = _copy(AGE_SEX_PKG, tmp_path / "agesex")
    registry = pkg / "T0_AGE_SEX_REGISTRY.csv"
    lines = registry.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[1] = str(int(cells[1]) + 1)          # shift one donor's age
    lines[1] = ",".join(cells)
    registry.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(AssertionError) as excinfo:
        runner.load_age_sex_presence(pkg)
    assert "ROOT" in str(excinfo.value) or "MISMATCH" in str(excinfo.value)


def test_age_sex_presence_reports_the_roots_it_verified() -> None:
    """RED before R6: only the package's own root file was read back."""
    loaded = runner.load_age_sex_presence(AGE_SEX_PKG)
    assert loaded.get("age_sex_root_sha256") == AGE_SEX_ROOT
    assert loaded.get("package_root_sha256") == AGE_SEX_PACKAGE_ROOT
    assert loaded.get("independently_verified") is True
    assert loaded.get("expected_roots_supplied_externally") is True
    # Still no covariate value leaves the loader.
    serialised = json.dumps(loaded, sort_keys=True)
    assert "Female" not in serialised and "Male" not in serialised


# ---------------------------------------------------------------------------
# Finding 3. The default TC replay must not claim work it did not do.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not TC_PKG.is_dir(),
                    reason="the technical-completeness package is absent")
def test_the_default_tc_replay_does_not_claim_to_recompute_the_projection(
) -> None:
    """RED before R6: the log line asserted a recomputation it did not perform.

    The check is on the emitted report rather than on log text, so it survives
    rewording: the report must say whether the projection root was recomputed
    from a supplied feature split or merely read from the run summary.
    """
    source = (ROOT / "scripts" / "v4"
              / "t0_technical_completeness_replay_v1.py").read_text(
                  encoding="utf-8")
    assert 'log("recomputing the B1 projection root")' not in source
    assert "projection_root_recomputed_from_feature_split" in source


@pytest.mark.skipif(not TC_PKG.is_dir(),
                    reason="the technical-completeness package is absent")
def test_a_tampered_projection_root_in_the_summary_is_detected(
        tmp_path) -> None:
    """RED before R6: nothing compared the recorded projection root to anything.

    Without a supplied feature split the replay cannot recompute the projection,
    so it must at minimum refuse a summary whose recorded projection root is not
    the frozen one rather than passing it through into its own report.
    """
    pkg = _copy(TC_PKG, tmp_path / "tc")
    summary_path = pkg / "T0_TECHNICAL_COMPLETENESS_RUN_SUMMARY.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["projection_root_sha256"] = "0" * 64
    with io.open(summary_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    with pytest.raises(AssertionError) as excinfo:
        tc_replay.assert_projection_root_is_frozen(summary)
    assert "PROJECTION" in str(excinfo.value)
