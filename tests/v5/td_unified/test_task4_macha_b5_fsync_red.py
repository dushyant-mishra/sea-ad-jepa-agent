"""T4-B5: fsync must work with Windows writable-handle semantics."""
from __future__ import annotations
import os
from pathlib import Path
import pytest
from scripts.v5.td_unified import task4_custody_store_v1 as c

class NoTrust:
    trusted_signer_identities=frozenset()
    trusted_anchor_identities=frozenset()

def test_new_store_fsync_does_not_use_readonly_fd(tmp_path, monkeypatch):
    real=os.fsync
    def reject_readonly(fd):
        # Simulate Windows _commit refusing a descriptor opened read-only.
        import fcntl
        mode=fcntl.fcntl(fd,fcntl.F_GETFL) & os.O_ACCMODE
        if mode == os.O_RDONLY:
            raise OSError(9,"simulated Windows EBADF: read-only fsync")
        return real(fd)
    if os.name=="nt":
        pytest.skip("POSIX-only fcntl harness; Windows validation separately required")
    monkeypatch.setattr(os,"fsync",reject_readonly)
    c.PersistentCustodyStore.open(tmp_path/"store",verifier=NoTrust(),expected_head=None)
