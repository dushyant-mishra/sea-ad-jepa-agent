"""Independent Task2 exact-type attacks against Macha custody on repaired Task1.

All values are dummy fixtures. They test actual underlying bytes, not the
subclass's claimed length, iterator, integer representation or metadata.
No production nonce, withheld family, sealed run or realization involved.
"""
from __future__ import annotations

import pytest
from scripts.production_synthetic import custody_v1 as C


class _ShortNonceForgedAsLong(bytes):
    def __len__(self):
        return 64
    def __iter__(self):
        return iter(range(64))


class _ShortRootForgedAs32(bytes):
    def __len__(self):
        return 32
    def __iter__(self):
        return iter(range(32))


class _ForgedNumber(int):
    def __lt__(self, other):
        return False
    def __ge__(self, other):
        return False
    def to_bytes(self, length, byteorder):
        return (1).to_bytes(length, byteorder)


class _ForgedHex(str):
    def __len__(self):
        return 64
    def __iter__(self):
        return iter("a" * 64)


def test_t2_secret_nonce_256bit_check_uses_physical_byte_length():
    nonce=_ShortNonceForgedAsLong(b"x")
    assert bytes.__len__(nonce)==1
    with pytest.raises(C.CustodyError):
        C.commit_secret(nonce, "e"*64, "DUMMY_COMMIT")


def test_t2_root_256bit_check_uses_physical_byte_length():
    root=_ShortRootForgedAs32(b"x")
    assert bytes.__len__(root)==1
    with pytest.raises(C.CustodyError):
        C.stream_seed_digest(
            root, ("world_id","WORLD-1"), ("purpose_tag","DUMMY")
        )


def test_t2_nonce_commitment_cannot_accept_spoofed_secret_length():
    with pytest.raises(C.CustodyError):
        C.nonce_commitment(_ShortNonceForgedAsLong(b"x"))


def test_t2_integer_budget_cannot_override_domain_checks():
    root=bytes(range(32))
    bad=_ForgedNumber(-1)
    assert int.__int__(bad)==-1
    with pytest.raises(C.CustodyError):
        C.authorized_realization_ids(root, "SYNTH_DEBUG", bad)


def test_t2_malformed_digest_subclass_uses_actual_string_content():
    forged=_ForgedHex("0")
    assert str.__len__(forged)==1
    with pytest.raises(C.CustodyError):
        C.commit_secret(bytes(range(32)), forged, "DUMMY_COMMIT")
