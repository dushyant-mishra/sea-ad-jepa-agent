"""Outcome-blind precision/estimability helpers for target-tournament design."""
import math


class PrecisionContractError(ValueError):
    pass


def _exact_number(value, label):
    if isinstance(value, bool) or type(value) not in (int, float):
        raise PrecisionContractError(f'{label} must be an exact JSON numeric value')
    numeric = float(value)
    if not math.isfinite(numeric):
        raise PrecisionContractError(f'{label} must be finite')
    return numeric


def _validate_alpha(alpha_eff):
    numeric = _exact_number(alpha_eff, 'alpha_eff')
    if not (0.0 < numeric < 1.0):
        raise ValueError('alpha_eff must be in (0,1)')
    return numeric


def minimum_donors_for_sign_resolution(alpha_eff):
    alpha_eff = _validate_alpha(alpha_eff)
    n = 1
    while min(1.0, 2.0 * (0.5 ** n)) > alpha_eff:
        n += 1
    return n


def _binom_tail_ge(k, n):
    return sum(math.comb(n, j) for j in range(k, n + 1)) / (2.0 ** n)


def _binom_tail_le(k, n):
    return sum(math.comb(n, j) for j in range(0, k + 1)) / (2.0 ** n)


def exact_two_sided_sign_p(successes, n_nonzero):
    if (
        isinstance(successes, bool)
        or isinstance(n_nonzero, bool)
        or type(successes) is not int
        or type(n_nonzero) is not int
        or n_nonzero < 0
        or successes < 0
        or successes > n_nonzero
    ):
        raise ValueError('invalid sign counts')
    if n_nonzero == 0:
        return 1.0
    lower = _binom_tail_le(successes, n_nonzero)
    upper = _binom_tail_ge(successes, n_nonzero)
    return min(1.0, 2.0 * min(lower, upper))


def _validate_donor_deltas(donor_deltas):
    if not isinstance(donor_deltas, list):
        raise PrecisionContractError('donor_deltas must be a list')
    seen = set()
    normalized = []
    for i, record in enumerate(donor_deltas):
        if not isinstance(record, dict) or set(record) != {'donor_id', 'delta'}:
            raise PrecisionContractError(
                'each donor_deltas record must contain exactly donor_id and delta'
            )
        donor_id = record['donor_id']
        if (
            not isinstance(donor_id, str)
            or not donor_id
            or donor_id != donor_id.strip()
            or '\0' in donor_id
        ):
            raise PrecisionContractError(
                f'donor_deltas[{i}].donor_id must be an exact nonempty NUL-free trimmed string'
            )
        if donor_id in seen:
            raise PrecisionContractError(f'duplicate donor_id: {donor_id}')
        seen.add(donor_id)
        delta = _exact_number(record['delta'], f'donor_deltas[{i}].delta')
        normalized.append((donor_id, delta))
    return normalized


def sign_recurrence_gate(donor_deltas, alpha_eff):
    alpha_eff = _validate_alpha(alpha_eff)
    normalized = _validate_donor_deltas(donor_deltas)
    clean = [delta for _, delta in normalized]
    positives = sum(x > 0 for x in clean)
    negatives = sum(x < 0 for x in clean)
    ties = sum(x == 0 for x in clean)
    if positives + negatives + ties != len(clean):
        raise AssertionError('sign accounting invariant failed')
    n = positives + negatives
    min_n = minimum_donors_for_sign_resolution(alpha_eff)
    p = exact_two_sided_sign_p(positives, n)
    estimable = n >= min_n
    return {
        'donor_ids_bound': True,
        'n_total_donors': len(clean),
        'n_nonzero_donors': n,
        'n_positive_donors': positives,
        'n_negative_donors': negatives,
        'n_tied_donors': ties,
        'minimum_nonzero_donors_for_resolution': min_n,
        'resolution_estimable': estimable,
        'two_sided_p': p,
        'alpha_eff': alpha_eff,
        'pass': bool(estimable and positives > negatives and p <= alpha_eff),
    }


def minimum_permutation_draws_for_resolution(alpha_eff):
    alpha_eff = _validate_alpha(alpha_eff)
    return max(1, math.ceil(1.0 / alpha_eff) - 1)
