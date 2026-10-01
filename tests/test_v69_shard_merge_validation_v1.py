"""Tests for the motif-shard merge validator.

The invariant under test has never been enforced in this repository before: the
concatenated shard motif axes must equal the frozen ordered motif universe exactly.
A merge that silently drops, duplicates or reorders motifs would remap every
downstream score without crashing.

Every failure mode is driven to its failure, and the PASS path is tested, so no
assertion here is a check that cannot fail.

ENVIRONMENT: this file needs pyarrow for feather I/O and therefore runs INSIDE the
SCENIC+ container, not under the Windows interpreter that runs the rest of the suite:

    docker run --rm -v "D:/jepa_wt_v69_scenicplus_20261001":/workspace -w /workspace       scenicplus:1.0a2 bash -c "micromamba run -n base python -m pip install -q pytest       && micromamba run -n base python -m pytest tests/test_v69_shard_merge_validation_v1.py -q"
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_MOD = Path(__file__).resolve().parents[1] / "scripts" / "v69" / \
    "merge_cistarget_motif_shards_v1.py"
_spec = importlib.util.spec_from_file_location("v69_merge", _MOD)
mg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mg)

REGIONS = [f"chr1:{i*1000}-{i*1000+500}" for i in range(20)]
FROZEN = [f"motif_{i:03d}" for i in range(12)]


def _write_shard(tmp_path, prefix, motifs, regions=REGIONS, kind="scores"):
    rng = np.random.default_rng(abs(hash(prefix)) % 2**32)
    df = pd.DataFrame(rng.random((len(regions), len(motifs))),
                      index=regions, columns=motifs)
    df.index.name = mg.REGION_INDEX_COLUMN
    p = tmp_path / f"{prefix}.motifs_vs_regions.{kind}.feather"
    df.reset_index().to_feather(p)
    return p


def _frozen_file(tmp_path, motifs=FROZEN):
    p = tmp_path / "motifs.all.lst"
    p.write_text("\n".join(motifs) + "\n")
    return p


def test_pass_is_reachable_and_axis_is_validated(tmp_path):
    _write_shard(tmp_path, "s0", FROZEN[:4])
    _write_shard(tmp_path, "s1", FROZEN[4:8])
    _write_shard(tmp_path, "s2", FROZEN[8:])
    r = mg.merge([tmp_path] * 3, ["s0", "s1", "s2"], _frozen_file(tmp_path),
                 tmp_path / "MERGED")
    assert r["status"] == "PASS__SHARDS_MERGED_AND_AXIS_VALIDATED"
    a = r["motif_axis_validation"]
    assert a["n_motifs"] == 12 and a["n_shards"] == 3
    assert a["digests_equal"] is True
    assert r["output_shape_regions_by_motifs"] == [20, 12]
    assert r["reread_from_disk_before_recording"] is True


def test_merged_values_match_the_source_shards(tmp_path):
    """Proves the merge moves the right numbers, not merely the right shape."""
    p0 = _write_shard(tmp_path, "s0", FROZEN[:6])
    p1 = _write_shard(tmp_path, "s1", FROZEN[6:])
    mg.merge([tmp_path] * 2, ["s0", "s1"], _frozen_file(tmp_path), tmp_path / "M")
    merged = mg.read_axis_frame(
        tmp_path / "M.motifs_vs_regions.scores.feather", mg.REGION_INDEX_COLUMN)
    for p in (p0, p1):
        src = mg.read_axis_frame(p, mg.REGION_INDEX_COLUMN)
        assert np.array_equal(merged[src.columns].to_numpy(), src.to_numpy())


def test_omitted_motif_fails_closed(tmp_path):
    _write_shard(tmp_path, "s0", FROZEN[:4])
    _write_shard(tmp_path, "s1", FROZEN[4:8])   # FROZEN[8:] never produced
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path] * 2, ["s0", "s1"], _frozen_file(tmp_path), tmp_path / "M")
    assert e.value.status == "FAIL__MERGED_MOTIF_AXIS_MISSING_MOTIFS"
    assert e.value.detail["n_missing"] == 4


def test_duplicated_motif_fails_closed(tmp_path):
    _write_shard(tmp_path, "s0", FROZEN[:6])
    _write_shard(tmp_path, "s1", FROZEN[4:])    # overlaps s0 by two motifs
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path] * 2, ["s0", "s1"], _frozen_file(tmp_path), tmp_path / "M")
    assert e.value.status == "FAIL__MERGED_MOTIF_AXIS_HAS_DUPLICATES"
    assert e.value.detail["n_duplicates"] == 2


def test_reordered_shards_fail_closed(tmp_path):
    """Right members, wrong order: membership-only checking would accept this."""
    _write_shard(tmp_path, "s0", FROZEN[:6])
    _write_shard(tmp_path, "s1", FROZEN[6:])
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path] * 2, ["s1", "s0"], _frozen_file(tmp_path), tmp_path / "M")
    assert e.value.status == "FAIL__MERGED_MOTIF_AXIS_ORDER_DIFFERS"
    assert e.value.detail["first_differing_index"] == 0


def test_unexpected_motif_fails_closed(tmp_path):
    _write_shard(tmp_path, "s0", FROZEN[:6])
    _write_shard(tmp_path, "s1", FROZEN[6:] + ["motif_999_NOT_IN_UNIVERSE"])
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path] * 2, ["s0", "s1"], _frozen_file(tmp_path), tmp_path / "M")
    assert e.value.status == "FAIL__MERGED_MOTIF_AXIS_HAS_UNEXPECTED_MOTIFS"


def test_divergent_region_axis_fails_closed(tmp_path):
    _write_shard(tmp_path, "s0", FROZEN[:6])
    _write_shard(tmp_path, "s1", FROZEN[6:], regions=REGIONS[:-1])
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path] * 2, ["s0", "s1"], _frozen_file(tmp_path), tmp_path / "M")
    assert e.value.status == "FAIL__SHARD_REGION_AXIS_DIFFERS"


def test_permuted_region_axis_fails_closed(tmp_path):
    """Same regions, different order -- must not be silently absorbed."""
    _write_shard(tmp_path, "s0", FROZEN[:6])
    _write_shard(tmp_path, "s1", FROZEN[6:], regions=list(reversed(REGIONS)))
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path] * 2, ["s0", "s1"], _frozen_file(tmp_path), tmp_path / "M")
    assert e.value.status == "FAIL__SHARD_REGION_AXIS_DIFFERS"


def test_absent_shard_output_fails_closed(tmp_path):
    _write_shard(tmp_path, "s0", FROZEN[:6])
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path] * 2, ["s0", "s_missing"], _frozen_file(tmp_path),
                 tmp_path / "M")
    assert e.value.status == "FAIL__SHARD_OUTPUT_ABSENT"


def test_empty_frozen_list_fails_closed(tmp_path):
    _write_shard(tmp_path, "s0", FROZEN[:6])
    p = tmp_path / "empty.lst"
    p.write_text("")
    with pytest.raises(mg.FailClosed) as e:
        mg.merge([tmp_path], ["s0"], p, tmp_path / "M")
    assert e.value.status == "FAIL__FROZEN_MOTIF_LIST_EMPTY"


def test_ordered_digest_detects_permutation():
    a = mg.ordered_digest(FROZEN)
    b = mg.ordered_digest(list(reversed(FROZEN)))
    assert a != b, "an order-sensitive digest must change under permutation"
    assert a == mg.ordered_digest(list(FROZEN))
