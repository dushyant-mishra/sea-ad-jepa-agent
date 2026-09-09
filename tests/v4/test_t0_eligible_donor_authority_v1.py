"""Adversarial tests for the T0 eligible-donor authority.

The module under test decides which donors enter the statistical population and
which of them are CONFIRMATION. Two failure modes matter more than the rest, and
most of what follows aims at them:

  * a coverage gap in a parent authority presenting itself as ineligibility,
    which would let an authority failure quietly shrink the population;
  * a role assignment that does not follow the frozen rule, which would refit a
    pre-registered design.

Scope: these tests read and write only this repository's own artifacts. No
pathology value, donor covariate value, or sealed input is touched.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "v4"))

import t0_eligible_donor_authority_v1 as eld  # noqa: E402

PARENTS = {
    "at8_availability_root_sha256": "a" * 64,
    "technical_completeness_root_sha256": "b" * 64,
    "age_sex_authority_root_sha256": "c" * 64,
    "immune_support_count_root_sha256": "d" * 64,
}
CODE_DIGEST = "e" * 64


def _universe(n: int = 46) -> list[str]:
    return ["H%02d.%03d" % (i // 10, i) for i in range(n)]


def _all_true(donors, value=True):
    return {d: value for d in donors}


def _lawful(n: int = 46):
    donors = _universe(n)
    return dict(candidate_donors=donors,
                at8_available=_all_true(donors),
                technical_complete=_all_true(donors),
                age_present=_all_true(donors),
                sex_present=_all_true(donors))


# ---------------------------------------------------------------------------
# The frozen split rule.
# ---------------------------------------------------------------------------

def test_split_hash_is_the_frozen_digest() -> None:
    for donor in ("H20.33.001", "D1", "x"):
        expected = hashlib.sha256(
            ("T0-DISCOVERY-CONFIRM-V2|%s" % donor).encode("utf-8")).hexdigest()
        assert eld.split_hash(donor) == expected


def test_the_frozen_floors_are_eighteen_and_eighteen() -> None:
    assert eld.CONFIRMATION_DONORS == 18
    assert eld.MINIMUM_DISCOVERY_DONORS == 18
    assert eld.ROLE_NAMESPACE == "T0-DISCOVERY-CONFIRM-V2"
    assert eld.assert_role_rule_unaltered() is True


def test_an_empty_or_non_string_donor_id_is_refused() -> None:
    for bad in ("", None, 7, b"D1"):
        with pytest.raises(AssertionError):
            eld.split_hash(bad)


# ---------------------------------------------------------------------------
# The predicate is a conjunction, and nothing else.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("flag", ["at8_available", "technical_complete",
                                  "age_present", "sex_present"])
def test_each_conjunct_alone_makes_a_donor_ineligible(flag) -> None:
    inputs = _lawful()
    target = inputs["candidate_donors"][0]
    inputs[flag] = dict(inputs[flag])
    inputs[flag][target] = False
    rows = eld.derive_eligible_donors(**inputs)
    row = next(r for r in rows if r["donor_id"] == target)
    assert row["eligible"] is False
    assert row["donor_role"] == "INELIGIBLE"
    assert sum(1 for r in rows if r["eligible"]) == 45


def test_all_conjuncts_true_is_eligible_and_the_universe_is_intact() -> None:
    rows = eld.derive_eligible_donors(**_lawful())
    assert len(rows) == 46
    assert all(r["eligible"] for r in rows)
    assert sum(1 for r in rows if r["donor_role"] == "CONFIRMATION") == 18
    assert sum(1 for r in rows if r["donor_role"] == "DISCOVERY") == 28


# ---------------------------------------------------------------------------
# A coverage gap is a STOP, never ineligibility.
#
# This is the finding the owner named directly: technical_complete=False must not
# become a way to absorb authority failures. A donor a parent does not mention is
# a broken parent, not an ineligible donor.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("parent", ["at8_available", "technical_complete",
                                    "age_present", "sex_present"])
def test_a_parent_that_does_not_cover_the_universe_stops(parent) -> None:
    inputs = _lawful()
    dropped = inputs["candidate_donors"][5]
    inputs[parent] = {d: v for d, v in inputs[parent].items() if d != dropped}
    with pytest.raises(AssertionError) as excinfo:
        eld.derive_eligible_donors(**inputs)
    assert eld.STOP_PARENT_COVERAGE in str(excinfo.value)
    assert parent in str(excinfo.value)


@pytest.mark.parametrize("parent", ["at8_available", "technical_complete",
                                    "age_present", "sex_present"])
def test_a_parent_covering_donors_outside_the_universe_stops(parent) -> None:
    inputs = _lawful()
    inputs[parent] = dict(inputs[parent])
    inputs[parent]["NOT_A_CANDIDATE"] = True
    with pytest.raises(AssertionError) as excinfo:
        eld.derive_eligible_donors(**inputs)
    assert eld.STOP_PARENT_COVERAGE in str(excinfo.value)


def test_a_missing_donor_does_not_silently_shrink_the_population() -> None:
    """The negative form of the same claim, stated as an outcome."""
    inputs = _lawful()
    dropped = inputs["candidate_donors"][5]
    del inputs["technical_complete"][dropped]
    with pytest.raises(AssertionError):
        eld.derive_eligible_donors(**inputs)
    # And with the donor restored as explicitly False, it is ineligible rather
    # than absent, so the distinction is observable.
    inputs["technical_complete"][dropped] = False
    rows = eld.derive_eligible_donors(**inputs)
    assert len(rows) == 46
    assert next(r for r in rows
                if r["donor_id"] == dropped)["eligible"] is False


def test_a_duplicate_candidate_donor_stops() -> None:
    inputs = _lawful()
    inputs["candidate_donors"] = list(inputs["candidate_donors"]) + [
        inputs["candidate_donors"][0]]
    with pytest.raises(AssertionError) as excinfo:
        eld.derive_eligible_donors(**inputs)
    assert eld.STOP_DUPLICATE_DONOR in str(excinfo.value)


# ---------------------------------------------------------------------------
# Only real booleans.
#
# Truthy stand-ins are refused because a parent that emitted 1, "yes" or 0.0 has
# not answered a boolean question, and coercing it here would invent an answer.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [1, 0, "yes", "true", "TRUE", "", None, 1.0,
                                 0.0, [], "1", "True", "False"])
def test_a_non_boolean_flag_stops(bad) -> None:
    """The strings True and False are refused here, though the loader parses them.

    CSV has no booleans, so the loader has to parse the textual form back. A
    derivation gets no such latitude: a parent handing over the string "True"
    has not been validated as boolean by anything, and accepting it would let an
    unparsed CSV column decide eligibility.
    """
    inputs = _lawful()
    target = inputs["candidate_donors"][3]
    inputs["at8_available"] = dict(inputs["at8_available"])
    inputs["at8_available"][target] = bad
    with pytest.raises(AssertionError) as excinfo:
        eld.derive_eligible_donors(**inputs)
    assert eld.STOP_NOT_BOOLEAN in str(excinfo.value)


# ---------------------------------------------------------------------------
# The design floor is a STOP, not a smaller study.
# ---------------------------------------------------------------------------

def test_too_few_eligible_donors_stops_rather_than_shrinking() -> None:
    inputs = _lawful()
    for donor in inputs["candidate_donors"][:12]:
        inputs["technical_complete"][donor] = False
    # 34 eligible, and the frozen design needs 36.
    with pytest.raises(AssertionError) as excinfo:
        eld.derive_eligible_donors(**inputs)
    assert eld.STOP_DESIGN_NOT_EXECUTABLE in str(excinfo.value)
    assert "34 eligible" in str(excinfo.value)


def test_exactly_thirty_six_eligible_donors_is_the_boundary() -> None:
    inputs = _lawful()
    for donor in inputs["candidate_donors"][:10]:
        inputs["technical_complete"][donor] = False
    rows = eld.derive_eligible_donors(**inputs)
    assert sum(1 for r in rows if r["eligible"]) == 36
    assert sum(1 for r in rows if r["donor_role"] == "CONFIRMATION") == 18
    assert sum(1 for r in rows if r["donor_role"] == "DISCOVERY") == 18

    inputs["technical_complete"][inputs["candidate_donors"][10]] = False
    with pytest.raises(AssertionError):
        eld.derive_eligible_donors(**inputs)


# ---------------------------------------------------------------------------
# Roles follow the frozen rule, computed over eligible donors only.
# ---------------------------------------------------------------------------

def test_roles_are_the_first_eighteen_eligible_donors_by_split_hash() -> None:
    inputs = _lawful()
    for donor in inputs["candidate_donors"][:4]:
        inputs["age_present"][donor] = False
    rows = eld.derive_eligible_donors(**inputs)
    eligible = [r for r in rows if r["eligible"]]
    ordered = sorted(eligible, key=lambda r: (r["split_hash"], r["donor_id"]))
    assert {r["donor_id"] for r in ordered[:18]} == {
        r["donor_id"] for r in rows if r["donor_role"] == "CONFIRMATION"}
    assert eld.assert_roles_agree_with_frozen_rule(rows) is True


def test_ineligible_donors_do_not_occupy_confirmation_slots() -> None:
    """Eligibility is applied before ranking, as the role authority does."""
    inputs = _lawful()
    all_donors = list(inputs["candidate_donors"])
    ranked = sorted(all_donors, key=lambda d: (eld.split_hash(d), d))
    victim = ranked[0]  # would be CONFIRMATION if ranked over everyone
    inputs["at8_available"][victim] = False
    rows = eld.derive_eligible_donors(**inputs)
    row = next(r for r in rows if r["donor_id"] == victim)
    assert row["donor_role"] == "INELIGIBLE"
    assert sum(1 for r in rows if r["donor_role"] == "CONFIRMATION") == 18


def test_the_two_frozen_role_paths_are_reported_when_they_diverge() -> None:
    """The divergence is measured, not argued about."""
    donors = _universe()
    ranked = sorted(donors, key=lambda d: (eld.split_hash(d), d))
    eligible = [d for d in donors if d != ranked[0]]
    report = eld.split_rule_divergence(donors, eligible)
    assert report["paths_agree"] is False
    assert report["ineligible_donors_inside_support_top_18"] == [ranked[0]]
    assert report["binding_rule"] == eld.ROLE_AUTHORITY_RULE

    agree = eld.split_rule_divergence(donors, donors)
    assert agree["paths_agree"] is True
    assert agree["ineligible_donors"] == []


def test_roles_are_stable_under_the_order_donors_are_supplied_in() -> None:
    inputs = _lawful()
    first = eld.derive_eligible_donors(**inputs)
    inputs["candidate_donors"] = list(reversed(inputs["candidate_donors"]))
    second = eld.derive_eligible_donors(**inputs)
    assert eld.eligible_donor_root(first) == eld.eligible_donor_root(second)
    assert eld.donor_role_root(first) == eld.donor_role_root(second)


# ---------------------------------------------------------------------------
# Roots discriminate.
# ---------------------------------------------------------------------------

def test_flipping_any_eligibility_bit_moves_the_root() -> None:
    base = eld.derive_eligible_donors(**_lawful())
    base_root = eld.eligible_donor_root(base)
    seen = {base_root}
    for flag in ("at8_available", "technical_complete", "age_present",
                 "sex_present"):
        inputs = _lawful()
        inputs[flag][inputs["candidate_donors"][7]] = False
        root = eld.eligible_donor_root(
            eld.derive_eligible_donors(**inputs))
        assert root not in seen
        seen.add(root)


def test_the_role_root_covers_eligible_donors_only() -> None:
    """So it is directly comparable to the frozen role authority's assignment."""
    inputs = _lawful()
    inputs["sex_present"][inputs["candidate_donors"][2]] = False
    rows = eld.derive_eligible_donors(**inputs)
    eligible_rows = [dict(r) for r in rows if r["eligible"]]
    assert eld.donor_role_root(rows) == eld.donor_role_root(eligible_rows)


def test_donor_ids_cannot_be_confused_across_the_field_boundary() -> None:
    """Length-prefixed framing: concatenation must not collide."""
    a = eld.derive_eligible_donors(
        candidate_donors=_universe(36),
        **{k: _all_true(_universe(36))
           for k in ("at8_available", "technical_complete", "age_present",
                     "sex_present")})
    shifted = ["%sX" % d for d in _universe(36)]
    b = eld.derive_eligible_donors(
        candidate_donors=shifted,
        **{k: _all_true(shifted)
           for k in ("at8_available", "technical_complete", "age_present",
                     "sex_present")})
    assert eld.eligible_donor_root(a) != eld.eligible_donor_root(b)


def test_the_parent_contract_root_requires_named_hex_digests() -> None:
    assert eld.parent_contract_root(PARENTS)
    for bad in ({"x": "not-hex"}, {"x": "A" * 64}, {"x": "a" * 63},
                {"x": None}, {"x": 7}):
        with pytest.raises(AssertionError) as excinfo:
            eld.parent_contract_root(bad)
        assert eld.STOP_PARENT_IDENTITY in str(excinfo.value)


def test_the_parent_contract_root_is_order_independent_but_name_sensitive(
) -> None:
    reordered = {k: PARENTS[k] for k in reversed(list(PARENTS))}
    assert eld.parent_contract_root(PARENTS) == eld.parent_contract_root(
        reordered)
    renamed = dict(PARENTS)
    renamed["at8_availability_root_sha256_"] = renamed.pop(
        "at8_availability_root_sha256")
    assert eld.parent_contract_root(PARENTS) != eld.parent_contract_root(
        renamed)


# ---------------------------------------------------------------------------
# Nothing about pathology, and no covariate value, may leave this authority.
# ---------------------------------------------------------------------------

def test_no_pathology_field_may_be_emitted() -> None:
    assert eld.assert_no_pathology_in_artifact() is True
    for bad in ("at8_value", "AT8_percent", "braak_stage", "percent AT8 area",
                "cerad", "thal_phase", "ptau_density"):
        with pytest.raises(AssertionError) as excinfo:
            eld.assert_no_pathology_in_artifact(["donor_id", bad])
        assert eld.STOP_PATHOLOGY_IN_ARTIFACT in str(excinfo.value)


def test_the_registry_carries_no_age_or_sex_value(tmp_path) -> None:
    rows = eld.derive_eligible_donors(**_lawful())
    eld.build_authority(tmp_path / "pkg", rows=rows, parents=PARENTS,
                        derivation_code_sha256=CODE_DIGEST,
                        at8_availability_independently_verified=True)
    text = (tmp_path / "pkg" / eld.REGISTRY).read_text(encoding="utf-8")
    header = text.splitlines()[0].split(",")
    assert header == list(eld.REGISTRY_FIELDS)
    assert "age" not in header and "sex" not in header
    assert "age_present" in header and "sex_present" in header
    # Every non-identifier cell is one of exactly two boolean spellings.
    for line in text.splitlines()[1:]:
        cells = line.split(",")
        assert cells[1:6] == ["True"] * 5
        assert cells[7] in ("CONFIRMATION", "DISCOVERY", "INELIGIBLE")


# ---------------------------------------------------------------------------
# The package, and its replay.
# ---------------------------------------------------------------------------

def _restamp(pkgdir):
    """Rewrite the manifest and return the package root for the bytes on disk.

    Mutating a member breaks three things at once: the manifest, the package
    root and whatever the member itself asserts. A test that only wants to
    exercise the third has to repair the first two, or the earlier check fires
    and the test silently stops testing what its name says.
    """
    import csv as _csv
    import hashlib as _hashlib

    rows = [["filename", "bytes", "sha256"]]
    for name in (eld.REGISTRY, eld.METADATA):
        blob = (pkgdir / name).read_bytes()
        rows.append([name, len(blob), _hashlib.sha256(blob).hexdigest()])
    buf = io.StringIO()
    writer = _csv.writer(buf, lineterminator="\n")
    for row in rows:
        writer.writerow(row)
    (pkgdir / eld.MANIFEST).write_bytes(buf.getvalue().encode("utf-8"))
    members = {name: (pkgdir / name).read_bytes() for name in eld.MEMBERS}
    return eld.package_root(members)


def _build(tmp_path, inputs=None):
    rows = eld.derive_eligible_donors(**(inputs or _lawful()))
    summary = eld.build_authority(
        tmp_path / "pkg", rows=rows, parents=PARENTS,
        derivation_code_sha256=CODE_DIGEST,
        at8_availability_independently_verified=True)
    return rows, summary


def test_a_built_package_replays_and_reproduces_every_root(tmp_path) -> None:
    rows, summary = _build(tmp_path)
    replayed = eld.load_authority(
        tmp_path / "pkg",
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_eligible_donor_root_sha256=summary[
            "eligible_donor_root_sha256"],
        expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
        expected_parent_contract_root_sha256=summary[
            "parent_contract_root_sha256"],
        expected_candidate_donors=[r["donor_id"] for r in rows])
    assert replayed["eligible_donor_root_sha256"] == summary[
        "eligible_donor_root_sha256"]
    assert replayed["donor_role_root_sha256"] == summary[
        "donor_role_root_sha256"]
    assert len(replayed["rows"]) == 46
    assert replayed["metadata"]["real_execution_ready"] is False


def test_the_output_directory_must_be_absent_or_empty(tmp_path) -> None:
    _build(tmp_path)
    rows = eld.derive_eligible_donors(**_lawful())
    with pytest.raises(AssertionError) as excinfo:
        eld.build_authority(tmp_path / "pkg", rows=rows, parents=PARENTS,
                            derivation_code_sha256=CODE_DIGEST,
                            at8_availability_independently_verified=True)
    assert eld.STOP_PACKAGE_MEMBER in str(excinfo.value)


def test_a_missing_package_member_is_refused(tmp_path) -> None:
    rows, summary = _build(tmp_path)
    (tmp_path / "pkg" / eld.MANIFEST).unlink()
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_PACKAGE_MEMBER in str(excinfo.value)


def test_a_substituted_registry_row_is_refused(tmp_path) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.REGISTRY
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("True,True,True,True,True",
                                 "True,False,True,True,False", 1),
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_MANIFEST_MISMATCH in str(excinfo.value)


def test_a_role_swapped_registry_is_refused_even_when_digests_agree(
        tmp_path) -> None:
    """The role is re-derived on load, so a self-consistent package still fails.

    Recomputing every digest after the swap is what makes this test meaningful:
    without it the package root would fire first and the frozen-rule check would
    never be reached.
    """
    rows, _summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.REGISTRY
    lines = path.read_text(encoding="utf-8").splitlines()
    swapped = []
    for line in lines:
        if line.endswith(",CONFIRMATION"):
            swapped.append(line[: -len("CONFIRMATION")] + "DISCOVERY")
        elif line.endswith(",DISCOVERY"):
            swapped.append(line[: -len("DISCOVERY")] + "CONFIRMATION")
        else:
            swapped.append(line)
    path.write_text("\n".join(swapped) + "\n", encoding="utf-8")

    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256="0" * 64,
            expected_donor_role_root_sha256="0" * 64,
            expected_parent_contract_root_sha256="0" * 64)
    assert eld.STOP_ROLE_RULE in str(excinfo.value)
    # Specifically the role check, not the split-hash check that shares the
    # terminal.
    assert "the frozen rule says" in str(excinfo.value)


def test_a_substituted_split_hash_is_refused(tmp_path) -> None:
    rows, _summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.REGISTRY
    lines = path.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[6] = "f" * 64
    lines[1] = ",".join(cells)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256="0" * 64,
            expected_donor_role_root_sha256="0" * 64,
            expected_parent_contract_root_sha256="0" * 64)
    assert eld.STOP_ROLE_RULE in str(excinfo.value)
    # Specifically the split-hash check, not the role check.
    assert "the frozen rule yields" in str(excinfo.value)


def test_a_metadata_parent_root_that_does_not_match_its_parents_is_refused(
        tmp_path) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["parents"]["at8_availability_root_sha256"] = "9" * 64
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_PARENT_IDENTITY in str(excinfo.value)


@pytest.mark.parametrize("flag", ["numeric_at8_value_read",
                                  "numeric_at8_value_emitted",
                                  "numeric_covariate_values_emitted",
                                  "pathology_fields_in_artifact",
                                  "real_execution_ready"])
def test_a_package_claiming_any_of_the_closed_flags_is_refused(
        tmp_path, flag) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta[flag] = True
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_FIELD_SCHEMA in str(excinfo.value)


def test_a_replay_against_a_different_candidate_universe_is_refused(
        tmp_path) -> None:
    rows, summary = _build(tmp_path)
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=summary["package_root_sha256"],
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"],
            expected_candidate_donors=_universe(45))
    assert eld.STOP_PARENT_COVERAGE in str(excinfo.value)


def test_a_package_over_the_wrong_number_of_candidate_donors_is_refused(
        tmp_path) -> None:
    """The 46-donor universe is the production geometry, and it is checked."""
    rows = eld.derive_eligible_donors(**_lawful(40))
    with pytest.raises(AssertionError) as excinfo:
        eld.build_authority(tmp_path / "pkg", rows=rows, parents=PARENTS,
                            derivation_code_sha256=CODE_DIGEST,
                            at8_availability_independently_verified=True)
    assert eld.STOP_PARENT_COVERAGE in str(excinfo.value)
    # It is a declared expectation, not a hidden constant, so a smaller cohort
    # can be built deliberately.
    summary = eld.build_authority(
        tmp_path / "pkg2", rows=rows, parents=PARENTS,
        derivation_code_sha256=CODE_DIGEST,
        at8_availability_independently_verified=True,
        expected_candidate_donors=40)
    assert summary["candidate_donors"] == 40


def test_the_metadata_records_the_binding_role_rule(tmp_path) -> None:
    _rows, _summary = _build(tmp_path)
    meta = json.loads((tmp_path / "pkg" / eld.METADATA).read_text(
        encoding="utf-8"))
    assert meta["binding_role_rule"] == eld.ROLE_AUTHORITY_RULE
    assert meta["confirmation_donors"] == 18
    assert meta["minimum_discovery_donors"] == 18
    assert meta["real_execution_ready"] is False
    assert meta["eligibility_predicate"] == (
        "AT8_available & technical_complete & age_present & sex_present")


# ---------------------------------------------------------------------------
# The three checks added after attacking this suite.
#
# Each of these describes a package that is internally consistent under every
# digest it publishes and still wrong. Digest agreement is not correctness: it
# certifies that the bytes are the bytes someone intended, not that the claim
# they encode follows from the rule it cites.
# ---------------------------------------------------------------------------

def test_eligible_true_beside_a_false_conjunct_is_refused(tmp_path) -> None:
    """A self-consistent package that contradicts its own predicate."""
    rows, _summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.REGISTRY
    lines = path.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[2] = "False"          # technical_complete
    lines[1] = ",".join(cells)  # eligible stays True
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256="0" * 64,
            expected_donor_role_root_sha256="0" * 64,
            expected_parent_contract_root_sha256="0" * 64)
    assert eld.STOP_PREDICATE_CONTRADICTED in str(excinfo.value)


def test_an_ineligible_donor_carrying_a_study_role_is_refused(
        tmp_path) -> None:
    inputs = _lawful()
    inputs["age_present"][inputs["candidate_donors"][0]] = False
    rows, _summary = _build(tmp_path, inputs)
    path = tmp_path / "pkg" / eld.REGISTRY
    text = path.read_text(encoding="utf-8").replace(",INELIGIBLE",
                                                    ",DISCOVERY", 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256="0" * 64,
            expected_donor_role_root_sha256="0" * 64,
            expected_parent_contract_root_sha256="0" * 64)
    assert eld.STOP_PREDICATE_CONTRADICTED in str(excinfo.value)


def test_the_writer_refuses_to_emit_a_contradicted_predicate(
        tmp_path) -> None:
    """The check runs on the way out too, not only on the way back in."""
    rows = [dict(r) for r in eld.derive_eligible_donors(**_lawful())]
    rows[0]["technical_complete"] = False   # eligible left True
    with pytest.raises(AssertionError) as excinfo:
        eld.build_authority(tmp_path / "pkg", rows=rows, parents=PARENTS,
                            derivation_code_sha256=CODE_DIGEST,
                            at8_availability_independently_verified=True)
    assert eld.STOP_PREDICATE_CONTRADICTED in str(excinfo.value)


def test_a_manifest_that_does_not_describe_its_members_is_refused(
        tmp_path) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.MANIFEST
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    cells = lines[1].split(",")
    cells[1] = str(int(cells[1]) + 1)
    lines[1] = ",".join(cells)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    members = {name: (tmp_path / "pkg" / name).read_bytes()
               for name in eld.MEMBERS}
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=eld.package_root(members),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_MANIFEST_MISMATCH in str(excinfo.value)


def test_a_manifest_omitting_a_member_is_refused(tmp_path) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.MANIFEST
    lines = path.read_text(encoding="utf-8").splitlines()
    kept = [line for line in lines if not line.startswith(eld.METADATA)]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    members = {name: (tmp_path / "pkg" / name).read_bytes()
               for name in eld.MEMBERS}
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=eld.package_root(members),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_MANIFEST_MISMATCH in str(excinfo.value)


@pytest.mark.parametrize("field,value", [("candidate_donors", 40),
                                         ("eligible_donors", 40)])
def test_metadata_counts_that_disagree_with_the_registry_are_refused(
        tmp_path, field, value) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta[field] = value
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_COUNTS_MISMATCH in str(excinfo.value)


def test_metadata_role_counts_that_disagree_with_the_registry_are_refused(
        tmp_path) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["role_counts"] = {"CONFIRMATION": 18, "DISCOVERY": 27,
                           "INELIGIBLE": 1}
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_COUNTS_MISMATCH in str(excinfo.value)


def test_a_metadata_confirmation_floor_other_than_eighteen_is_refused(
        tmp_path) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["confirmation_donors"] = 17
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_ROLE_RULE in str(excinfo.value)


def test_a_metadata_binding_rule_naming_the_wrong_path_is_refused(
        tmp_path) -> None:
    """A package may not claim it ranked all support donors."""
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["binding_role_rule"] = "RANK_ALL_SUPPORT_DONORS"
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_ROLE_RULE in str(excinfo.value)


def test_the_textual_boolean_is_accepted_on_reload_but_not_on_derivation(
        tmp_path) -> None:
    """The two directions differ deliberately, so both are pinned."""
    donors = _universe(40)
    text_flags = {d: "True" for d in donors}
    with pytest.raises(AssertionError) as excinfo:
        eld.derive_eligible_donors(
            candidate_donors=donors, at8_available=text_flags,
            technical_complete=text_flags, age_present=text_flags,
            sex_present=text_flags)
    assert eld.STOP_NOT_BOOLEAN in str(excinfo.value)

    # The same spelling round-trips through a written package, because that is
    # how a boolean survives a CSV.
    rows, summary = _build(tmp_path)
    assert "True" in (tmp_path / "pkg" / eld.REGISTRY).read_text(
        encoding="utf-8")
    replayed = eld.load_authority(
        tmp_path / "pkg",
        expected_package_root_sha256=summary["package_root_sha256"],
        expected_eligible_donor_root_sha256=summary[
            "eligible_donor_root_sha256"],
        expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
        expected_parent_contract_root_sha256=summary[
            "parent_contract_root_sha256"])
    assert all(r["at8_available"] is True for r in replayed["rows"])


def test_a_package_naming_no_parent_authorities_is_refused(tmp_path) -> None:
    rows, summary = _build(tmp_path)
    path = tmp_path / "pkg" / eld.METADATA
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["parents"] = {}
    path.write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        eld.load_authority(
            tmp_path / "pkg",
            expected_package_root_sha256=_restamp(tmp_path / "pkg"),
            expected_eligible_donor_root_sha256=summary[
                "eligible_donor_root_sha256"],
            expected_donor_role_root_sha256=summary["donor_role_root_sha256"],
            expected_parent_contract_root_sha256=summary[
                "parent_contract_root_sha256"])
    assert eld.STOP_PARENT_IDENTITY in str(excinfo.value)
