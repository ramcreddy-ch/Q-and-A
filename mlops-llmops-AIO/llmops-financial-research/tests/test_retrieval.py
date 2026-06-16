import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from retrieval.assembler import RetrievedChunk, build_prompt
from retrieval.entitlement import filter_authorized_chunks


def test_build_prompt_includes_top_chunks():
    chunks = [
        RetrievedChunk("doc-1", "risk", 0.9, "Liquidity risk increased.", ["research"]),
        RetrievedChunk("doc-2", "summary", 0.8, "Capital remained strong.", ["research"]),
    ]
    prompt = build_prompt("Summarize risk", chunks)
    assert "QUESTION" in prompt
    assert "doc-1" in prompt


def test_filter_authorized_chunks():
    chunks = [
        RetrievedChunk("doc-1", "risk", 0.9, "Allowed", ["research"]),
        RetrievedChunk("doc-2", "secret", 0.95, "Blocked", ["executive"]),
    ]
    filtered = filter_authorized_chunks(chunks, {"research"})
    assert len(filtered) == 1
    assert filtered[0].doc_id == "doc-1"
