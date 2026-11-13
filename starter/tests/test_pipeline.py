"""Source fidelity, evidence semantics and optional real-pgvector integration."""
import os
import unittest
import uuid
from pathlib import Path

from dotenv import load_dotenv
from src.chunking import by_paragraph, fixed_size
from src.evaluation import evaluate_query, summarize
from src.ingestion import load_pages, normalize_text
from src.models import Chunk, DocumentPage
from src.store import PgVectorStore

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')


class ChunkingTests(unittest.TestCase):
    def test_all_corpus_characters_trace_to_source(self):
        pages = load_pages(ROOT.parent / 'data/processed/pages.jsonl')
        for page in pages:
            for chunks in (fixed_size(page, 500, 50), by_paragraph(page, 500)):
                covered = set()
                for chunk in chunks:
                    a, b = chunk.metadata['start_char'], chunk.metadata['end_char']
                    self.assertEqual(chunk.text, page.text[a:b])
                    self.assertLessEqual(len(chunk.text), 500)
                    self.assertEqual(chunk.page, page.page)
                    self.assertEqual(chunk.metadata['chapter'], page.metadata['chapter'])
                    self.assertEqual(chunk.metadata['attribution'], page.metadata['attribution'])
                    covered.update(range(a, b))
                self.assertTrue(all(i in covered for i, char in enumerate(page.text) if not char.isspace()))
                self.assertEqual(len(chunks), len({c.chunk_id for c in chunks}))

    def test_paragraphs_and_code_remain_intact_when_they_fit(self):
        page = DocumentPage('d', 's', 1, 'Heading\n\nif flag:\n    print("ok")\n\nNext idea.', {'chapter': 14})
        chunks = by_paragraph(page, 40)
        self.assertTrue(any('if flag:\n    print("ok")' in c.text for c in chunks))
        self.assertEqual(chunks, by_paragraph(page, 40))

    def test_invalid_window_fails_without_looping(self):
        page = DocumentPage('d', 's', 1, 'text')
        for size, overlap in [(0, 0), (10, 10), (10, -1)]:
            with self.assertRaises(ValueError):
                fixed_size(page, size, overlap)
        with self.assertRaises(ValueError):
            by_paragraph(page, 0)

    def test_unicode_and_indentation(self):
        self.assertEqual(normalize_text('e\u0301\r\n    code  \n\n\nnext'), 'é\n    code\n\nnext')


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.q = {'id': 'unit', 'split': 'dev', 'question': 'Q', 'expected_answer': 'A',
                  'gold_source_id': 'd', 'gold_page': 2, 'evidence_quote': 'full evidence here',
                  'alternative_gold': [{'gold_source_id': 'd', 'gold_page': 3,
                                        'evidence_quote': 'another valid proof'}]}

    @staticmethod
    def hit(page, text, document='d'):
        return {'page': page, 'text': text, 'document_id': document}

    def test_right_page_or_partial_quote_is_insufficient(self):
        for hit in [self.hit(2, 'full evidence'), self.hit(1, 'full evidence here'),
                    self.hit(2, 'full evidence here', 'wrong')]:
            self.assertFalse(evaluate_query(self.q, [hit])['hit3'])

    def test_alternative_gold_and_whitespace_are_accepted(self):
        trace = evaluate_query(self.q, [self.hit(1, 'irrelevant'), self.hit(3, 'another\n  valid proof')])
        self.assertFalse(trace['hit1'])
        self.assertTrue(trace['hit3'])
        self.assertEqual(trace['hits'][1]['matched_gold_indices'], [1])
        self.assertIsNone(trace['human_grounding'])

    def test_empty_hits_count_as_miss(self):
        trace = evaluate_query(self.q, [])
        trace['strategy'] = 'A'
        summary = summarize([trace])['metrics'][0]
        self.assertEqual((summary['questions'], summary['hit1_n'], summary['hit3_n']), (1, 0, 0))


@unittest.skipUnless(os.getenv('RUN_DB_TESTS') == '1', 'Set RUN_DB_TESTS=1 for real pgvector tests')
class PgVectorIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.store = PgVectorStore(os.environ['DATABASE_URL'], 384)
        self.store.create_schema()
        self.strategy = 'unit-' + uuid.uuid4().hex
        self.v1, self.v2 = [1.0] + [0.0]*383, [0.0, 1.0] + [0.0]*382
        self.chunks = [Chunk('a', 'd', 's', 1, 'chapter fourteen', {'chapter': 14}),
                       Chunk('b', 'd', 's', 2, 'chapter fifteen', {'chapter': 15})]

    def tearDown(self):
        self.store.upsert(self.strategy, [], [])
        self.store.close()

    def test_cosine_ranking_and_filter_before_topk(self):
        self.store.upsert(self.strategy, self.chunks, [self.v1, self.v2])
        hits = self.store.search(self.strategy, self.v1)
        self.assertEqual(hits[0]['chunk_id'], 'a')
        self.assertAlmostEqual(hits[0]['score'], 1)
        filtered = self.store.search(self.strategy, self.v1, 1, {'chapter': 15})
        self.assertEqual([h['chunk_id'] for h in filtered], ['b'])
        self.assertEqual(filtered[0]['metadata']['page'], 2)
        self.assertEqual(self.store.search(self.strategy, self.v1, 3, {'chapter': 99}), [])

    def test_reingestion_removes_stale_chunks_and_survives_reconnect(self):
        for _ in range(2):
            self.store.upsert(self.strategy, self.chunks, [self.v1, self.v2])
        self.assertEqual(self.store.count(self.strategy), 2)
        self.store.upsert(self.strategy, self.chunks[:1], [self.v1])
        self.assertEqual(self.store.count(self.strategy), 1)
        other = PgVectorStore(os.environ['DATABASE_URL'], 384)
        try:
            self.assertEqual(other.count(self.strategy), 1)
        finally:
            other.close()

    def test_invalid_batch_does_not_destroy_existing_snapshot(self):
        self.store.upsert(self.strategy, self.chunks[:1], [self.v1])
        for vectors in [[self.v1, [float('nan')]*384], [self.v1, [0.0]*384], [self.v1]]:
            with self.assertRaises(ValueError):
                self.store.upsert(self.strategy, self.chunks, vectors)
            self.assertEqual(self.store.count(self.strategy), 1)

    def test_untrusted_filters_rejected(self):
        for filters in [{'chapter': "14 OR 1=1"}, {'chapter': True}, {"x' OR true --": 14}]:
            with self.assertRaises(ValueError):
                self.store.search(self.strategy, self.v1, filters=filters)


if __name__ == '__main__':
    unittest.main()
