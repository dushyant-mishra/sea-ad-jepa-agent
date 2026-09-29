"""A minimal caching HTTP byte-range file object, so h5py can read a remote
.h5ad without downloading it.

WHY THIS EXISTS. The NIH-CARD deposit is 33 GB across two files. The schema
probe needs obs/var metadata and a bounded sample of matrix values -- a few tens
of megabytes at most. Downloading 33 GB to read that is wasteful, and in this
environment the usual route is unavailable anyway: `fsspec`'s HTTP backend needs
`aiohttp`, and `aiohttp` cannot even be imported here because the interpreter's
SSL certificate store raises

    ssl.SSLError: [ASN1: NOT_ENOUGH_DATA] not enough data

`requests` with an explicit `certifi` bundle works and returns 206 Partial
Content, so this class is built on that.

DESIGN NOTES
  - HDF5 issues many small, scattered reads. Serving each one as its own HTTP
    request would be unusably slow, so reads are served from a block cache with
    a bounded number of blocks (LRU eviction).
  - Every HTTP request is counted and the counts are exposed, because a probe
    that silently makes 200,000 requests is a different thing from one that
    makes 200, and the receipt should be able to say which happened.
  - A server that ignores Range and returns 200 with the whole body would
    silently produce correct-looking results after transferring the entire file.
    That is treated as an ERROR, not quietly accepted.
"""
from __future__ import annotations

import io
from collections import OrderedDict

import certifi
import requests

DEFAULT_BLOCK = 4 * 1024 * 1024
DEFAULT_MAX_BLOCKS = 96          # ~384 MB ceiling at the default block size


class HTTPRangeFile(io.RawIOBase):
    def __init__(self, url: str, block_size: int = DEFAULT_BLOCK,
                 max_blocks: int = DEFAULT_MAX_BLOCKS, timeout: int = 120,
                 session: requests.Session | None = None):
        self.url = url
        self.block_size = int(block_size)
        self.max_blocks = int(max_blocks)
        self.timeout = timeout
        self._pos = 0
        self._cache: "OrderedDict[int, bytes]" = OrderedDict()
        self._s = session or requests.Session()
        self._verify = certifi.where()
        self.n_requests = 0
        self.bytes_fetched = 0

        head = self._s.head(url, timeout=timeout, allow_redirects=True,
                            verify=self._verify)
        head.raise_for_status()
        cl = head.headers.get("content-length")
        if cl is None:
            raise OSError(f"no content-length for {url}; cannot range-read")
        self.size = int(cl)

    # ----------------------------------------------------------- io plumbing
    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self._pos = offset
        elif whence == io.SEEK_CUR:
            self._pos += offset
        elif whence == io.SEEK_END:
            self._pos = self.size + offset
        else:
            raise ValueError(f"bad whence {whence}")
        self._pos = max(0, min(self._pos, self.size))
        return self._pos

    # ------------------------------------------------------------- fetching
    def _fetch_block(self, idx: int) -> bytes:
        blk = self._cache.get(idx)
        if blk is not None:
            self._cache.move_to_end(idx)
            return blk
        start = idx * self.block_size
        end = min(start + self.block_size, self.size) - 1
        if end < start:
            return b""
        r = self._s.get(self.url, headers={"Range": f"bytes={start}-{end}"},
                        timeout=self.timeout, verify=self._verify)
        self.n_requests += 1
        if r.status_code != 206:
            # A 200 here means the server ignored Range and sent everything.
            # Accepting it would work but would quietly transfer the whole file.
            raise OSError(
                f"expected 206 Partial Content, got {r.status_code}; the server "
                f"does not honour Range requests for {self.url}")
        blk = r.content
        self.bytes_fetched += len(blk)
        self._cache[idx] = blk
        self._cache.move_to_end(idx)
        while len(self._cache) > self.max_blocks:
            self._cache.popitem(last=False)
        return blk

    def readinto(self, b) -> int:  # type: ignore[override]
        n = len(b)
        data = self.read(n)
        b[: len(data)] = data
        return len(data)

    def read(self, size: int = -1) -> bytes:  # type: ignore[override]
        if size is None or size < 0:
            size = self.size - self._pos
        size = max(0, min(size, self.size - self._pos))
        if size == 0:
            return b""
        out = bytearray()
        pos = self._pos
        remaining = size
        while remaining > 0:
            idx = pos // self.block_size
            off = pos - idx * self.block_size
            blk = self._fetch_block(idx)
            if not blk:
                break
            take = min(remaining, len(blk) - off)
            if take <= 0:
                break
            out += blk[off: off + take]
            pos += take
            remaining -= take
        self._pos = pos
        return bytes(out)

    def stats(self) -> dict:
        return {"url": self.url, "size_bytes": self.size,
                "block_size": self.block_size, "max_blocks": self.max_blocks,
                "http_requests": self.n_requests,
                "bytes_fetched": self.bytes_fetched,
                "fraction_of_file_fetched": round(self.bytes_fetched / max(1, self.size), 6)}


def open_remote_h5(url: str, **kw):
    """h5py.File over an HTTP range reader. Returns (file, reader)."""
    import h5py
    f = HTTPRangeFile(url, **kw)
    return h5py.File(f, "r"), f
