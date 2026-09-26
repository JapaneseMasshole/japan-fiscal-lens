"""Helpers for reading government Excel files safely."""

from __future__ import annotations

import zipfile
from pathlib import Path

OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


class UnreadableWorkbook(Exception):
    """The file exists but cannot be parsed (e.g. rights-management encryption)."""


def check_readable_xlsx(path: Path) -> None:
    """Raise UnreadableWorkbook with a clear reason if `path` is not a plain .xlsx.

    Some official files are published with Microsoft rights-management (DRM)
    encryption or password protection. They keep the .xlsx name but are really
    OLE containers holding an `EncryptedPackage`, which no one outside the
    publishing organisation can open.
    """
    head = path.read_bytes()[:8]
    if head == OLE_MAGIC:
        import olefile

        with olefile.OleFileIO(str(path)) as ole:
            streams = {"/".join(s) for s in ole.listdir()}
        if "EncryptedPackage" in streams:
            kind = (
                "Microsoft rights-management (DRM) protection"
                if any("DRMEncrypted" in s for s in streams)
                else "password protection"
            )
            raise UnreadableWorkbook(f"{path} is encrypted with {kind}; it cannot be opened.")
        raise UnreadableWorkbook(f"{path} is a legacy .xls file saved with an .xlsx name.")
    if not zipfile.is_zipfile(path):
        raise UnreadableWorkbook(f"{path} is not an Excel workbook.")


def norm(text: object) -> str:
    """Normalize a label: strip all whitespace (incl. full-width and newlines)."""
    return "".join(str(text).split()) if text is not None else ""
