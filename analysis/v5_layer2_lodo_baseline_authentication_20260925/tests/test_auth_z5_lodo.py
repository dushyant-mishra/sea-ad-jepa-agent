"""Adversarial tests for the Layer-2 LODO baseline authenticator.

The point of these tests is NOT to show that the authenticator returns PASS.  It
currently returns a refusal, and a refusal is easy to produce by accident -- a
typo in a path would produce one too.  These tests exist to show the authenticator
is capable of BOTH outcomes, so that the refusal it actually emitted carries
information.

Each test therefore drives a mechanism to an outcome opposite to the one observed
in the real run, or drives it to failure deliberately.

Run:  python test_auth_z5_lodo.py       (no pytest needed)
  or: pytest test_auth_z5_lodo.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import auth_z5_lodo as A  # noqa: E402

REPO = Path(__file__).resolve().parents[3]


# --------------------------------------------------------------------------
# 1. The digest check is live in BOTH directions.
# --------------------------------------------------------------------------

def test_match_is_reachable_not_just_absent():
    """A file whose bytes really do hash to the declared digest reports MATCH.

    Without this, 'ABSENT everywhere' could be a stuck output rather than a
    measurement.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        payload = b"bind_population placeholder bytes"
        (root / "bind_population.npz").write_bytes(payload)
        saved = A.DECLARED_INPUTS["bind_population.npz"]["sha256"]
        try:
            A.DECLARED_INPUTS["bind_population.npz"]["sha256"] = \
                hashlib.sha256(payload).hexdigest()
            rep = A.authenticate_inputs([root])
        finally:
            A.DECLARED_INPUTS["bind_population.npz"]["sha256"] = saved
        assert rep["bind_population.npz"]["status"] == "MATCH", rep


def test_tampered_bytes_report_digest_mismatch():
    """A file with the right NAME but wrong bytes must not authenticate."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "bind_population.npz").write_bytes(b"not the real artifact")
        rep = A.authenticate_inputs([root])
        assert rep["bind_population.npz"]["status"] == "DIGEST_MISMATCH", rep


def test_right_size_wrong_content_still_fails():
    """The 'do not substitute a similar-looking file' guard.

    A decoy of EXACTLY the declared byte length must still be rejected, so the
    check cannot be satisfied by matching metadata instead of content.
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        n = A.DECLARED_INPUTS["bind_population.npz"]["size_bytes"]
        (root / "bind_population.npz").write_bytes(b"\x00" * n)
        rep = A.authenticate_inputs([root])
        e = rep["bind_population.npz"]
        assert e["status"] == "DIGEST_MISMATCH", e
        assert Path(e["candidates_found"][0]).stat().st_size == n


def test_absent_input_reports_absent():
    with tempfile.TemporaryDirectory() as td:
        rep = A.authenticate_inputs([Path(td)])
        for name, e in rep.items():
            assert e["status"] == "ABSENT", (name, e)
            assert e["found_sha256"] is None


# --------------------------------------------------------------------------
# 2. The refusal to replay is enforced, and is not bypassable.
# --------------------------------------------------------------------------

def test_unauthenticated_inputs_block_replay_and_record_unmeasured():
    with tempfile.TemporaryDirectory() as td:
        r = A.build_receipt(REPO, [Path(td)], skip_substrate_hash=True)
        assert r["verdict"] == "PENDING_PHYSICAL_INPUT_AUTHENTICATION"
        assert r["replay"]["executed"] is False
        # An unmeasured quantity is recorded as UNMEASURED, never estimated.
        assert r["replay"]["replayed_r2"] == "UNMEASURED"
        assert r["replay"]["deltas_vs_historical"] == "UNMEASURED"


def test_one_missing_input_is_enough_to_refuse():
    """Three of four inputs authenticating must NOT produce AUTHENTICATED."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        saved = {}
        try:
            for name in ("bind_population.npz", "screen_out.npz", "final_manifest.csv"):
                payload = ("stand-in for " + name).encode()
                (root / name).write_bytes(payload)
                saved[name] = A.DECLARED_INPUTS[name]["sha256"]
                A.DECLARED_INPUTS[name]["sha256"] = hashlib.sha256(payload).hexdigest()
            # y_source.json deliberately left absent
            r = A.build_receipt(REPO, [root], skip_substrate_hash=True)
        finally:
            for name, d in saved.items():
                A.DECLARED_INPUTS[name]["sha256"] = d
        assert r["physical_input_authentication"]["y_source.json"]["status"] == "ABSENT"
        assert r["verdict"] == "PENDING_PHYSICAL_INPUT_AUTHENTICATION"
        assert r["replay"]["executed"] is False


# --------------------------------------------------------------------------
# 3. The replay, if it ever runs, is a faithful replay.
# --------------------------------------------------------------------------

def test_repoint_changes_exactly_one_line_and_no_estimator_constant():
    src = A.git_show(REPO, A.HISTORICAL_COMMIT,
                     A.ANALYSIS_DIR + "/scripts/z5_lodo.py").decode()
    out = A.repoint(src, Path("X:/somewhere"))
    a, b = src.splitlines(), out.splitlines()
    assert len(a) == len(b)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(diff) == 1, diff
    assert a[diff[0]].startswith("S = pathlib.Path(")
    # the estimator, the ridge penalty, the dimensionality and the population
    # filter must be untouched
    for token in ("LAM = 1e-2", "np.eye(256)", "np.linalg.solve",
                  "pd.factorize(dc_all[m])[0]", "p100_v0", "p100_v1",
                  "['HVS', 'NPH52', 'SEA_AD', 'ALL']"):
        assert src.count(token) == out.count(token), token
        assert token in out, token


def test_repoint_survives_a_windows_backslash_path():
    r"""Regression: the real scratchpad path is a Windows path, so the repointed
    directory reaches re.subn full of backslashes.  With a STRING replacement
    those are read as regex escapes and the replay either raises (bad escape
    \s) or silently rewrites the path (\U).  Caught by this suite before any
    replay was possible; the replacement is now a function."""
    src = A.git_show(REPO, A.HISTORICAL_COMMIT,
                     A.ANALYSIS_DIR + "/scripts/z5_lodo.py").decode()
    target = Path(r"C:\Users\dushy\AppData\Local\Temp\scratchpad")
    out = A.repoint(src, target)
    line = [ln for ln in out.splitlines() if ln.startswith("S = pathlib.Path(")]
    assert len(line) == 1, line
    assert str(target) in line[0], line[0]


def test_repoint_refuses_when_anchor_absent():
    """If the S-line is not exactly where expected, the replay must abort rather
    than silently run against whatever path happens to be baked in."""
    try:
        A.repoint("import numpy as np\nprint(1)\n", Path("X:/somewhere"))
    except RuntimeError as exc:
        assert "repoint S" in str(exc)
    else:
        raise AssertionError("repoint() accepted a source with no S anchor")


# --------------------------------------------------------------------------
# 4. Pathology-blindness scanner is live.
# --------------------------------------------------------------------------

def test_protected_scanner_fires_on_a_planted_token():
    hits = A.scan_protected("x = load('reader_oracle.npz')  # AT8 braak")
    assert "reader_oracle" in hits and "at8" in hits and "braak" in hits


def test_protected_scanner_is_clean_on_the_real_script():
    src = A.git_show(REPO, A.HISTORICAL_COMMIT,
                     A.ANALYSIS_DIR + "/scripts/z5_lodo.py").decode()
    assert A.scan_protected(src) == []


# --------------------------------------------------------------------------
# 5. The frozen comparison constants are the committed ones, not retyped ones.
# --------------------------------------------------------------------------

def test_frozen_historical_values_equal_the_committed_result():
    committed = json.loads(A.git_show(
        REPO, A.HISTORICAL_COMMIT, A.ANALYSIS_DIR + "/results/z_lodo.json").decode())
    for s, hist in A.HISTORICAL_R2.items():
        assert committed[s]["pooled_lodo_r2"] == hist["pooled_lodo_r2"], s
        assert committed[s]["n_donors"] == hist["n_donors"], s
    # the donor counts sum to 94, NOT 104 -- this is the population caveat
    assert (A.HISTORICAL_R2["SEA_AD"]["n_donors"]
            + A.HISTORICAL_R2["HVS"]["n_donors"]
            + A.HISTORICAL_R2["NPH52"]["n_donors"]) == 94
    assert A.HISTORICAL_R2["ALL"]["n_donors"] == 94


def test_reproduction_tolerance_is_not_vacuous():
    """A tolerance so loose that a materially different number passes would make
    a later 'reproduced' verdict meaningless."""
    assert A.REPLAY_ABS_TOLERANCE < 1e-9
    seaad = A.HISTORICAL_R2["SEA_AD"]["pooled_lodo_r2"]
    assert abs((seaad + 1e-9) - seaad) > A.REPLAY_ABS_TOLERANCE


def test_committed_code_digests_authenticate():
    """The positive control: the code/result side really does verify, which shows
    the digest machinery reports MATCH when the bytes are right."""
    out = A.authenticate_code(REPO)
    for rel, e in out.items():
        assert e["status"] == "MATCH", (rel, e)


def test_code_digest_check_can_fail():
    saved = A.EXPECTED_CODE_AND_RESULT_DIGESTS["scripts/z5_lodo.py"]
    try:
        A.EXPECTED_CODE_AND_RESULT_DIGESTS["scripts/z5_lodo.py"] = "00" * 32
        out = A.authenticate_code(REPO)
    finally:
        A.EXPECTED_CODE_AND_RESULT_DIGESTS["scripts/z5_lodo.py"] = saved
    assert out["scripts/z5_lodo.py"]["status"] == "DIGEST_MISMATCH"


# --------------------------------------------------------------------------
# 6. The recorded historical head is the live head.
# --------------------------------------------------------------------------

def test_live_head_equals_recorded_head():
    live = A.git_out(REPO, "ls-remote", "origin",
                     "refs/heads/" + A.HISTORICAL_BRANCH).split()[0]
    assert live == A.HISTORICAL_COMMIT, (live, A.HISTORICAL_COMMIT)


def _main():
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    bad = 0
    for n, f in fns:
        try:
            f()
            print("PASS  " + n)
        except Exception as exc:
            bad += 1
            print("FAIL  %s: %r" % (n, exc))
    print("\n%d/%d passed" % (len(fns) - bad, len(fns)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_main())
