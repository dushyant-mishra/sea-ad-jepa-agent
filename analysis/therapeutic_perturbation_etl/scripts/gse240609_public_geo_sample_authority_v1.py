"""Independently reviewed GSE240609 public-GEO sample identity, V2.

Biological role truth derives from NCBI GEO GSE240609's PUBLIC SAMPLE TITLES,
not filename substring inference: GSM7703564 APOE3CH-WT, GSM7703567
APOE3CH-PSEN1, GSM7703569 APOE3-WT, GSM7703571 APOE3-PSEN1.
https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE240609

Source file basenames and full-file SHA-256 pins below derive separately from
the physically authenticated PR77 bulk sample-identity receipt. The downloaded
files must be independently rehashed against these frozen roots before V2 ETL.
No missing-sample, unrecognized filename, duplicate design cell or replaced
source is silently accepted.

GEO Series description: CD11b bead-purified microglia isolated after neuron
coculture, NOT unfractionated mixed coculture transcriptome. One biological
sample per 2x2 condition: effect descriptive, no biological SE estimable.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path
from collections.abc import Iterable

SCHEMA = "GSE240609_PUBLIC_GEO_SAMPLE_IDENTITY_V1"
GEO_SERIES = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE240609"
EXPERIMENTAL_MATERIAL = "CD11B_PURIFIED_MICROGLIA_AFTER_NEURON_COCULTURE"

# Exact public GEO titles and independently matched PR77 producer raw-file
# bytes. Source files live on Claude's separate physically authenticated disk.
REVIEWED_SAMPLES = {
    "GSM7703564": {
        "geo_title": "APOE3CH-WT",
        "neuron_genotype": "WT", "microglia_genotype": "APOE3ch",
        "filename": "GSM7703564_45229_14048iN_APOEChurchMG_gene_counts.txt.gz",
        "sha256": "f61d1ba45877aca810a962c59bb7e5fece5448c5bc23fe69b921dfc12d1615be",
    },
    "GSM7703567": {
        "geo_title": "APOE3CH-PSEN1",
        "neuron_genotype": "PSEN", "microglia_genotype": "APOE3ch",
        "filename": "GSM7703567_45232_14048PSEN_iN_APOECHurchMG_gene_counts.txt.gz",
        "sha256": "b7d48bdf0987c888d1563d3ea6da4fcedd817b3ede3d1bcd49439ce4748058e3",
    },
    "GSM7703569": {
        "geo_title": "APOE3-WT",
        "neuron_genotype": "WT", "microglia_genotype": "APOE3",
        "filename": "GSM7703569_45227_14048iN_APOE3MG_gene_counts.txt.gz",
        "sha256": "46db9651d4792bf193eb470827daab4a05f22c11368c054ccb0fab105483ada9",
    },
    "GSM7703571": {
        "geo_title": "APOE3-PSEN1",
        "neuron_genotype": "PSEN", "microglia_genotype": "APOE3",
        "filename": "GSM7703571_45230_14048PSEN_iN_APOE3MG_gene_counts.txt.gz",
        "sha256": "28cbe1b2b5d3dcdcf0085de59b351b41cc91c6cc8cfd6c78f03b6512c1ea9198",
    },
}


class GSE240609AuthorityError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class SampleIdentity:
    gsm: str
    filename: str
    sha256: str
    geo_title: str
    neuron_genotype: str
    microglia_genotype: str
    material: str = EXPERIMENTAL_MATERIAL

    def public_info(self) -> dict:
        return {
            "gsm": self.gsm, "geo_title": self.geo_title,
            "geo_series_url": GEO_SERIES, "file": self.filename,
            "file_sha256": self.sha256,
            "neuron_genotype": self.neuron_genotype,
            "microglia_genotype": self.microglia_genotype,
            "material": self.material,
            "sample_unit": "one original sample per genotype cross",
            "biological_uncertainty_estimable": False,
        }


def validate_sample_basename(name: str) -> SampleIdentity:
    if not isinstance(name, str) or not re.fullmatch(r"GSM[0-9]+_.*\.txt\.gz", name):
        raise GSE240609AuthorityError("unrecognized GEO accession filename")
    gsm = name.split("_", 1)[0]
    record = REVIEWED_SAMPLES.get(gsm)
    if record is None:
        raise GSE240609AuthorityError(f"unreviewed GEO sample accession {gsm}")
    if name != record["filename"]:
        raise GSE240609AuthorityError(
            f"{gsm} basename differs from independently reviewed file assignment"
        )
    return SampleIdentity(
        gsm=gsm, filename=name, sha256=record["sha256"],
        geo_title=record["geo_title"], neuron_genotype=record["neuron_genotype"],
        microglia_genotype=record["microglia_genotype"],
    )


def validate_sample_inventory(
    paths: Iterable[Path], *, test_fixture: bool = False,
) -> tuple[SampleIdentity, ...]:
    """Validate exact 2x2 membership and byte roots before ETL reads any data.

    test_fixture bypasses ONLY physical byte-root matching, never design-cell
    identity. It is reserved for synthetic tests and does not issue receipts.
    """
    files = list(paths)
    if len(files) != 4:
        raise GSE240609AuthorityError(
            "STOP_GSE240609_EXACT_FOUR_INDEPENDENT_GEO_SAMPLE_FILES_REQUIRED"
        )
    entries: dict[str, SampleIdentity] = {}
    cells: set[tuple[str, str]] = set()
    for path in files:
        item = validate_sample_basename(path.name)
        if item.gsm in entries:
            raise GSE240609AuthorityError("duplicated GEO accession source file")
        design = item.neuron_genotype, item.microglia_genotype
        if design in cells:
            raise GSE240609AuthorityError("duplicate genotype design cell")
        if not path.is_file():
            raise GSE240609AuthorityError(f"source file missing: {path.name}")
        if not test_fixture and sha256_file(path) != item.sha256:
            raise GSE240609AuthorityError(
                f"{item.gsm}: source bytes do not match the frozen PR77 file digest"
            )
        cells.add(design)
        entries[item.gsm] = item
    if set(entries) != set(REVIEWED_SAMPLES):
        raise GSE240609AuthorityError("reviewed public GEO sample census mismatch")
    expected_cells = {
        ("WT", "APOE3"), ("WT", "APOE3ch"),
        ("PSEN", "APOE3"), ("PSEN", "APOE3ch"),
    }
    if cells != expected_cells:
        raise GSE240609AuthorityError("genotype cross incomplete or duplicated")
    return tuple(entries[gsm] for gsm in sorted(entries))
