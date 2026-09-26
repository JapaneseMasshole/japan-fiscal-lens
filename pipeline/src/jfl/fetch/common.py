"""Shared download helpers: polite HTTP session, link discovery, manifests."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from jfl import __version__

USER_AGENT = (
    f"japan-fiscal-lens/{__version__} "
    "(+https://github.com/JapaneseMasshole/japan-fiscal-lens; open-data research)"
)
REQUEST_DELAY_SECONDS = 1.0  # be gentle with government servers


@dataclass
class Link:
    url: str
    text: str


@dataclass
class ManifestEntry:
    file: str
    source_url: str
    sha256: str
    bytes: int
    fetched_at: str


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def get_html(s: requests.Session, url: str) -> str:
    resp = s.get(url, timeout=60)
    resp.raise_for_status()
    # Japanese government pages are mostly UTF-8 but some older ones are Shift_JIS.
    resp.encoding = resp.apparent_encoding or resp.encoding
    return resp.text


def find_links(html: str, base_url: str, extensions: tuple[str, ...]) -> list[Link]:
    """Return absolute links whose path ends with one of `extensions` (case-insensitive)."""
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    links: list[Link] = []
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"].strip())
        path = url.split("?", 1)[0].split("#", 1)[0].lower()
        if path.endswith(extensions) and url not in seen:
            seen.add(url)
            links.append(Link(url=url, text=" ".join(a.get_text().split())))
    return links


def download(s: requests.Session, url: str, dest: Path) -> ManifestEntry:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    h = hashlib.sha256()
    size = 0
    with s.get(url, timeout=120, stream=True) as resp:
        resp.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                f.write(chunk)
                h.update(chunk)
                size += len(chunk)
    tmp.replace(dest)
    time.sleep(REQUEST_DELAY_SECONDS)
    return ManifestEntry(
        file=dest.name,
        source_url=url,
        sha256=h.hexdigest(),
        bytes=size,
        fetched_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def write_manifest(directory: Path, source_id: str, page_url: str, entries: list[ManifestEntry]):
    manifest = {
        "source_id": source_id,
        "listing_page": page_url,
        "files": [asdict(e) for e in entries],
    }
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
