# Retrieval benchmark — dev

| Strategy | Hit@1 | Evidence Hit@3 | Chunks | Ingest (s) |
|---|---|---|---|---|
| A | 6/15 | 7/15 | 222 | 7.553 |
| B | 9/15 | 11/15 | 252 | 6.351 |
| C | 9/15 | 11/15 | 252 | 6.649 |

Exact evidence matching is a proxy; human coherence/grounding/metadata audit is pending.
Local CPU embeddings: paid service cost USD 0; hardware/electricity excluded.
Ingest timing excludes model loading, query embedding and reload verification.
All three strategies are embedded independently; timing varies with warm-up and run order.
Access for free at openstax.org. Source content: OpenStax / Rice University, CC BY-NC-SA 4.0.
