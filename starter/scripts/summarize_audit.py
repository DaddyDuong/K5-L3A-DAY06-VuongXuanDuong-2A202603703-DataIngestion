"""Validate provenance and aggregate explicitly AI-authored qualitative labels.

This script does not assign qualitative scores: those are recorded, with reasons,
in results/audit/review_decisions.json. It never edits frozen gold or raw traces.
"""
import csv
import hashlib
import json
import re
import statistics
import subprocess
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/audit'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def compact(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text).replace('\u00ad', '')).strip()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def csv_save(name, values):
    with (OUT / name).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(values[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(values)


def main():
    review = read(OUT / 'review_decisions.json')
    selection = read(ROOT / 'results/selection.json')
    marker = read(ROOT / 'results/test_started.json')
    dev = ROOT / 'results' / Path(selection['dev_run']).name
    test = ROOT / 'results' / Path(marker['run']).name
    traces = rows(test / 'traces.jsonl')
    assert len(traces) == 15 and all(t['split'] == 'test' for t in traces)
    assert read(test / 'run_metadata.json')['fingerprints'] == selection['fingerprints']
    assert marker['selection'] == selection, 'Selection changed after opening test'
    assert (test/'chunks_B.jsonl').read_bytes() == (test/'chunks_C.jsonl').read_bytes()
    by_case = {(t['strategy'], t['question_id']):t for t in traces}
    for qid in [f'q{n}' for n in range(16,21)]:
        key = lambda h: (h['chunk_id'], h['text'], h['page'], h['metadata'])
        assert list(map(key, by_case['B',qid]['hits'])) == list(map(key, by_case['C',qid]['hits']))
    source = {p['page']:p for p in rows(ROOT/'data/processed/pages.jsonl')}
    manifest = read(ROOT/'data/manifest.json')
    pdf = ROOT/manifest['local_path']
    raw_pages = {}
    metadata_labels, grounding_labels = [], []
    for trace in traces:
        strategy, qid = trace['strategy'], trace['question_id']
        decision = review['grounding_decisions']['B' if strategy=='C' else strategy][qid]
        assert decision['score'] in (0,1,2) and decision['reason']
        reviewed_hits = []
        for hit in trace['hits']:
            number, text = hit['page'], hit['text']
            page, meta = source[number], hit['metadata']
            if number not in raw_pages:
                raw_pages[number] = subprocess.check_output(
                    ['pdftotext','-f',str(number),'-l',str(number),'-layout',str(pdf),'-'],encoding='utf-8')
            raw = raw_pages[number]
            expected_text = page['text'][meta['start_char']:meta['end_char']]
            checks = {
                'document_id_correct': hit['document_id']==page['document_id']==meta['document_id'],
                'source_correct': hit['source']==page['source']==meta['source'] and (ROOT/hit['source']).is_file(),
                'pdf_page_correct': number==meta['page'] and str(number-10) in raw.splitlines()[0],
                'printed_page_correct': meta['printed_page']==page['printed_page']==number-10,
                'chapter_correct': meta['chapter']==page['metadata']['chapter'] and bool(re.search(r'\b'+str(meta['chapter'])+r'(?:\.\d|\s*•)',raw)),
                'source_slice_correct': text==expected_text,
                'source_pdf_text_present': compact(text) in compact(raw),
                'attribution_present': meta.get('attribution')=='Access for free at openstax.org.',
            }
            complete = all(checks.values())
            metadata_labels.append({'strategy':strategy,'question_id':qid,'rank':hit['rank'],
                'chunk_id':hit['chunk_id'],'pdf_page':number,**checks,'metadata_complete_correct':complete,
                'requested_chapter':trace['requested_filter'].get('chapter',''),
                'applied_chapter':trace['applied_filter'].get('chapter',''),
                'requested_filter_satisfied':all(meta.get(k)==v for k,v in trace['requested_filter'].items()),
                'reviewer_type':review['reviewer_type']+' + deterministic source checks','human_review_status':review['human_review_status']})
            overrides = [o for o in review['semantic_overrides']
                         if (o['strategy'],o['question_id'],o['rank']) == (strategy,qid,hit['rank'])]
            for override in overrides:
                assert override['chunk_id']==hit['chunk_id'] and override['source_page']==number
                assert compact(override['evidence_quote']) in compact(text)
                assert complete, 'Semantic override requires valid source provenance'
            reviewed_hits.append({'rank':hit['rank'],'chunk_id':hit['chunk_id'],
                'strict_evidence_hit':hit['evidence_hit'],
                'ai_reviewed_evidence_hit':hit['evidence_hit'] or bool(overrides),
                'semantic_overrides':overrides})
        grounding_labels.append({'strategy':strategy,'question_id':qid,'grounding_score':decision['score'],
            'reason':decision['reason'],'reviewer':review['reviewer'],'reviewer_type':review['reviewer_type'],
            'human_review_status':review['human_review_status'],'strict_hit1':trace['hit1'],'strict_hit3':trace['hit3'],
            'ai_reviewed_hit1':reviewed_hits[0]['ai_reviewed_evidence_hit'],
            'ai_reviewed_hit3':any(h['ai_reviewed_evidence_hit'] for h in reviewed_hits),
            'per_hit_evidence':reviewed_hits,
            'requested_filter_compliant':None if not trace['requested_filter'] else all(
                all(h['metadata'].get(k)==v for k,v in trace['requested_filter'].items()) for h in trace['hits'])})
    coherence_labels=[]
    samples=rows(test/'coherence_samples.jsonl')
    assert len(samples)==30
    assert {(s['chunk']['page'],s['position']) for s in samples} == {(p,0) for p in range(319,329)}
    for sample in samples:
        strategy, chunk=sample['strategy'],sample['chunk']
        decision=review['coherence_decisions']['B' if strategy=='C' else strategy][str(chunk['page'])]
        assert decision['score'] in (0,1,2) and decision['reason']
        original=source[chunk['page']]['text']
        assert original[chunk['metadata']['start_char']:chunk['metadata']['end_char']]==chunk['text']
        coherence_labels.append({**sample,'coherence_score':decision['score'],'reason':decision['reason'],
            'rater':review['reviewer'],'reviewer_type':review['reviewer_type'],'human_review_status':review['human_review_status']})
    summary={'reviewer':review['reviewer'],'reviewer_type':review['reviewer_type'],'human_review_status':review['human_review_status'],
             'method':review['method'],'dev_run':dev.name,'test_run':test.name,
             'selected_strategy_before_test':selection['selected_strategy'],'strategies':{}}
    for strategy in ('A','B','C'):
        coherence=[s for s in coherence_labels if s['strategy']==strategy]
        ground=[s for s in grounding_labels if s['strategy']==strategy]
        metadata=[s for s in metadata_labels if s['strategy']==strategy]
        filtered=[s for s in ground if s['requested_filter_compliant'] is not None]
        counts=Counter(s['grounding_score'] for s in ground)
        summary['strategies'][strategy]={
            'coherence_n':len(coherence),'coherence_sum':sum(s['coherence_score'] for s in coherence),
            'coherence_mean':statistics.mean(s['coherence_score'] for s in coherence),
            'metadata_correct_n':sum(s['metadata_complete_correct'] for s in metadata),'metadata_n':len(metadata),
            'filter_compliant_n':sum(s['requested_filter_compliant'] for s in filtered),'filter_question_n':len(filtered),
            'grounding_counts':{str(k):counts[k] for k in range(3)},'grounding_mean':statistics.mean(s['grounding_score'] for s in ground),
            'strict_hit1_n':sum(s['strict_hit1'] for s in ground),'strict_hit3_n':sum(s['strict_hit3'] for s in ground),
            'ai_reviewed_hit1_n':sum(s['ai_reviewed_hit1'] for s in ground),
            'ai_reviewed_hit3_n':sum(s['ai_reviewed_hit3'] for s in ground),'test_questions':len(ground)}
    assert len(metadata_labels)==45 and all(s['metadata_complete_correct'] for s in metadata_labels)
    csv_save('metadata_labels.csv',metadata_labels)
    for filename,values in [('coherence_labels.jsonl',coherence_labels),('grounding_labels.jsonl',grounding_labels)]:
        (OUT/filename).write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in values),encoding='utf-8')
    save('summary.json',summary)
    inputs=[OUT/'review_decisions.json',test/'traces.jsonl',test/'coherence_samples.jsonl',ROOT/'results/selection.json']
    save('provenance.json',{'created_at':datetime.now(timezone.utc).isoformat(),
         'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
         'gold_and_raw_trace_modified':False,'pdf_text_pages_verified':sorted(raw_pages),
         'visually_reviewed_pdf_pages':[324,336,337,357,361],
         'reviewer_type':review['reviewer_type'],'human_review_status':review['human_review_status']})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
