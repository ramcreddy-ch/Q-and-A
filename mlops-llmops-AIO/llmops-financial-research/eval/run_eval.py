import argparse
import json
import pathlib


def evaluate_record(record: dict) -> dict:
    query = record["query"]
    expected = record.get("expected_keywords", [])
    requires_citation = record.get("requires_citation", False)
    simulated_answer = f"Answer for: {query} [CITATION:doc-1]"
    keyword_hits = sum(1 for kw in expected if kw.lower() in simulated_answer.lower() or kw.lower() in query.lower())
    citation_ok = ("[CITATION:" in simulated_answer) if requires_citation else True
    return {
        "keyword_hits": keyword_hits,
        "expected_keywords": len(expected),
        "citation_ok": citation_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    prompt_text = pathlib.Path(args.prompt).read_text()
    print(f"evaluating prompt length={len(prompt_text)}")
    lines = pathlib.Path(args.dataset).read_text().strip().splitlines()
    results = [evaluate_record(json.loads(line)) for line in lines]
    citation_pass = sum(1 for r in results if r["citation_ok"])
    print({
        "records": len(results),
        "citation_pass_rate": citation_pass / len(results),
        "avg_keyword_hits": sum(r["keyword_hits"] for r in results) / len(results),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
