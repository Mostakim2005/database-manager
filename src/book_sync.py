#!/usr/bin/env python3
"""Book Domain — Alexandria Library Hybrid Sync & Safe Cover Extractor.

Incorporates genuine book volumes from E:\\Books\\catalogs\\catalog_index.json
into two complementary layers:
  1. Sanitized Public Catalog (data/book/books.json):
     Preserves curated highlights (with verified Open Library covers) plus
     sanitized Alexandria metadata (title, author, subject, normalized format,
     reading/ownership status) — strictly excluding Windows paths, URIs,
     utility shortcuts, and private links.
  2. Gitignored Local Library Map (data/book/local_library.json):
     Maps book IDs to verified local filesystem paths inside E:\\Books and
     pre-indexes embedded EPUB cover zip members for zero-bloat O(1) serving
     via GET /api/book/cover?id=<book_id>.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import mimetypes
import os
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
BOOK_DATA_DIR = ROOT_DIR / "data" / "book"
PUBLIC_BOOKS_FILE = BOOK_DATA_DIR / "books.json"
LOCAL_LIBRARY_FILE = BOOK_DATA_DIR / "local_library.json"

DEFAULT_ALEXANDRIA_ROOT = Path(r"E:\Books")
DEFAULT_CATALOG_INDEX = DEFAULT_ALEXANDRIA_ROOT / "catalogs" / "catalog_index.json"

CURATED_COVER_URLS: dict[str, dict[str, str]] = {
    "ddia-kleppmann": {
        "isbn": "9781449373320",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781449373320-M.jpg?default=false",
    },
    "pragmatic-programmer-20th": {
        "isbn": "9780135957059",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780135957059-M.jpg?default=false",
    },
    "genki-1-3rd": {
        "isbn": "9784789017305",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9784789017305-M.jpg?default=false",
    },
    "art-of-strategy-dixit": {
        "isbn": "9780393337174",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780393337174-M.jpg?default=false",
    },
    "the-last-wish-witcher-1": {
        "isbn": "9780316029186",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780316029186-M.jpg?default=false",
    },
    "sword-of-destiny-witcher-2": {
        "isbn": "9780316389709",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780316389709-M.jpg?default=false",
    },
    "metro-2033-glukhovsky": {
        "isbn": "9780575086258",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780575086258-M.jpg?default=false",
    },
    "rainbow-six-clancy": {
        "isbn": "9780425170342",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780425170342-M.jpg?default=false",
    },
    "assassins-creed-renaissance": {
        "isbn": "9780441019298",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9780441019298-M.jpg?default=false",
    },
    "metro-2034-glukhovsky": {
        "cover_url": "https://covers.openlibrary.org/b/id/8428171-M.jpg?default=false",
    },
    "metro-2035-glukhovsky": {
        "isbn": "9781539930723",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781539930723-M.jpg?default=false",
    },
    "dishonored-corroded-man": {
        "isbn": "9781783293049",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781783293049-M.jpg?default=false",
    },
    "alien-isolation-novel": {
        "isbn": "9781789093070",
        "cover_url": "https://covers.openlibrary.org/b/isbn/9781789093070-M.jpg?default=false",
    },
}

REFERENCE_DOMAINS = {
    "Mathematics",
    "Physics",
    "Chemistry",
    "Electrical Engineering",
    "Computer Science",
    "Admission",
    "English",
    "A Very Short Introduction",
    "General Knowledge",
    "10 Minute School",
}

FORMAT_MAP = {
    "PDF": "pdf",
    "M4B": "audiobook",
    "EPUB": "ebook",
    "MOBI": "ebook",
    "AZW3": "ebook",
    "DJVU": "ebook",
    "CBZ": "ebook",
    "MHTML": "ebook",
    "HTML": "ebook",
    "DOCX": "ebook",
    "TXT": "ebook",
}


def _slugify(text: str, max_len: int = 38) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:max_len].strip("-")) or "book"


def _make_alexandria_id(entry: dict[str, Any]) -> str:
    basis = str(entry.get("relative_path") or f"{entry.get('domain')}|{entry.get('title')}|{entry.get('author')}|{entry.get('format')}")
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:7]
    prefix = _slugify(str(entry.get("title") or "vol"), max_len=34)
    return f"alex-{prefix}-{digest}"


def _format_subject(domain: str, subfolder: str) -> str:
    dom = (domain or "General").strip()
    sub = (subfolder or "").strip()
    if sub and sub != ".":
        leaf = sub.split("/")[-1].strip()
        if leaf and leaf.lower() != dom.lower():
            return f"{dom} · {leaf}"
    return dom


def find_epub_cover_member(epub_path: Path) -> str | None:
    """Inspect an EPUB archive and return the zip member name of its cover image, if present."""
    if not epub_path.is_file():
        return None
    try:
        with zipfile.ZipFile(epub_path, "r") as zf:
            names = zf.namelist()
            name_map = {n.lower(): n for n in names}

            # 1. Inspect container.xml -> OPF manifest cover-image / meta[name="cover"]
            opf_path = None
            if "meta-inf/container.xml" in name_map:
                try:
                    croot = ET.fromstring(zf.read(name_map["meta-inf/container.xml"]))
                    for elem in croot.iter():
                        if elem.tag.endswith("rootfile") and elem.attrib.get("full-path"):
                            opf_path = elem.attrib["full-path"]
                            break
                except (ET.ParseError, KeyError):
                    opf_path = None

            if opf_path and opf_path.lower() in name_map:
                real_opf = name_map[opf_path.lower()]
                opf_dir = posixpath.dirname(real_opf)
                try:
                    oroot = ET.fromstring(zf.read(real_opf))
                    cover_id = None
                    href_by_id: dict[str, str] = {}
                    for elem in oroot.iter():
                        tag = elem.tag.rsplit("}", 1)[-1]
                        if tag == "meta" and elem.attrib.get("name", "").lower() == "cover":
                            cover_id = elem.attrib.get("content")
                        elif tag == "item":
                            iid = elem.attrib.get("id")
                            href = elem.attrib.get("href")
                            props = (elem.attrib.get("properties") or "").lower()
                            mtype = (elem.attrib.get("media-type") or "").lower()
                            if iid and href:
                                href_by_id[iid] = href
                            if "cover-image" in props and href and mtype.startswith("image/"):
                                candidate = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
                                if candidate.lower() in name_map:
                                    return name_map[candidate.lower()]
                    if cover_id and cover_id in href_by_id:
                        href = href_by_id[cover_id]
                        candidate = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
                        if candidate.lower() in name_map:
                            return name_map[candidate.lower()]
                except (ET.ParseError, KeyError):
                    pass

            # 2. Fallback heuristic: image filenames mentioning cover/title
            img_exts = (".jpg", ".jpeg", ".png", ".webp")
            imgs = [n for n in names if n.lower().endswith(img_exts)]
            for cand in imgs:
                base = posixpath.basename(cand).lower()
                if "cover" in base or "title" in base:
                    return cand
            return imgs[0] if imgs else None
    except (zipfile.BadZipFile, OSError):
        return None


def sync_alexandria_library(
    catalog_index_path: Path = DEFAULT_CATALOG_INDEX,
    alexandria_root: Path = DEFAULT_ALEXANDRIA_ROOT,
    public_books_path: Path = PUBLIC_BOOKS_FILE,
    local_library_path: Path = LOCAL_LIBRARY_FILE,
    scan_epub_covers: bool = True,
) -> dict[str, Any]:
    """Sync curated books + E:\\Books Alexandria volumes safely across public/local layers."""
    existing_data: dict[str, Any] = {}
    if public_books_path.exists():
        try:
            existing_data = json.loads(public_books_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing_data = {}

    curated_books: list[dict[str, Any]] = []
    for item in existing_data.get("books", []):
        bid = str(item.get("id") or "")
        if bid.startswith("alex-"):
            continue
        rec = dict(item)
        rec["source"] = rec.get("source") or "curated"
        if bid in CURATED_COVER_URLS:
            for k, v in CURATED_COVER_URLS[bid].items():
                rec.setdefault(k, v)
        curated_books.append(rec)

    if not catalog_index_path.is_file():
        return {
            "status": "skipped",
            "reason": f"Catalog index not found at {catalog_index_path}",
            "curated_count": len(curated_books),
            "alexandria_count": 0,
            "total_books": len(curated_books),
        }

    raw_index = json.loads(catalog_index_path.read_text(encoding="utf-8"))
    if not isinstance(raw_index, list):
        raise ValueError("Expected list inside Alexandria catalog_index.json")

    domain_covers: dict[str, str] = {}
    for entry in raw_index:
        if entry.get("classification") == "Directory Visual Asset":
            dom = str(entry.get("domain") or "ROOT")
            rel = str(entry.get("relative_path") or "")
            if rel and dom not in domain_covers:
                domain_covers[dom] = str(alexandria_root / rel)

    sanitized_alex: list[dict[str, Any]] = []
    local_entries: dict[str, dict[str, Any]] = {}
    seen_ids = {str(b.get("id")) for b in curated_books}
    epub_cover_hits = 0

    for entry in raw_index:
        if entry.get("classification") != "Book / Volume":
            continue
        title = str(entry.get("canonical_title") or entry.get("title") or "").strip()
        if not title:
            continue

        bid = _make_alexandria_id(entry)
        if bid in seen_ids:
            continue
        seen_ids.add(bid)

        domain = str(entry.get("domain") or "General").strip()
        subfolder = str(entry.get("subfolder") or ".").strip()
        author = str(entry.get("canonical_author") or entry.get("author") or "Unknown Author").strip()
        if author in ("N/A", "Unknown"):
            author = "Various / Reference"
        edition = str(entry.get("edition") or "").strip()
        raw_fmt = str(entry.get("format") or "PDF").strip().upper()
        norm_fmt = FORMAT_MAP.get(raw_fmt, "ebook")
        size_str = str(entry.get("size_str") or "").strip()
        subject = _format_subject(domain, subfolder)
        read_status = "reference" if domain in REFERENCE_DOMAINS else "queued"

        full_title = f"{title} ({edition})" if edition and edition.lower() not in title.lower() else title
        note_parts = [f"Digital {raw_fmt}"]
        if size_str:
            note_parts.append(size_str)
        note_parts.append(f"Subject: {subject}")

        sanitized_alex.append(
            {
                "id": bid,
                "title": full_title,
                "author": author,
                "subject": subject,
                "format": norm_fmt,
                "ownership_status": "owned",
                "reading_status": read_status,
                "rating": 0,
                "pages": 0,
                "source": "alexandria",
                "notes": " · ".join(note_parts),
            }
        )

        rel_path = str(entry.get("relative_path") or "").strip()
        local_path = str(alexandria_root / rel_path) if rel_path else str(entry.get("path") or "")
        epub_member = None
        if scan_epub_covers and raw_fmt == "EPUB" and local_path:
            epub_member = find_epub_cover_member(Path(local_path))
            if epub_member:
                epub_cover_hits += 1

        local_entries[bid] = {
            "local_path": local_path,
            "relative_path": rel_path,
            "domain": domain,
            "format_raw": raw_fmt,
            "size_str": size_str,
            "epub_cover_member": epub_member,
            "has_epub_cover": bool(epub_member),
        }

    today = datetime.date.today().isoformat()
    merged_public = {
        "schema_version": "2.0.0",
        "updated_at": today,
        "books": curated_books + sanitized_alex,
    }
    public_books_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_pub = public_books_path.with_suffix(".json.tmp")
    tmp_pub.write_text(json.dumps(merged_public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_pub.replace(public_books_path)

    local_payload = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "library_root": str(alexandria_root),
        "total_local_books": len(local_entries),
        "epub_cover_count": epub_cover_hits,
        "domain_covers": domain_covers,
        "entries": local_entries,
    }
    tmp_loc = local_library_path.with_suffix(".json.tmp")
    tmp_loc.write_text(json.dumps(local_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_loc.replace(local_library_path)

    return {
        "status": "ok",
        "curated_count": len(curated_books),
        "alexandria_count": len(sanitized_alex),
        "total_books": len(merged_public["books"]),
        "epub_covers_indexed": epub_cover_hits,
        "domains_count": len({b["subject"].split(" · ")[0] for b in sanitized_alex}),
    }


def load_local_library(local_library_path: Path = LOCAL_LIBRARY_FILE) -> dict[str, Any]:
    """Load gitignored local_library.json metadata safely if present on this machine."""
    if not local_library_path.is_file():
        return {}
    try:
        data = json.loads(local_library_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def load_merged_book_payload(
    public_books_path: Path = PUBLIC_BOOKS_FILE,
    local_library_path: Path = LOCAL_LIBRARY_FILE,
) -> dict[str, Any]:
    """Load sanitized books.json and enrich dynamically with gitignored local library & EPUB covers."""
    if not public_books_path.is_file():
        return {"books": []}
    data = json.loads(public_books_path.read_text(encoding="utf-8"))
    books = list(data.get("books", []))
    local = load_local_library(local_library_path)
    entries = local.get("entries") if isinstance(local.get("entries"), dict) else {}

    enriched: list[dict[str, Any]] = []
    local_matches = 0
    for item in books:
        rec = dict(item)
        bid = str(rec.get("id") or "")
        if bid in CURATED_COVER_URLS and not rec.get("cover_url"):
            rec["cover_url"] = CURATED_COVER_URLS[bid].get("cover_url", "")
        loc = entries.get(bid)
        if isinstance(loc, dict):
            local_matches += 1
            rec["has_local_file"] = True
            rec["format_raw"] = loc.get("format_raw") or str(rec.get("format") or "").upper()
            rec["size_str"] = loc.get("size_str") or ""
            rec["local_relative_path"] = loc.get("relative_path") or ""
            if loc.get("has_epub_cover") and not rec.get("cover_url"):
                rec["cover_url"] = f"/api/book/cover?id={bid}"
        enriched.append(rec)

    out = dict(data)
    out["books"] = enriched
    out["local_library_available"] = bool(local)
    out["local_matched_count"] = local_matches
    return out


def get_book_cover_bytes(
    book_id: str,
    local_library_path: Path = LOCAL_LIBRARY_FILE,
) -> tuple[bytes, str] | None:
    """Safely extract embedded EPUB cover bytes for a verified local Alexandria book ID."""
    local = load_local_library(local_library_path)
    entries = local.get("entries") if isinstance(local.get("entries"), dict) else {}
    loc = entries.get(str(book_id or "").strip())
    if not isinstance(loc, dict):
        return None
    root_str = str(local.get("library_root") or DEFAULT_ALEXANDRIA_ROOT)
    root_resolved = Path(root_str).resolve()
    raw_file = Path(str(loc.get("local_path") or ""))
    try:
        resolved = raw_file.resolve()
        resolved.relative_to(root_resolved)
    except (OSError, ValueError):
        return None

    member = loc.get("epub_cover_member")
    if member and resolved.is_file() and resolved.suffix.lower() == ".epub":
        try:
            with zipfile.ZipFile(resolved, "r") as zf:
                blob = zf.read(member)
                ctype, _ = mimetypes.guess_type(member)
                return blob, (ctype or "image/jpeg")
        except (OSError, KeyError, zipfile.BadZipFile):
            return None
    return None


def open_local_book_file(
    book_id: str,
    local_library_path: Path = LOCAL_LIBRARY_FILE,
) -> dict[str, Any]:
    """Open a verified local E:\\Books file in the OS default handler (Windows loopback-only)."""
    local = load_local_library(local_library_path)
    entries = local.get("entries") if isinstance(local.get("entries"), dict) else {}
    loc = entries.get(str(book_id or "").strip())
    if not isinstance(loc, dict):
        raise LookupError(f"Book ID '{book_id}' has no linked local file in local_library.json")

    root_resolved = Path(str(local.get("library_root") or DEFAULT_ALEXANDRIA_ROOT)).resolve()
    target = Path(str(loc.get("local_path") or "")).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("Refusing to open path outside configured library root") from exc

    if not target.is_file():
        raise FileNotFoundError(f"Local book file missing on disk: {target.name}")

    if hasattr(os, "startfile"):
        os.startfile(str(target))  # type: ignore[attr-defined]
        return {"status": "opened", "filename": target.name, "relative_path": loc.get("relative_path", "")}
    raise OSError("os.startfile is supported only on Windows hosts")


if __name__ == "__main__":
    summary = sync_alexandria_library()
    print(json.dumps(summary, indent=2))
