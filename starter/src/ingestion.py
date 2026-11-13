"""Read PDFs or the prepared, page-addressable JSONL corpus."""
import json
import logging
import re
import unicodedata
from pathlib import Path
from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Preserve paragraph boundaries and Python indentation."""
    text = unicodedata.normalize('NFC', text).replace('\u00ad', '')
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Keep physical page numbers; report errors and pages needing OCR."""
    from pypdf import PdfReader
    result = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        try:
            text = normalize_text(page.extract_text(extraction_mode='layout') or '')
        except Exception:
            logging.exception('PDF extraction failed: document=%s page=%s', document_id, number)
            raise
        if not text:
            logging.warning('Empty text layer: document=%s page=%s; OCR may be needed', document_id, number)
        result.append(DocumentPage(document_id, source, number, text))
    return result


def load_pages(path: Path) -> list[DocumentPage]:
    """Load frozen normalized text without changing character offsets."""
    pages, seen = [], set()
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        key = (record['document_id'], record['page'])
        if key in seen:
            raise ValueError(f'Duplicate document/page at JSONL line {line_number}: {key}')
        if type(record['page']) is not int or record['page'] < 1 or not record['text'].strip():
            raise ValueError(f'Invalid or empty source page at line {line_number}')
        if len(record['text']) != record['char_count']:
            raise ValueError(f'Incorrect char_count at line {line_number}')
        metadata = dict(record['metadata'])
        if type(metadata.get('chapter')) is not int:
            raise ValueError(f'Missing integer chapter at line {line_number}')
        for name in ('page_id', 'printed_page', 'source_url', 'attribution'):
            metadata[name] = record[name]
        pages.append(DocumentPage(record['document_id'], record['source'], record['page'], record['text'], metadata))
        seen.add(key)
    if sum(p.metadata.get('counted_content_page', False) for p in pages) < 30:
        raise ValueError('Corpus must contain at least 30 counted content pages')
    return pages
