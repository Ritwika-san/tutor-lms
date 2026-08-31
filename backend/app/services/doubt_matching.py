from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _get_chroma_client():
    try:
        import chromadb
    except ImportError as error:
        raise RuntimeError("RAG dependencies are not installed") from error

    return chromadb.PersistentClient(path=settings.chroma_path)


def _get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise RuntimeError("RAG dependencies are not installed") from error

    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str):
    model = _get_embedding_model()
    embedding = model.encode(text).tolist()
    logger.info("Embedding generated for text length=%s", len(text))
    return embedding


def _answered_collection_name(course_id: int) -> str:
    return f"course_{course_id}_answered_doubts"


# Checking the answered-doubts collection before course materials is the whole cache win:
# recent student doubts are likely to be repeated, so we resolve the fast in-memory lookup
# first and only fall back to slower material retrieval if no confident match exists.
def search_answered_doubts(course_id: int, doubt_text: str) -> dict[str, Any] | None:
    client = _get_chroma_client()
    collection = client.get_or_create_collection(_answered_collection_name(course_id))
    query_embedding = embed_text(doubt_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=1,
        include=["distances", "documents", "metadatas"],
        where={"course_id": course_id},
    )

    if not results.get("ids") or not results["ids"][0]:
        logger.info("No answered doubts cached for course %s", course_id)
        return None

    scores = results.get("distances", [[]])[0]
    if not scores:
        logger.info("Answered-doubt query returned no distances for course %s", course_id)
        return None

    top_score = 1.0 - float(scores[0])
    logger.info("Answered-doubt match search for course %s produced top similarity=%s", course_id, top_score)
    if top_score < 0.0:
        top_score = 0.0

    if results.get("documents") and results["documents"][0]:
        answer_content = results["metadatas"][0][0].get("answer_content")
        if answer_content:
            return {"similarity": top_score, "answer_content": answer_content}

    return {"similarity": top_score, "answer_content": ""}


def save_answered_doubt(course_id: int, doubt_id: int, student_id: int, answer_id: int, doubt_text: str, answer_content: str) -> None:
    client = _get_chroma_client()
    collection = client.get_or_create_collection(_answered_collection_name(course_id))
    embedding = embed_text(doubt_text)
    collection.add(
        ids=[f"course-{course_id}-doubt-{doubt_id}-answer-{answer_id}"],
        documents=[doubt_text],
        embeddings=[embedding],
        metadatas=[{"course_id": course_id, "student_id": student_id, "doubt_id": doubt_id, "answer_id": answer_id, "answer_content": answer_content}],
    )
    logger.info("Saved answered doubt %s for course %s into Chroma answer cache", doubt_id, course_id)


def search_course_materials(course_id: int, doubt_text: str, limit: int = 5) -> list[str]:
    client = _get_chroma_client()
    collection = client.get_or_create_collection("course_materials")
    query_embedding = embed_text(doubt_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=["documents", "distances"],
        where={"course_id": course_id},
    )

    documents = results.get("documents", [[]])[0]
    logger.info("Course-material query for course %s returned %s chunks", course_id, len(documents))
    return [doc for doc in documents if doc and isinstance(doc, str)]


def generate_answer_from_context(question: str, context_chunks: list[str]) -> str:
    if not context_chunks:
        return "I could not find relevant course material for this question. Please review the course content and ask again."

    context = "\n\n".join(context_chunks)
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY missing; using a local fallback answer without invoking the LLM")
        return (
            "Based on the course materials, the relevant idea is: "
            f"{context[:800]}"
        )

    try:
        import requests
    except ImportError as error:
        raise RuntimeError("HTTP dependencies are not installed") from error

    payload = {
        "model": settings.groq_model,
        "messages": [
            {
                "role": "system",
                "content": "Answer the student's question using only the provided course context. If the context does not contain the answer, say that it is not available in the course materials.",
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{context}",
            },
        ],
        "temperature": 0.2,
        "max_tokens": 512,
    }

    logger.info("Calling Groq model %s for question answer generation", settings.groq_model)
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
