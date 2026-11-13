"""Ingest a frozen corpus, run dev by default, and retain reproducible traces."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import statistics
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pages
from .store import PgVectorStore

ROOT = Path(__file__).resolve().parents[2]
STARTER = ROOT / 'starter'


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(path: Path, values) -> None:
    path.write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in values), encoding='utf-8')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(config_path: Path) -> dict:
    return {
        'config_sha256': sha(config_path),
        'questions_sha256': sha(ROOT / 'benchmark/questions.jsonl'),
        'pages_sha256': sha(ROOT / 'data/processed/pages.jsonl'),
        'source_code_sha256': hashlib.sha256(b''.join(
            p.name.encode() + p.read_bytes() for p in sorted((STARTER / 'src').glob('*.py'))
        )).hexdigest(),
    }


def update_experiment_log(config: dict, summary: dict, run_path: Path) -> None:
    path = ROOT / 'artifacts/experiment_log.csv'
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        existing = [row for row in reader if any(value for key, value in row.items() if key != 'strategy')]
    hypotheses = {
        'A': 'Fixed character windows provide a simple baseline; overlap may preserve boundary evidence.',
        'B': 'Paragraph boundaries may improve coherence; large paragraphs still require splitting.',
        'C': 'Chapter filters may improve scoped retrieval; identical chunks to B.',
    }
    for row in summary['metrics']:
        strategy = row['strategy']
        spec = config['strategies'][strategy]
        record = {key: '' for key in fields}
        record.update(strategy=strategy, chunking=spec['chunking'], chunk_size=spec['chunk_size'],
                      overlap=spec['overlap'], metadata='document_id/source/page/chapter/language/offsets',
                      filter='chapter when requested' if spec['use_filter'] else 'none',
                      vectorizer=config['model'] + '@' + config['model_revision'],
                      hypothesis=hypotheses[strategy], notes=str(run_path))
        record[row['split'] + '_hit1'] = row['hit1']
        record[row['split'] + '_hit3'] = row['hit3']
        existing.append(record)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(existing)


def execute(args, run_path: Path) -> None:
    load_dotenv(STARTER / '.env')
    url = os.getenv('DATABASE_URL')
    if not url:
        raise ValueError('DATABASE_URL missing; copy starter/.env.example to starter/.env')
    config = json.loads(args.config.read_text())
    if config['device'] != 'cpu' or config['metric'] != 'cosine' or config['search'] != 'exact':
        raise ValueError('This implementation supports CPU embeddings and exact cosine search')
    if config['top_k'] != 3 or set(config['strategies']) != {'A', 'B', 'C'}:
        raise ValueError('Benchmark requires A/B/C and top_k=3')
    b, c = config['strategies']['B'], config['strategies']['C']
    if {k: v for k, v in b.items() if k != 'use_filter'} != {k: v for k, v in c.items() if k != 'use_filter'}:
        raise ValueError('B and C must differ only in metadata filtering')
    subprocess.run([sys.executable, str(STARTER / 'scripts/check_benchmark.py')], check=True)
    signature = fingerprints(args.config)
    selection_path = args.output_root / 'selection.json'
    if args.split == 'test':
        if not selection_path.exists():
            raise ValueError('Run dev and freeze a selection before running test')
        selection = json.loads(selection_path.read_text())
        if selection['fingerprints'] != signature:
            raise ValueError('Configuration/code/data changed after selection; test run refused')
        write_json(args.output_root / 'test_started.json', {'run': str(run_path), 'selection': selection})
    elif (args.output_root / 'test_started.json').exists():
        raise ValueError('Test has already been opened; use a new, documented experiment for further tuning')
    pages = load_pages(ROOT / 'data/processed/pages.jsonl')
    questions = [q for q in map(json.loads, (ROOT / 'benchmark/questions.jsonl').read_text().splitlines())
                 if q['split'] == args.split]
    metadata = {
        'started_at': datetime.now(timezone.utc).isoformat(), 'split': args.split,
        'config': config, 'fingerprints': signature, 'python': platform.python_version(),
        'packages': {name: importlib.metadata.version(name) for name in
                     ('torch', 'sentence-transformers', 'transformers', 'psycopg', 'pypdf', 'numpy')},
        'corpus_pages': len(pages), 'counted_content_pages': sum(p.metadata['counted_content_page'] for p in pages),
        'embedding_provider': 'local CPU; no remote inference API',
        'paid_service_cost_usd': 0, 'cost_note': 'Excludes electricity, hardware, network and labor',
        'selection_rule': json.loads((ROOT / 'benchmark/benchmark_lock.json').read_text())['selection_rule'],
        'embedding_prefixes': {'document': 'passage: ', 'query': 'query: '},
    }
    started = perf_counter()
    logging.info('Loading real model %s, revision %s', config['model'], config['model_revision'])
    embedder = MyEmbedder(config['model'], config['model_revision'], config['batch_size'], config['threads'])
    metadata['model_load_seconds'] = perf_counter() - started
    if embedder.dimensions != config['dimensions']:
        raise ValueError('Model dimension differs from config')
    store = PgVectorStore(url, embedder.dimensions)
    traces, samples, ingestion = [], [], {}
    try:
        store.create_schema()
        metadata['database_versions'] = store.versions()
        metadata['model_max_tokens'] = embedder.max_tokens
        query_vectors = {}
        query_start = perf_counter()
        for question in questions:
            # Only question text is embedded. Gold is used after retrieval.
            query_vectors[question['id']] = embedder.embed_query(question['question'])
        metadata['query_embedding_seconds'] = perf_counter() - query_start
        paragraph_ids = None
        for strategy, spec in config['strategies'].items():
            logging.info('Ingesting strategy %s', strategy)
            start = perf_counter()
            chunks = []
            for page in pages:
                if spec['chunking'] == 'fixed':
                    chunks.extend(fixed_size(page, spec['chunk_size'], spec['overlap']))
                elif spec['chunking'] == 'paragraph':
                    chunks.extend(by_paragraph(page, spec['chunk_size']))
                else:
                    raise ValueError('Unknown chunking method')
            chunking_seconds = perf_counter() - start
            if strategy == 'B':
                paragraph_ids = [chunk.chunk_id for chunk in chunks]
            if strategy == 'C' and paragraph_ids != [chunk.chunk_id for chunk in chunks]:
                raise ValueError('B/C chunks are not identical')
            embedded_at = perf_counter()
            vectors = embedder.embed_documents([chunk.text for chunk in chunks])
            embedding_seconds = perf_counter() - embedded_at
            token_counts = list(embedder.last_token_counts)
            written_at = perf_counter()
            store.upsert(strategy, chunks, vectors)
            write_seconds = perf_counter() - written_at
            ingest_seconds = perf_counter() - start
            first_count = store.count(strategy)
            reload_started = perf_counter()
            store.upsert(strategy, chunks, vectors)
            reloaded_count = store.count(strategy)
            if first_count != len(chunks) or reloaded_count != first_count:
                raise ValueError('Re-ingestion introduced missing or duplicate chunks')
            lengths = [len(chunk.text) for chunk in chunks]
            ingestion[strategy] = {
                'chunks': len(chunks), 'length_min': min(lengths),
                'length_median': statistics.median(lengths), 'length_max': max(lengths),
                'length_mean': statistics.mean(lengths),
                'total_characters': sum(lengths), 'document_tokens_including_prefix': sum(token_counts),
                'max_document_tokens': max(token_counts), 'chunking_seconds': chunking_seconds,
                'embedding_seconds': embedding_seconds, 'store_write_seconds': write_seconds,
                'ingest_seconds': ingest_seconds, 'reload_count': reloaded_count,
                'reload_seconds': perf_counter() - reload_started,
                'paid_service_cost_usd': 0,
            }
            write_jsonl(run_path / f'chunks_{strategy}.jsonl', (asdict(chunk) for chunk in chunks))
            for page in pages[:10]:
                for chunk in chunks:
                    if (chunk.document_id, chunk.page) == (page.document_id, page.page) and chunk.metadata['start_char'] == 0:
                        samples.append({'strategy': strategy, 'page_id': page.metadata['page_id'],
                                        'position': 0, 'chunk': asdict(chunk),
                                        'coherence_score': None, 'reason': '', 'rater': ''})
            for question in questions:
                applied_filter = question['filter'] if spec['use_filter'] else {}
                searched_at = perf_counter()
                hits = store.search(strategy, query_vectors[question['id']], 3, applied_filter)
                search_seconds = perf_counter() - searched_at
                if applied_filter and any(any(h['metadata'].get(k) != v for k, v in applied_filter.items()) for h in hits):
                    raise ValueError('Backend violated the requested metadata filter')
                trace = evaluate_query(question, hits)
                trace.update(strategy=strategy, applied_filter=applied_filter,
                             search_seconds=search_seconds)
                traces.append(trace)
            logging.info('Strategy %s: %d chunks, reload count %d', strategy, len(chunks), reloaded_count)
    finally:
        store.close()
    # Reconnect to verify the database retains the ingested snapshots.
    reopened = PgVectorStore(url, config['dimensions'])
    try:
        persisted = {s: reopened.count(s) for s in config['strategies']}
        if persisted != {s: row['chunks'] for s, row in ingestion.items()}:
            raise ValueError('Persistence check failed after reopening connection')
    finally:
        reopened.close()
    metadata['persisted_counts_after_reconnect'] = persisted
    summary = summarize(traces)
    summary['ingestion'] = ingestion
    write_json(run_path / 'run_metadata.json', metadata)
    write_json(run_path / 'summary.json', summary)
    write_jsonl(run_path / 'traces.jsonl', traces)
    write_jsonl(run_path / 'coherence_samples.jsonl', samples)
    if args.split == 'test':
        write_jsonl(run_path / 'human_audit_samples.jsonl', (
            {'strategy': t['strategy'], 'question_id': t['question_id'],
             'hits': t['hits'], 'requested_filter': t['requested_filter'],
             'applied_filter': t['applied_filter'], 'grounding_score': None,
             'metadata_labels_per_hit': [], 'filter_compliant': None, 'reason': '', 'rater': ''}
            for t in traces
        ))
    else:
        ranked = sorted(summary['metrics'], key=lambda r: (
            -r['hit3'], -r['hit1'], ingestion[r['strategy']]['ingest_seconds'], r['strategy']))
        selection = {'selected_strategy': ranked[0]['strategy'], 'fingerprints': signature,
                     'dev_run': str(run_path),
                     'selection_rule': metadata['selection_rule'],
                     'selected_at': datetime.now(timezone.utc).isoformat(),
                     'human_audit_status': 'pending; not used in the selection rule'}
        write_json(selection_path, selection)
        write_json(run_path / 'selection.json', selection)
    lines = ['# Retrieval benchmark — ' + args.split, '',
             '| Strategy | Hit@1 | Evidence Hit@3 | Chunks | Ingest (s) |',
             '|---|---|---|---|---|']
    for row in summary['metrics']:
        s, n = row['strategy'], row['questions']
        lines.append(f"| {s} | {row['hit1_n']}/{n} | {row['hit3_n']}/{n} | {ingestion[s]['chunks']} | {ingestion[s]['ingest_seconds']:.3f} |")
    lines += ['', 'Exact evidence matching is a proxy; human coherence/grounding/metadata audit is pending.',
              'Local CPU embeddings: paid service cost USD 0; hardware/electricity excluded.',
              'Ingest timing excludes model loading, query embedding and reload verification.',
              'All three strategies are embedded independently; timing varies with warm-up and run order.',
              'Access for free at openstax.org. Source content: OpenStax / Rice University, CC BY-NC-SA 4.0.', '']
    (run_path / 'summary.md').write_text('\n'.join(lines), encoding='utf-8')
    update_experiment_log(config, summary, run_path)
    logging.info('Completed %s benchmark. Results: %s', args.split, run_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=('dev', 'test'), default='dev')
    parser.add_argument('--config', type=Path, default=STARTER / 'config.json')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    args.config, args.output_root = args.config.resolve(), args.output_root.resolve()
    run_path = args.output_root / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + args.split)
    run_path.mkdir(parents=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.FileHandler(run_path / 'run.log'), logging.StreamHandler()])
    try:
        execute(args, run_path)
    except Exception as error:
        # Do not write connection strings, credentials or environment variables.
        write_json(run_path / 'failure.json', {'error_type': type(error).__name__,
                                               'status': 'failed; no mock fallback'})
        logging.error('Pipeline failed (%s); check the backend, model and inputs.', type(error).__name__)
        raise


if __name__ == '__main__':
    main()
