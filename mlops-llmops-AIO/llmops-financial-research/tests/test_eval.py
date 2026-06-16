import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from eval.run_eval import evaluate_record


def test_eval_requires_citation():
    result = evaluate_record({
        "query": "Explain liquidity risk",
        "expected_keywords": ["liquidity", "risk"],
        "requires_citation": True,
    })
    assert result["citation_ok"] is True
    assert result["keyword_hits"] >= 1
