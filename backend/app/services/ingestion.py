from pathlib import Path
from typing import TypedDict

from app.core.config import get_settings


class IngestionStats(TypedDict):
    text_length: int
    chunk_count: int
    embedding_count: int
    stored_count: int


def extract_pdf_text(file_path: str | Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("RAG dependencies are not installed") from error
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(file_path)).pages)


def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    return [
        text[index:index + chunk_size]
        for index in range(0, len(text), chunk_size)
        if text[index:index + chunk_size].strip()
    ]


def index_material(course_id: int, material_id: int, text: str) -> IngestionStats:
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise RuntimeError("RAG dependencies are not installed") from error

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("The uploaded PDF contains no extractable text")
    client = chromadb.PersistentClient(path=get_settings().chroma_path)
    collection = client.get_or_create_collection("course_materials")
    embeddings = SentenceTransformer("all-MiniLM-L6-v2").encode(chunks).tolist()
    ids = [f"course-{course_id}-material-{material_id}-{index}" for index in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"course_id": course_id, "material_id": material_id} for _ in chunks],
    )
    return {
        "text_length": len(text),
        "chunk_count": len(chunks),
        "embedding_count": len(embeddings),
        "stored_count": len(ids),
    }