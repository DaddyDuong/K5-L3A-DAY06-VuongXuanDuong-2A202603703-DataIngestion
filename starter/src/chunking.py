"""Character windows and paragraph-aware chunks with exact source offsets."""
import hashlib
import re
from .models import Chunk, DocumentPage


def _chunk(page: DocumentPage, start: int, end: int, method: str) -> Chunk:
    text = page.text[start:end]
    identity = f'{page.document_id}:{page.page}:{method}:{start}:{end}:{text}'
    return Chunk(hashlib.sha256(identity.encode()).hexdigest()[:32],
                 page.document_id, page.source, page.page, text,
                 {**page.metadata, 'start_char': start, 'end_char': end, 'chunking': method})


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError('Require size > 0 and 0 <= overlap < size')
    chunks = []
    for start in range(0, len(page.text), size - overlap):
        end = min(start + size, len(page.text))
        if page.text[start:end].strip():
            chunks.append(_chunk(page, start, end, f'fixed:{size}:{overlap}'))
        if end == len(page.text):
            break
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Prefer paragraph boundaries, then lines/words for oversized paragraphs.

    Slices preserve blank lines and indentation. Never cross page boundaries.
    """
    if max_size <= 0:
        raise ValueError('max_size must be positive')
    chunks, start = [], 0
    boundaries = [match.end() for match in re.finditer(r'\n\s*\n', page.text)]
    boundaries.append(len(page.text))
    while start < len(page.text):
        limit = min(start + max_size, len(page.text))
        possible = [end for end in boundaries if start < end <= limit]
        if possible:
            end = max(possible)
        else:
            end = limit
            if limit < len(page.text):
                lower = start + max_size // 2
                newline = page.text.rfind('\n', lower, limit)
                space = page.text.rfind(' ', lower, limit)
                if newline >= lower:
                    end = newline + 1
                elif space >= lower:
                    end = space + 1
        if page.text[start:end].strip():
            chunks.append(_chunk(page, start, end, f'paragraph:{max_size}'))
        start = end
    return chunks
