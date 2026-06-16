from retrieval.assembler import RetrievedChunk


def filter_authorized_chunks(chunks: list[RetrievedChunk], user_tags: set[str]) -> list[RetrievedChunk]:
    allowed = []
    for chunk in chunks:
        if set(chunk.acl_tags).issubset(user_tags):
            allowed.append(chunk)
    return allowed
