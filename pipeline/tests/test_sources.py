from pathlib import Path

import pytest

from jfl.sources import load_sources


def test_catalog_loads_and_covers_both_levels():
    sources = load_sources()
    assert "mof-fs" in sources
    assert {s.level for s in sources.values()} == {"national", "local"}


def test_mof_fs_has_year_pages():
    src = load_sources()["mof-fs"]
    assert 2024 in src.year_pages
    assert all(url.startswith("https://www.mof.go.jp/") for url in src.year_pages.values())


def test_rejects_duplicate_ids(tmp_path: Path):
    entry = """
  - id: x
    level: national
    publisher: p
    title_ja: t
    title_en: t
    listing_url: https://example.go.jp/
    verified: 2026-01-01
"""
    f = tmp_path / "sources.yaml"
    f.write_text("sources:" + entry + entry, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_sources(f)


def test_rejects_missing_fields(tmp_path: Path):
    f = tmp_path / "sources.yaml"
    f.write_text("sources:\n  - id: x\n    level: national\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing"):
        load_sources(f)
