from __future__ import annotations
import importlib.util
from pathlib import Path
import zipfile
import gzip

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/validate_open_promoter_resource_bytes_v1.py"
    spec=importlib.util.spec_from_file_location("v64_validate_open_resources",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_validator_rejects_html_disguised_as_xlsx(tmp_path):
    m=_load()
    p=tmp_path/"fake.xlsx"
    p.write_text("<!DOCTYPE html><html><title>Client Challenge</title></html>")
    try:
        m.validate_xlsx(p)
    except ValueError as e:
        assert "HTML" in str(e)
    else:
        raise AssertionError("HTML disguised as XLSX must fail closed")


def test_validator_accepts_minimal_real_xlsx_structure(tmp_path):
    m=_load()
    p=tmp_path/"ok.xlsx"
    with zipfile.ZipFile(p,"w") as z:
        z.writestr("[Content_Types].xml","<Types/>")
        z.writestr("xl/workbook.xml","<workbook/>")
        z.writestr("xl/worksheets/sheet1.xml","<worksheet/>")
    out=m.validate_xlsx(p)
    assert out["kind"]=="xlsx"
    assert out["worksheet_xml_count"]==1


def test_validator_rejects_malformed_bed(tmp_path):
    m=_load()
    p=tmp_path/"bad.bed"
    p.write_text("chr1\t100\t90\n")
    try:
        m.validate_bed(p)
    except ValueError as e:
        assert "invalid BED coordinates" in str(e)
    else:
        raise AssertionError("invalid BED must fail closed")


def test_validator_accepts_gzip_text_fixture(tmp_path):
    m=_load()
    p=tmp_path/"a.txt.gz"
    with gzip.open(p,"wt",encoding="utf-8") as f:
        f.write("a\tb\tc\n")
    out=m.validate_gzip_text(p)
    assert out["kind"]=="gzip_text"
