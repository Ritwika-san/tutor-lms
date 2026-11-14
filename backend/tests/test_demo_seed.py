import secrets

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.main import _start_demo_seed_on_startup
from app.models import Course, CourseMaterial, Enrollment, User
from app.services.demo_seed import seed_demo


def _set_demo_passwords(monkeypatch):
    monkeypatch.setenv("DEMO_TUTOR_PASSWORD", f"Tutor{secrets.token_hex(16)}9!")
    monkeypatch.setenv("DEMO_STUDENT_PASSWORD", f"Student{secrets.token_hex(16)}9!")


def test_demo_seeding_is_disabled_when_environment_is_missing(monkeypatch):
    monkeypatch.delenv("SEED_DEMO_ON_START", raising=False)
    monkeypatch.delenv("DEMO_TUTOR_PASSWORD", raising=False)
    monkeypatch.delenv("DEMO_STUDENT_PASSWORD", raising=False)

    assert _start_demo_seed_on_startup() is False


def test_seed_demo_twice_is_idempotent_and_preserves_passwords(monkeypatch):
    _set_demo_passwords(monkeypatch)

    first_vector_count = seed_demo()
    with SessionLocal() as session:
        first_counts = (
            session.scalar(select(func.count()).select_from(User)),
            session.scalar(select(func.count()).select_from(Course)),
            session.scalar(select(func.count()).select_from(Enrollment)),
            session.scalar(select(func.count()).select_from(CourseMaterial)),
        )
        first_passwords = {
            user.email: user.password_hash
            for user in session.scalars(select(User)).all()
        }

    second_vector_count = seed_demo()
    with SessionLocal() as session:
        second_counts = (
            session.scalar(select(func.count()).select_from(User)),
            session.scalar(select(func.count()).select_from(Course)),
            session.scalar(select(func.count()).select_from(Enrollment)),
            session.scalar(select(func.count()).select_from(CourseMaterial)),
        )
        second_passwords = {
            user.email: user.password_hash
            for user in session.scalars(select(User)).all()
        }

    assert first_counts == (2, 1, 1, 1)
    assert second_counts == first_counts
    assert second_passwords == first_passwords
    assert second_vector_count == first_vector_count


def test_seed_demo_upserts_when_pdf_index_already_exists(monkeypatch):
    _set_demo_passwords(monkeypatch)

    seed_demo()

    assert seed_demo() > 0
