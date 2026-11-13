"""Persistent PostgreSQL/pgvector with exact cosine search and typed filters."""
import math
from typing import Any
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        if type(dimensions) is not int or not 1 <= dimensions <= 16000:
            raise ValueError('Invalid vector dimensions')
        self.dimensions = dimensions
        self.connection = psycopg.connect(database_url, connect_timeout=5, autocommit=True,
                                           row_factory=dict_row)

    def close(self) -> None:
        self.connection.close()

    def create_schema(self) -> None:
        with self.connection.transaction(), self.connection.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
            cur.execute('CREATE SCHEMA IF NOT EXISTS day6_ingestion')
            cur.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS day6_ingestion.chunks (
                strategy text NOT NULL, chunk_id text NOT NULL, document_id text NOT NULL,
                source text NOT NULL, page integer NOT NULL CHECK (page > 0), text text NOT NULL,
                metadata jsonb NOT NULL, embedding vector({}) NOT NULL,
                PRIMARY KEY (strategy, chunk_id))''').format(sql.SQL(str(self.dimensions))))
            cur.execute("""SELECT format_type(atttypid, atttypmod) AS type FROM pg_attribute
                WHERE attrelid='day6_ingestion.chunks'::regclass AND attname='embedding'""")
            if cur.fetchone()['type'] != f'vector({self.dimensions})':
                raise ValueError('Existing vector dimension differs; use a separate database')

    def _vector(self, vector: list[float]) -> str:
        if len(vector) != self.dimensions or not all(math.isfinite(x) for x in vector):
            raise ValueError('Invalid embedding dimensions or non-finite value')
        if not any(x != 0 for x in vector):
            raise ValueError('Zero vector cannot be ranked by cosine distance')
        return '[' + ','.join(str(float(x)) for x in vector) + ']'

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Atomically replace this strategy's COMPLETE corpus snapshot.

        Remove stale chunks and deleted documents. Leave other strategies intact.
        """
        if not strategy or len(chunks) != len(vectors):
            raise ValueError('Strategy required and one embedding per chunk expected')
        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError('Duplicate chunk IDs in snapshot')
        rows = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            if not chunk.text.strip() or chunk.page < 1:
                raise ValueError('Invalid chunk')
            metadata = {**chunk.metadata, 'document_id': chunk.document_id,
                        'source': chunk.source, 'page': chunk.page}
            rows.append((strategy, chunk.chunk_id, chunk.document_id, chunk.source,
                         chunk.page, chunk.text, Jsonb(metadata), self._vector(vector)))
        with self.connection.transaction(), self.connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'day6:{strategy}',))
            cur.execute('DELETE FROM day6_ingestion.chunks WHERE strategy=%s', (strategy,))
            cur.executemany('''INSERT INTO day6_ingestion.chunks
                (strategy,chunk_id,document_id,source,page,text,metadata,embedding)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s::vector)''', rows)

    def count(self, strategy: str) -> int:
        return self.connection.execute(
            'SELECT count(*) AS n FROM day6_ingestion.chunks WHERE strategy=%s', (strategy,)
        ).fetchone()['n']

    def versions(self) -> dict[str, str]:
        return self.connection.execute("""SELECT current_setting('server_version') AS postgres,
            extversion AS pgvector FROM pg_extension WHERE extname='vector'""").fetchone()

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if type(top_k) is not int or top_k < 1:
            raise ValueError('top_k must be a positive integer')
        filters = filters or {}
        for field, value in filters.items():
            if field not in {'chapter', 'language'}:
                raise ValueError(f'Unsupported metadata filter: {field}')
            if field == 'chapter' and type(value) is not int:
                raise ValueError('chapter filter must be an integer')
            if field == 'language' and not isinstance(value, str):
                raise ValueError('language filter must be a string')
        vector = self._vector(query_vector)
        # No ANN index: filter first, then rank the eligible rows exactly.
        return self.connection.execute('''SELECT chunk_id,document_id,source,page,text,
                metadata,1-(embedding <=> %s::vector) AS score
            FROM day6_ingestion.chunks WHERE strategy=%s AND metadata @> %s
            ORDER BY embedding <=> %s::vector, chunk_id LIMIT %s''',
            (vector, strategy, Jsonb(filters), vector, top_k)).fetchall()
