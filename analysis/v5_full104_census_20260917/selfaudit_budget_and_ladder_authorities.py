"""Self-audit of the two new authorities before building further on them.

Checks the claims I made when writing them, especially the load-bearing one:
that V2 is behaviour-identical to V1 for the same fraction, so the streaming
executor needs no change.
"""
import sys
from fractions import Fraction

sys.path.insert(0, r'D:/jepa_full104_mask_20260917/src')

from sea_ad_jepa.v5.target_evidence_budget_authority_v1 import TargetEvidenceBudgetAuthorityV1
from sea_ad_jepa.v5.target_evidence_budget_authority_v2 import (
    TargetEvidenceBudgetAuthorityV2, REQUIRED_EXCLUDED_OBSERVATION_STATE_IDS)
from sea_ad_jepa.v5.masking_burden_ladder_authority_v1 import (
    MaskingBurdenLadderAuthorityV1, FROZEN_BURDEN_LADDER)

H = 'a' * 64
CEN = 'b' * 64
MAN = '66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29'
OBS = '852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'
fails = []


def check(name, fn):
    try:
        fn()
        print('  PASS  %s' % name)
    except AssertionError as exc:
        fails.append((name, str(exc)))
        print('  FAIL  %s : %s' % (name, exc))
    except Exception as exc:
        fails.append((name, repr(exc)))
        print('  ERROR %s : %r' % (name, exc))


def mk_v2(num, den, minret=0):
    return TargetEvidenceBudgetAuthorityV2(
        authority_id='AUDIT',
        support_estimability_authority_sha256=H,
        support_semantics_id='STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1',
        census_authority_sha256=CEN,
        full104_block_manifest_sha256=MAN,
        observation_state_sha256=OBS,
        terminal_universe_id='FULL_COMMON_CORE_17186_V1',
        budget_semantics_id='MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1',
        eligibility_rule_id='VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1',
        rounding_policy_id='FLOOR_EXACT_RATIONAL_V1',
        mask_fraction_numerator=num,
        mask_fraction_denominator=den,
        min_retained_non_target_address_count=minret,
        infeasible_policy_id='FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1',
    )


def mk_v1(num, den, minret=0):
    return TargetEvidenceBudgetAuthorityV1(
        authority_id='AUDIT',
        support_estimability_authority_sha256=H,
        budget_semantics_id='MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1',
        rounding_policy_id='FLOOR_EXACT_RATIONAL_V1',
        mask_fraction_numerator=num,
        mask_fraction_denominator=den,
        min_retained_non_target_rna_count=minret,
        infeasible_policy_id='FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1',
    )


print('=== A. V1/V2 behavioural parity (load-bearing: executor needs no change) ===')


def parity():
    eligible = 17186 - 1
    for num, den in FROZEN_BURDEN_LADDER:
        a = mk_v1(num, den).mask_count(eligible)
        b = mk_v2(num, den).mask_count(eligible)
        assert a == b, '%d/%d: V1=%d V2=%d' % (num, den, a, b)
    # and across a sweep of eligible sizes and min-retained values
    for elig in (1, 2, 7, 100, 999, 17185, 41237):
        for num, den in FROZEN_BURDEN_LADDER:
            for mr in (0, 1, 10):
                try:
                    a = mk_v1(num, den, mr).mask_count(elig)
                    ea = None
                except Exception as exc:
                    a, ea = None, type(exc).__name__
                try:
                    b = mk_v2(num, den, mr).mask_count(elig)
                    eb = None
                except Exception as exc:
                    b, eb = None, type(exc).__name__
                assert (a, ea) == (b, eb), 'elig=%d %d/%d mr=%d : V1=%r/%s V2=%r/%s' % (
                    elig, num, den, mr, a, ea, b, eb)


check('V1 and V2 mask_count agree exactly on every rung and edge case', parity)

print()
print('=== B. value-independence is mechanically enforced ===')


def vi_ok():
    b = mk_v2(3, 20)
    assert b.verify_value_independence([17185] * 50) == 17185


def vi_reject():
    b = mk_v2(3, 20)
    try:
        b.verify_value_independence([2822, 1840, 3773])  # per-cell realized nonzero counts
    except ValueError as exc:
        assert 'value-dependent' in str(exc), str(exc)
        return
    raise AssertionError('per-cell varying counts were accepted')


def vi_empty():
    try:
        mk_v2(3, 20).verify_value_independence([])
    except ValueError:
        return
    raise AssertionError('empty accepted')


check('constant eligible count accepted', vi_ok)
check('per-cell varying (value-dependent) count REJECTED', vi_reject)
check('empty sequence rejected', vi_empty)

print()
print('=== C. V2 rejects semantics drift ===')


def reject_old_semantics():
    try:
        b = mk_v2(3, 20)
        object.__setattr__(b, 'budget_semantics_id', 'MASK_FRACTION_OF_ELIGIBLE_NON_TARGET_RNA_V1')
        b.validate()
    except ValueError:
        return
    raise AssertionError('V1 ambiguous semantics id accepted by V2')


def reject_loose_support():
    try:
        b = mk_v2(3, 20)
        object.__setattr__(b, 'support_semantics_id', 'MEASURED_ANY_INCLUDING_COLLISION_V1')
        b.validate()
    except ValueError:
        return
    raise AssertionError('loose support semantics accepted')


def reject_measured_zero_false():
    try:
        b = mk_v2(3, 20)
        object.__setattr__(b, 'measured_zero_is_measured_evidence', False)
        b.validate()
    except ValueError:
        return
    raise AssertionError('measured_zero_is_measured_evidence=False accepted')


def reject_training():
    try:
        b = mk_v2(3, 20)
        object.__setattr__(b, 'training_authorized', True)
        b.validate()
    except ValueError:
        return
    raise AssertionError('training_authorized=True accepted')


def reject_bad_excluded():
    try:
        b = mk_v2(3, 20)
        object.__setattr__(b, 'excluded_observation_state_ids', ('STRUCTURALLY_UNMEASURED',))
        b.validate()
    except ValueError:
        return
    raise AssertionError('incomplete exclusion set accepted')


check('V1 ambiguous semantics id rejected', reject_old_semantics)
check('loose support semantics rejected', reject_loose_support)
check('measured_zero_is_measured_evidence=False rejected', reject_measured_zero_false)
check('training_authorized=True rejected', reject_training)
check('incomplete excluded-state set rejected', reject_bad_excluded)

print()
print('=== D. burden ladder ===')


def mk_ladder():
    return MaskingBurdenLadderAuthorityV1(
        authority_id='AUDIT',
        ladder_id='FULL104_CENSUS_BURDEN_LADDER_20260917_V1',
        census_authority_sha256=CEN,
        selection_rule_id='LOWEST_QUALIFYING_BURDEN_V1',
        escalation_rule_id='ASCENDING_BURDEN_STAGED_ESCALATION_V1',
        no_qualifier_policy_id='FAIL_CLOSED_NO_MASKING_AUTHORITY_V1',
        terminal_universe_size=17186,
    )


CENSUS_STRESS_ROUND = [859, 1719, 2578, 3437, 5156, 8593]   # from the census artifact


def ladder_universe_burden():
    """Expectation recomputed independently as floor(f*17186), not read off the code."""
    L = mk_ladder()
    for r in L.ordered_rungs():
        exp = (17186 * r.numerator) // r.denominator
        got = L.universe_burden_for(r)
        assert got == exp, '%s: got %d expected %d' % (r, got, exp)


def ladder_co_mask_count():
    """Operative quantity is floor(f*17185) over eligible NON-TARGET addresses."""
    L = mk_ladder()
    for r in L.ordered_rungs():
        exp = (17185 * r.numerator) // r.denominator
        got = L.co_mask_count_for(r, 17185)
        assert got == exp, '%s: got %d expected %d' % (r, got, exp)


def ladder_three_quantities_distinct():
    """The defect this fix addresses: the three integers really do differ."""
    L = mk_ladder()
    disagreements = 0
    for r, census in zip(L.ordered_rungs(), CENSUS_STRESS_ROUND):
        u = L.universe_burden_for(r)
        c = L.co_mask_count_for(r, 17185)
        if not (census == u == c):
            disagreements += 1
    assert disagreements == 4, 'expected 4 disagreeing rungs, got %d' % disagreements


def ladder_provenance_matches_recomputation():
    """Provenance dict must agree with independent recomputation on all 3 columns."""
    from sea_ad_jepa.v5.masking_burden_ladder_authority_v1 import BURDEN_LADDER_PROVENANCE
    L = mk_ladder()
    for r, census in zip(L.ordered_rungs(), CENSUS_STRESS_ROUND):
        key = '%d/%d' % (r.numerator, r.denominator)
        rec = BURDEN_LADDER_PROVENANCE[key]
        assert rec['census_stress_burden_round'] == census, key
        assert rec['universe_burden_floor'] == (17186 * r.numerator) // r.denominator, key
        assert rec['co_mask_count_floor'] == (17185 * r.numerator) // r.denominator, key


def ladder_budget_agree():
    L = mk_ladder()
    for n, d in FROZEN_BURDEN_LADDER:
        got = L.assert_agrees_with_budget(mk_v2(n, d), 17185)
        exp = (17185 * n) // d
        assert got == exp, '%d/%d: %d != %d' % (n, d, got, exp)


def ladder_rejects_offladder_budget():
    L = mk_ladder()
    try:
        L.assert_agrees_with_budget(mk_v2(7, 100), 17185)   # 7% is not a rung
    except ValueError as exc:
        assert 'not a frozen ladder rung' in str(exc), str(exc)
        return
    raise AssertionError('off-ladder budget fraction accepted')


def ladder_lowest():
    L = mk_ladder()
    rungs = L.ordered_rungs()
    q = {r: False for r in rungs}
    q[rungs[3]] = True
    q[rungs[4]] = True
    assert L.select(q) == rungs[3], L.select(q)


def ladder_failclosed():
    L = mk_ladder()
    q = {r: False for r in L.ordered_rungs()}
    try:
        L.select(q)
    except ValueError as exc:
        assert 'FAIL_CLOSED_NO_MASKING_AUTHORITY' in str(exc), str(exc)
        return
    raise AssertionError('no-qualifier did not fail closed')


def ladder_partial_rejected():
    L = mk_ladder()
    rungs = L.ordered_rungs()
    q = {rungs[0]: False, rungs[1]: True}
    try:
        L.select(q)
    except ValueError as exc:
        assert 'explicit qualification verdict' in str(exc), str(exc)
        return
    raise AssertionError('partial verdict map accepted')


def ladder_reorder_rejected():
    try:
        L = mk_ladder()
        object.__setattr__(L, 'rungs', tuple(reversed(FROZEN_BURDEN_LADDER)))
        L.validate()
    except ValueError:
        return
    raise AssertionError('reordered ladder accepted')


def ladder_extend_rejected():
    try:
        L = mk_ladder()
        object.__setattr__(L, 'rungs', FROZEN_BURDEN_LADDER + ((2, 5),))
        L.validate()
    except ValueError:
        return
    raise AssertionError('extended ladder accepted')


def ladder_universe_rejected():
    try:
        L = mk_ladder()
        object.__setattr__(L, 'terminal_universe_size', 17405)
        L.validate()
    except ValueError:
        return
    raise AssertionError('loose universe size accepted')


check('universe_burden_for == floor(f*17186) [recomputed independently]', ladder_universe_burden)
check('co_mask_count_for == floor(f*17185) [recomputed independently]', ladder_co_mask_count)
check('the three burden integers genuinely differ on 4 of 6 rungs', ladder_three_quantities_distinct)
check('BURDEN_LADDER_PROVENANCE agrees with independent recomputation', ladder_provenance_matches_recomputation)
check('ladder and evidence-budget authority agree exactly', ladder_budget_agree)
check('off-ladder budget fraction rejected', ladder_rejects_offladder_budget)
check('select returns the LOWEST qualifying rung', ladder_lowest)
check('no qualifier -> fail closed', ladder_failclosed)
check('partial verdict map rejected', ladder_partial_rejected)
check('reordered ladder rejected', ladder_reorder_rejected)
check('extended ladder rejected (no post-hoc rung)', ladder_extend_rejected)
check('loose universe size 17405 rejected', ladder_universe_rejected)

print()
print('=== E. digests are stable and distinct ===')


def digest_stable():
    a = mk_v2(3, 20).canonical_digest()
    b = mk_v2(3, 20).canonical_digest()
    assert a == b


def digest_distinct():
    a = mk_v2(3, 20).canonical_digest()
    b = mk_v2(1, 5).canonical_digest()
    assert a != b


def digest_v1_v2_distinct():
    assert mk_v1(3, 20).canonical_digest() != mk_v2(3, 20).canonical_digest()


check('digest deterministic', digest_stable)
check('different fraction -> different digest', digest_distinct)
check('V1 and V2 digests differ (no role splicing)', digest_v1_v2_distinct)

print()
print('=' * 60)
if fails:
    print('SELF_AUDIT_FAILURES: %d' % len(fails))
    for n, e in fails:
        print('   %s : %s' % (n, e))
    raise SystemExit(1)
print('SELF_AUDIT_ALL_PASS')
