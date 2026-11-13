from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password, validate_password_strength
from app.models import Course, CourseMaterial, Enrollment, RoleEnum, User
from app.services.ingestion import extract_pdf_text, index_material

DEMO_TUTOR_EMAIL = "demo-tutor@example.com"
DEMO_STUDENT_EMAIL = "demo-student@example.com"
DEMO_COURSE_TITLE = "Demo: Newton's Laws"
DEMO_COURSE_DESCRIPTION = "A short introduction to Newton's laws of motion."
DEMO_PDF = BACKEND_DIR / "demo_data" / "newton_laws.pdf"
DEMO_FILE_URL = "demo_data/newton_laws.pdf"


def get_or_create_user(
    session,
    email: str,
    name: str,
    role: RoleEnum,
    password_env: str,
) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user:
        if user.role != role:
            raise RuntimeError(f"Existing demo account has an unexpected role: {email}")
        return user

    password = os.getenv(password_env)
    if not password:
        raise RuntimeError(f"{password_env} is required to create its demo account")
    is_valid, error = validate_password_strength(password)
    if not is_valid:
        raise RuntimeError(f"{password_env} is invalid: {error}")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    session.add(user)
    session.flush()
    return user


def get_or_create_course(session, tutor_id: int) -> Course:
    courses = session.scalars(
        select(Course).where(
            Course.tutor_id == tutor_id,
            Course.title == DEMO_COURSE_TITLE,
        )
    ).all()
    if len(courses) > 1:
        raise RuntimeError("Multiple demo courses already exist for the demo tutor")
    if courses:
        return courses[0]

    course = Course(
        tutor_id=tutor_id,
        title=DEMO_COURSE_TITLE,
        description=DEMO_COURSE_DESCRIPTION,
    )
    session.add(course)
    session.flush()
    return course


def get_or_create_material(session, course_id: int) -> CourseMaterial:
    materials = session.scalars(
        select(CourseMaterial).where(
            CourseMaterial.course_id == course_id,
            CourseMaterial.file_url == DEMO_FILE_URL,
        )
    ).all()
    if len(materials) > 1:
        raise RuntimeError("Multiple demo PDF records already exist for the demo course")
    if materials:
        return materials[0]

    material = CourseMaterial(course_id=course_id, file_url=DEMO_FILE_URL)
    session.add(material)
    session.flush()
    return material


def main() -> None:
    if not DEMO_PDF.is_file():
        raise RuntimeError("The checked-in demo PDF is missing")

    text = extract_pdf_text(DEMO_PDF)
    if not text.strip():
        raise RuntimeError("The demo PDF contains no extractable text")

    engine.echo = False
    Base.metadata.create_all(bind=engine)
    with SessionLocal.begin() as session:
        tutor = get_or_create_user(
            session,
            DEMO_TUTOR_EMAIL,
            "Demo Tutor",
            RoleEnum.TUTOR,
            "DEMO_TUTOR_PASSWORD",
        )
        student = get_or_create_user(
            session,
            DEMO_STUDENT_EMAIL,
            "Demo Student",
            RoleEnum.STUDENT,
            "DEMO_STUDENT_PASSWORD",
        )
        course = get_or_create_course(session, tutor.id)
        enrollment = session.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student.id,
                Enrollment.course_id == course.id,
            )
        )
        if enrollment is None:
            session.add(Enrollment(student_id=student.id, course_id=course.id))
        material = get_or_create_material(session, course.id)
        course_id = course.id
        material_id = material.id

    stats = index_material(course_id, material_id, text)
    print(
        "Demo seed complete: users=2, courses=1, enrollments=1, "
        f"materials=1, vectors={stats['stored_count']}."
    )


if __name__ == "__main__":
    main()
