"""Query an existing lab index; no gold answers are used."""
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from .embeddings import MyEmbedder
from .run import ROOT, STARTER, fingerprints
from .store import PgVectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question')
    parser.add_argument('--strategy', choices=('A', 'B', 'C'), default='C')
    parser.add_argument('--chapter', choices=(14, 15), type=int)
    args = parser.parse_args()
    if args.chapter is not None and args.strategy != 'C':
        parser.error('Only strategy C applies metadata filters')
    load_dotenv(STARTER / '.env')
    config_path = STARTER / 'config.json'
    config = json.loads(config_path.read_text())
    selection = json.loads((ROOT / 'results/selection.json').read_text())
    if selection['fingerprints'] != fingerprints(config_path):
        raise ValueError('Code/config/corpus changed since ingestion; rebuild the dev index')
    embedder = MyEmbedder(config['model'], config['model_revision'], config['batch_size'], config['threads'])
    store = PgVectorStore(os.environ['DATABASE_URL'], embedder.dimensions)
    try:
        if not store.count(args.strategy):
            raise ValueError('Index is empty; run src.run first')
        hits = store.search(args.strategy, embedder.embed_query(args.question), 3,
                            {} if args.chapter is None else {'chapter': args.chapter})
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    finally:
        store.close()


if __name__ == '__main__':
    main()
