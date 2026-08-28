"""Standalone end-to-end smoke test for course-material ingestion."""

import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Course, CourseMaterial, RoleEnum, User  # noqa: E402
from app.services.ingestion import chunk_text, extract_pdf_text, index_material  # noqa: E402

SAMPLE_PARAGRAPHS = [
    "A quadratic equation is an equation that can be written in the form ax^2 + bx + c = 0, where a is not zero. The graph of a quadratic function is a parabola, and its coefficient a controls whether the parabola opens upward or downward.",
    "The quadratic formula, x = (-b +/- sqrt(b^2 - 4ac)) / (2a), gives the solutions of every quadratic equation. The expression b^2 - 4ac is called the discriminant. A positive discriminant gives two real solutions, zero gives one repeated real solution, and a negative discriminant gives two complex solutions.",
    "Students can also solve some quadratic equations by factoring. After writing the equation in standard form, look for two factors whose product is ac and whose sum is b. The zero-product property then allows each factor to be set equal to zero. Checking the solutions in the original equation is a useful final step.",
]


def create_sample_pdf(file_path: Path) -> None:
    document = canvas.Canvas(str(file_path), pagesize=LETTER)
    document.setTitle("Tutor LMS quadratic equations ingestion test")
    text = document.beginText(54, 740)
    text.setFont("Helvetica-Bold", 16)
    text.textLine("Quadratic Equations: A Short Study Note")
    text.setFont("Helvetica", 11)
    text.setLeading(16)
    text.textLine("")
    for paragraph in SAMPLE_PARAGRAPHS:
        for line in _wrap(paragraph, 92):
            text.textLine(line)
        text.textLine("")
    document.drawText(text)
    document.save()


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def get_or_create_tutor(db):
    tutor = db.query(User).filter(User.role == RoleEnum.TUTOR).first()
    if tutor:
        return tutor
    tutor = User(
        name="Ingestion Test Tutor",
        email=f"ingestion-test-{uuid4().hex[:8]}@example.com",
        password_hash="debug-only-not-for-login",
        role=RoleEnum.TUTOR,
    )
    db.add(tutor)
    db.flush()
    return tutor


def main() -> None:
    settings = get_settings()
    print("Tutor LMS material-ingestion smoke test")
    print(f"Chroma path: {settings.chroma_path}")

    # Create all database tables
    Base.metadata.create_all(bind=engine)

    with tempfile.TemporaryDirectory(prefix="tutor-lms-ingestion-") as temp_dir:
        pdf_path = Path(temp_dir) / "quadratic-equations.pdf"
        create_sample_pdf(pdf_path)
        print(f"[1/6] Generated sample PDF: {pdf_path}")

        extracted_text = extract_pdf_text(pdf_path)
        print(f"[2/6] Extracted text: {len(extracted_text)} characters")
        if not extracted_text.strip():
            raise RuntimeError("PDF extraction returned empty text")

        chunks = chunk_text(extracted_text)
        print(f"[3/6] Created {len(chunks)} chunk(s)")
        for index, chunk in enumerate(chunks, start=1):
            print(f"\n--- Chunk {index} ({len(chunk)} characters) ---\n{chunk}")

        db = SessionLocal()
        try:
            tutor = get_or_create_tutor(db)
            course = Course(
                tutor_id=tutor.id,
                title="Ingestion Test: Quadratic Equations",
                description="Temporary course created by the standalone ingestion test.",
            )
            db.add(course)
            db.flush()
            material = CourseMaterial(course_id=course.id, file_url=str(pdf_path))
            db.add(material)
            db.flush()
            print(f"\n[4/6] Using course_id={course.id}, material_id={material.id}")

            stats = index_material(course.id, material.id, extracted_text)
            print(f"[5/6] Embeddings generated: {stats['embedding_count']} vector(s)")
            print(f"      Stored in ChromaDB: {stats['stored_count']} document(s)")
            db.rollback()

            import chromadb

            collection = chromadb.PersistentClient(path=settings.chroma_path).get_collection("course_materials")
            ids = [f"course-{course.id}-material-{material.id}-{index}" for index in range(stats["chunk_count"])]
            stored = collection.get(ids=ids, include=["documents", "metadatas"])
            print(f"[6/6] ChromaDB read-back: {len(stored['ids'])} document(s) found")
            if len(stored["ids"]) != stats["stored_count"]:
                raise RuntimeError("ChromaDB read-back count did not match stored count")
            print("SUCCESS: PDF ingestion completed end to end.")
        finally:
            db.close()


if __name__ == "__main__":
    main()
