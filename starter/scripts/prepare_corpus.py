"""Reproduce the selected OpenStax corpus using Python stdlib and Poppler."""
import csv
import hashlib
import json
import re
import subprocess
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = "https://assets.openstax.org/oscms-prodcms/media/documents/Introduction_to_Python_Programming-WEB.pdf"
SOURCE_ID = "openstax-introduction-python-ch14-15"
PDF = ROOT / "data/raw/Introduction_to_Python_Programming-WEB.pdf"
ATTRIBUTION = "Access for free at openstax.org."


def normalize(text: str) -> str:
    # Preserve indentation and paragraph boundaries, particularly for Python code.
    text = unicodedata.normalize("NFC", text).replace("\u00ad", "")
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").splitlines()]
    text = "\n".join(line for line in lines if line.strip() != ATTRIBUTION)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def main() -> None:
    PDF.parent.mkdir(parents=True, exist_ok=True)
    output = ROOT / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    if not PDF.exists():
        temporary = PDF.with_suffix(".download")
        urllib.request.urlretrieve(URL, temporary)
        temporary.replace(PDF)
    sha256 = hashlib.sha256(PDF.read_bytes()).hexdigest()
    manifest_path = ROOT / "data/manifest.json"
    accessed = datetime.now(timezone.utc).isoformat()
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        if old.get("sha256") == sha256:
            accessed = old["accessed_at"]
    version = subprocess.check_output(
        ["pdftotext", "-v"], stderr=subprocess.STDOUT, text=True
    ).splitlines()[0]
    info = subprocess.check_output(["pdfinfo", str(PDF)], text=True)
    total = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
    raw = subprocess.check_output(
        ["pdftotext", "-f", "319", "-l", "370", "-layout", str(PDF), "-"],
        encoding="utf-8",
    ).split("\f")
    assert len(raw) == 53 and not raw[-1].strip(), "Unexpected page extraction"
    pages, audit = [], []
    for number, text in enumerate(raw[:-1], 319):
        text = normalize(text)
        if not text:
            raise ValueError(f"No extracted text on PDF page {number}; OCR/review needed")
        chapter = 14 if number <= 340 else 15
        reason = "teaching_content"
        if number in (319, 341):
            reason = "chapter_opening_excluded_conservatively"
        elif 338 <= number <= 340 or 367 <= number <= 370:
            reason = "chapter_summary_excluded_conservatively"
        elif number == 358:
            reason = "sparse_table_continuation_excluded_conservatively"
        counted = reason == "teaching_content"
        page_id = f"{SOURCE_ID}:pdf-{number}"
        pages.append({
            "page_id": page_id, "document_id": SOURCE_ID,
            "source": str(PDF.relative_to(ROOT)), "source_url": URL,
            "page": number, "printed_page": number - 10,
            "text": text, "char_count": len(text),
            "metadata": {
                "chapter": chapter,
                "chapter_title": "Files" if chapter == 14 else "Data Science",
                "language": "en", "counted_content_page": counted,
            },
            "attribution": ATTRIBUTION,
        })
        audit.append({
            "page_id": page_id, "pdf_page": number, "printed_page": number - 10,
            "chapter": chapter, "char_count": len(text),
            "counted_content_page": counted, "reason": reason,
            "review_note": "Text extraction checked; verify tables, figures and evidence against PDF before benchmark labeling",
        })
    counted = sum(p["metadata"]["counted_content_page"] for p in pages)
    assert counted >= 30
    (output / "pages.jsonl").write_text(
        "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pages), encoding="utf-8"
    )
    with (output / "page_audit.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(audit[0]))
        writer.writeheader()
        writer.writerows(audit)
    license_text = subprocess.check_output(
        ["pdftotext", "-f", "4", "-l", "4", "-layout", str(PDF), "-"],
        encoding="utf-8",
    )
    assert "CC BY-NC-SA 4.0" in license_text
    (output / "source_license.txt").write_text(license_text, encoding="utf-8")
    manifest = {
        "source_id": SOURCE_ID, "title": "Introduction to Python Programming",
        "publisher": "OpenStax, Rice University", "source_path_or_url": URL,
        "local_path": str(PDF.relative_to(ROOT)), "sha256": sha256,
        "accessed_at": accessed, "original_publication_year": 2024,
        "snapshot_note": "Downloaded PDF copyright 2026; SHA-256 identifies exact snapshot",
        "license_or_permission": "CC BY-NC-SA 4.0; see PDF physical page 4 for attribution terms and third-party exclusions",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "attribution": ATTRIBUTION,
        "total_pdf_pages": total, "selected_pdf_pages": [319, 370],
        "selected_printed_pages": [309, 360], "retained_page_count": len(pages),
        "counted_content_page_count": counted,
        "counting_rule": "Count physical teaching pages in chapters 14-15, conservatively excluding chapter openings (319,341), summary pages (338-340,367-370), and sparse table continuation (358). Keep all 52 selected pages in retrieval corpus for context. PDF pages are 1-based; printed page = PDF page - 10 in this selection.",
        "extractor": version, "extraction_mode": "pdftotext -layout",
        "normalization": "Unicode NFC; remove soft hyphens and repeated attribution footer; trim trailing whitespace; collapse excessive blank lines; preserve code indentation. Page headers retained. Attribution stored separately on every page record.",
        "metadata_filter": {"field": "chapter", "type": "integer", "values": [14, 15], "provenance": "PDF chapter headings and table of contents"},
        "outputs": ["data/processed/pages.jsonl", "data/processed/page_audit.csv", "data/processed/source_license.txt"],
        "limitations": ["No OCR needed for the selected text layer. Layout extraction may flatten tables, detach code or lose information in figures.", "Extraction checks are not verification of benchmark evidence; each future gold quote must be checked against the source PDF."],
        "pages": [{"page_id": p["page_id"], "pdf_page": p["page"], "printed_page": p["printed_page"], "char_count": p["char_count"], "counted_content_page": p["metadata"]["counted_content_page"]} for p in pages],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(pages)} pages; {counted} conservatively counted content pages; {sum(p['char_count'] for p in pages)} normalized characters.")
    print(f"Source SHA-256: {sha256}")


if __name__ == "__main__":
    main()
