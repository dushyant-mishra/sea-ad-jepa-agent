"""Publication-surface secret guard for Unified Task 4."""
from __future__ import annotations


class Task4PublicationLeak(ValueError):
    pass


class Task4CustodyRefusal(Exception):
    """Expected custody refusal carrying only a stable public code."""
    def __init__(self, code: str):
        if type(code) is not str or not code or any(ch in code for ch in "\r\n"):
            raise ValueError("refusal code must be narrow public text")
        self.code = code
        super().__init__(code)


def _check(blob: bytes, secret: bytes, label: str) -> None:
    if secret and secret in blob:
        raise Task4PublicationLeak(f"secret token detected in {label}")


def scan_publication_surface(
    *,
    secret_tokens: tuple[bytes, ...],
    repository_bytes: bytes,
    log_bytes: bytes,
    artifact_bytes: tuple[bytes, ...],
    receipt_bytes: tuple[bytes, ...],
    path_strings: tuple[str, ...],
) -> None:
    for secret in secret_tokens:
        if type(secret) is not bytes or not secret:
            raise ValueError("secret_tokens must contain non-empty bytes")
        _check(repository_bytes, secret, "repository")
        _check(log_bytes, secret, "logs")
        for i, blob in enumerate(artifact_bytes):
            _check(blob, secret, f"artifact[{i}]")
        for i, blob in enumerate(receipt_bytes):
            _check(blob, secret, f"receipt[{i}]")
        encoded_paths = "\n".join(path_strings).encode("utf-8", errors="strict")
        _check(encoded_paths, secret, "paths")
