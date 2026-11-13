"""Strict evidence matching; human grounding/coherence labels remain separate."""
import re
from collections import defaultdict
from typing import Any


def canonical(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    golds = [question, *question.get('alternative_gold', [])]
    checked = []
    for rank, hit in enumerate(hits[:3], 1):
        matches = [index for index, gold in enumerate(golds)
                   if hit['document_id'] == gold['gold_source_id']
                   and hit['page'] == gold['gold_page']
                   and canonical(gold['evidence_quote']) in canonical(hit['text'])]
        checked.append({**hit, 'rank': rank, 'evidence_hit': bool(matches),
                        'matched_gold_indices': matches})
    return {
        'question_id': question['id'], 'split': question['split'], 'question': question['question'],
        'requested_filter': question.get('filter', {}),
        'gold': [{key: g[key] for key in ('gold_source_id', 'gold_page', 'evidence_quote')} for g in golds],
        'expected_answer': question['expected_answer'], 'hits': checked,
        'hit1': bool(checked and checked[0]['evidence_hit']),
        'hit3': any(hit['evidence_hit'] for hit in checked), 'human_grounding': None,
        'matching_method': 'same document/page + full evidence substring; whitespace normalized',
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    groups = defaultdict(list)
    for trace in traces:
        groups[(trace['strategy'], trace['split'])].append(trace)
    rows = []
    for (strategy, split), items in sorted(groups.items()):
        n = len(items)
        h1, h3 = sum(t['hit1'] for t in items), sum(t['hit3'] for t in items)
        rows.append({'strategy': strategy, 'split': split, 'questions': n,
                     'hit1_n': h1, 'hit1': h1/n, 'hit3_n': h3, 'hit3': h3/n})
    return {'metrics': rows, 'human_audit_status': 'not_scored'}
