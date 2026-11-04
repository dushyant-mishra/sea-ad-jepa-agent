from __future__ import annotations

import pytest

from scripts.v5.td_unified import task4_publication_guard_v1 as p


SECRET = b"DUMMY-FINAL-SECRET-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def test_secret_scan_catches_each_publication_surface():
    clean = dict(
        repository_bytes=b"clean repo",
        log_bytes=b"clean log",
        artifact_bytes=(b"clean artifact",),
        receipt_bytes=(b"clean receipt",),
        path_strings=("results/clean.json",),
    )
    for key, value in [
        ("repository_bytes", b"prefix" + SECRET + b"suffix"),
        ("log_bytes", SECRET),
        ("artifact_bytes", (b"x" + SECRET,)),
        ("receipt_bytes", (SECRET,)),
        ("path_strings", ("out/" + SECRET.decode() + ".json",)),
    ]:
        kwargs = dict(clean)
        kwargs[key] = value
        with pytest.raises(p.Task4PublicationLeak):
            p.scan_publication_surface(secret_tokens=(SECRET,), **kwargs)


def test_clean_publication_surface_passes():
    p.scan_publication_surface(
        secret_tokens=(SECRET,), repository_bytes=b"clean", log_bytes=b"clean",
        artifact_bytes=(b"a",), receipt_bytes=(b"r",), path_strings=("safe/path",),
    )


def test_refusal_message_never_echoes_attacker_secret():
    err = p.Task4CustodyRefusal("HIDDEN_MATERIAL_MISMATCH")
    assert str(err) == "HIDDEN_MATERIAL_MISMATCH"
    assert SECRET.decode() not in str(err)


def test_programming_error_is_not_custody_refusal():
    assert not issubclass(RuntimeError, p.Task4CustodyRefusal)
    with pytest.raises(RuntimeError):
        raise RuntimeError("internal programming failure")
