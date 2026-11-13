"""Read-only validation of frozen benchmark, provenance and exact gold quotes."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    question_path = ROOT / "benchmark/questions.jsonl"
    lock = json.loads((ROOT / "benchmark/benchmark_lock.json").read_text())
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    pdf = ROOT / manifest["local_path"]
    pages_path = ROOT / "data/processed/pages.jsonl"
    for path, expected in (
        (question_path, lock["questions_sha256"]),
        (pdf, lock["corpus_pdf_sha256"]),
        (pages_path, lock["pages_jsonl_sha256"]),
    ):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen file changed: {path.relative_to(ROOT)}")
    pages = {p["page"]: p for p in map(json.loads, pages_path.read_text().splitlines())}
    questions = list(map(json.loads, question_path.read_text().splitlines()))
    ids = [q["id"] for q in questions]
    assert len(questions) >= 20 and len(ids) == len(set(ids))
    assert {q["split"] for q in questions} == {"dev", "test"}
    for split, minimum in (("dev", 15), ("test", 5)):
        split_ids = [q["id"] for q in questions if q["split"] == split]
        assert len(split_ids) >= minimum and split_ids == lock[f"{split}_ids"]
    filtered = [q for q in questions if q["filter"]]
    assert len(filtered) >= 3 and any(q["split"] == "test" for q in filtered)
    assert [q["id"] for q in filtered] == lock["filter_ids"]
    checked = 0
    source_pages = {}
    for q in questions:
        assert all(q.get(key) for key in (
            "id", "question", "expected_answer", "gold_source_id",
            "gold_page", "evidence_quote", "attribution",
        ))
        assert q["gold_printed_page"] == q["gold_page"] - 10
        assert set(q["filter"]) <= {"chapter"}
        for gold in [q, *q["alternative_gold"]]:
            number = gold["gold_page"]
            page = pages[number]
            assert gold["gold_source_id"] == page["document_id"]
            assert gold["evidence_quote"] in page["text"], (q["id"], number)
            if q["filter"]:
                assert type(q["filter"]["chapter"]) is int
                assert q["filter"]["chapter"] == page["metadata"]["chapter"]
            if number not in source_pages:
                source_pages[number] = subprocess.check_output(
                    ["pdftotext", "-f", str(number), "-l", str(number),
                     "-layout", str(pdf), "-"], encoding="utf-8"
                )
            assert compact(gold["evidence_quote"]) in compact(source_pages[number]), (q["id"], number)
            checked += 1
    print(f"Benchmark OK: {len(questions)} questions, 15 dev / 5 test, {len(filtered)} filters.")
    print(f"Verified {checked} primary/alternative quotes in processed text and source PDF text layer.")
    print("Frozen benchmark/corpus checksums match. No retrieval experiment was run.")


if __name__ == "__main__":
    main()
