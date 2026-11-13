"""Real CPU multilingual E5 embeddings. No mock fallback."""
from typing import Protocol


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, question: str) -> list[float]: ...


class MyEmbedder:
    def __init__(self, model_name: str, revision: str, batch_size: int = 16, threads: int = 4) -> None:
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(threads)
        self.model_name, self.revision = model_name, revision
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, revision=revision, device='cpu')
        self.dimensions = self.model.get_embedding_dimension()
        self.max_tokens = min(512, self.model.max_seq_length)
        self.model.max_seq_length = self.max_tokens
        self.last_token_counts: list[int] = []

    def _encode(self, texts: list[str], prefix: str) -> list[list[float]]:
        if not texts:
            self.last_token_counts = []
            return []
        inputs = [prefix + text for text in texts]
        counts = [len(ids) for ids in self.model.tokenizer(
            inputs, truncation=False, padding=False, add_special_tokens=True
        )['input_ids']]
        if max(counts) > self.max_tokens:
            raise ValueError(f'Input exceeds {self.max_tokens} tokens; revise chunk size explicitly')
        self.last_token_counts = counts
        return self.model.encode(inputs, batch_size=self.batch_size, normalize_embeddings=True,
                                 show_progress_bar=False, convert_to_numpy=True).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts, 'passage: ')

    def embed_query(self, question: str) -> list[float]:
        return self._encode([question], 'query: ')[0]
