from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


CHROMA_PATH = Path(".skillsetu_chroma")
COLLECTION_NAME = "myscheme_schemes"

_embedding_model = None
_chroma_client = None
_collection = None


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def _get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    return _embedding_model


def _get_collection():
    global _chroma_client
    global _collection

    if _collection is None:
        import chromadb

        CHROMA_PATH.mkdir(parents=True, exist_ok=True)

        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "description": "SkillSetu live myScheme RAG index"
            },
        )

    return _collection


def _scheme_to_text(scheme: dict[str, Any]) -> str:
    fields = [
        ("Scheme", scheme.get("scheme_name")),
        ("Description", scheme.get("description")),
        ("Eligibility", scheme.get("eligibility_signals")),
        ("Benefits", scheme.get("benefits")),
        ("Application", scheme.get("application_info")),
    ]

    parts = []

    for label, value in fields:
        value = _clean_text(value)

        if value:
            parts.append(f"{label}: {value}")

    return "\n".join(parts)


def _chunk_text(
    text: str,
    chunk_size: int = 900,
    overlap: int = 120,
) -> list[str]:
    text = _clean_text(text)

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def _make_id(
    scheme: dict[str, Any],
    chunk_index: int,
) -> str:
    raw = (
        f"{scheme.get('url', '')}|"
        f"{scheme.get('scheme_name', '')}|"
        f"{chunk_index}"
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def index_schemes(
    schemes: list[dict[str, Any]],
) -> int:
    """
    Add normalized live scheme documents to ChromaDB.

    Returns number of indexed chunks.
    """
    if not schemes:
        return 0

    model = _get_embedding_model()
    collection = _get_collection()

    documents = []
    ids = []
    metadatas = []

    for scheme in schemes:
        text = _scheme_to_text(scheme)

        chunks = _chunk_text(text)

        for index, chunk in enumerate(chunks):
            metadata = {
                "source": _clean_text(
                    scheme.get("source")
                ) or "myScheme",
                "url": _clean_text(
                    scheme.get("url")
                ),
                "scheme_name": _clean_text(
                    scheme.get("scheme_name")
                ),
                "state": _clean_text(
                    scheme.get("state")
                ),
                "category": _clean_text(
                    scheme.get("category")
                ),
                "fetched_at": _clean_text(
                    scheme.get("fetched_at")
                ),
            }

            documents.append(chunk)
            ids.append(_make_id(scheme, index))
            metadatas.append(metadata)

    if not documents:
        return 0

    embeddings = model.encode(
        documents,
        normalize_embeddings=True,
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(documents)


def retrieve_schemes(
    query: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Retrieve source-grounded scheme chunks.

    Every result preserves the source metadata required by Phase 5.
    """
    query = _clean_text(query)

    if not query:
        return []

    try:
        collection = _get_collection()
        model = _get_embedding_model()

        if collection.count() == 0:
            return []

        query_embedding = model.encode(
            [query],
            normalize_embeddings=True,
        ).tolist()

        result = collection.query(
            query_embeddings=query_embedding,
            n_results=max(1, top_k),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        output = []

        for index, document in enumerate(documents):
            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            distance = (
                distances[index]
                if index < len(distances)
                else None
            )

            output.append(
                {
                    "text": document,
                    "source": metadata.get(
                        "source",
                        "myScheme",
                    ),
                    "url": metadata.get("url", ""),
                    "scheme_name": metadata.get(
                        "scheme_name",
                        "",
                    ),
                    "state": metadata.get(
                        "state",
                        "",
                    ),
                    "category": metadata.get(
                        "category",
                        "",
                    ),
                    "fetched_at": metadata.get(
                        "fetched_at",
                        "",
                    ),
                    "distance": distance,
                }
            )

        return output

    except Exception as exc:
        print(f"[RAG] retrieval unavailable: {exc}")
        return []


def fetch_and_index_schemes(
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Convenience function for Person 2:

    profile
      -> live myScheme
      -> normalize
      -> chunk
      -> embeddings
      -> ChromaDB
    """
    from data.schemes import fetch_schemes

    schemes = fetch_schemes(profile)

    if not schemes:
        return []

    index_schemes(schemes)

    return schemes