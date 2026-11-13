from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, or_, select

from app.core.database import SessionLocal, engine
from app.models import Answer, Assignment, Course, CourseMaterial, Doubt, Enrollment, Submission, User


@dataclass(frozen=True)
class CleanupPlan:
    user_ids: list[int]
    course_ids: list[int]
    assignment_ids: list[int]
    enrollment_ids: list[int]
    submission_ids: list[int]
    doubt_ids: list[int]
    answer_ids: list[int]
    material_ids: list[int]


def select_ids(session, statement) -> list[int]:
    return sorted(set(session.scalars(statement).all()))


def build_plan(session) -> CleanupPlan:
    user_ids = select_ids(
        session,
        select(User.id).where(
            or_(
                User.email.ilike("smoke-tutor-%@example.com"),
                User.email.ilike("smoke-student-%@example.com"),
                User.email.ilike("memory-%@example.com"),
            )
        ),
    )
    course_ids = select_ids(session, select(Course.id).where(Course.tutor_id.in_(user_ids)))
    assignment_ids = select_ids(
        session,
        select(Assignment.id).where(Assignment.course_id.in_(course_ids)),
    )
    enrollment_ids = select_ids(
        session,
        select(Enrollment.id).where(
            or_(
                Enrollment.student_id.in_(user_ids),
                Enrollment.course_id.in_(course_ids),
            )
        ),
    )
    submission_ids = select_ids(
        session,
        select(Submission.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .where(
            or_(
                Submission.student_id.in_(user_ids),
                Assignment.course_id.in_(course_ids),
            )
        ),
    )
    doubt_ids = select_ids(
        session,
        select(Doubt.id).where(
            or_(
                Doubt.student_id.in_(user_ids),
                Doubt.course_id.in_(course_ids),
            )
        ),
    )
    answer_ids = select_ids(session, select(Answer.id).where(Answer.doubt_id.in_(doubt_ids)))
    material_ids = select_ids(
        session,
        select(CourseMaterial.id).where(CourseMaterial.course_id.in_(course_ids)),
    )
    return CleanupPlan(
        user_ids=user_ids,
        course_ids=course_ids,
        assignment_ids=assignment_ids,
        enrollment_ids=enrollment_ids,
        submission_ids=submission_ids,
        doubt_ids=doubt_ids,
        answer_ids=answer_ids,
        material_ids=material_ids,
    )


def print_plan(plan: CleanupPlan, apply: bool) -> None:
    mode = "APPLY" if apply else "DRY RUN (no rows changed)"
    print(mode)
    for label, row_ids in (
        ("users", plan.user_ids),
        ("courses", plan.course_ids),
        ("assignments", plan.assignment_ids),
        ("enrollments", plan.enrollment_ids),
        ("submissions", plan.submission_ids),
        ("doubts", plan.doubt_ids),
        ("answers", plan.answer_ids),
        ("materials", plan.material_ids),
    ):
        print(f"{label}: count={len(row_ids)} ids={row_ids}")


def delete_ids(session, model, row_ids: list[int]) -> None:
    if row_ids:
        session.execute(delete(model).where(model.id.in_(row_ids)))


def run(apply: bool) -> None:
    engine.echo = False
    with SessionLocal() as session:
        if apply:
            with session.begin():
                plan = build_plan(session)
                print_plan(plan, apply=True)
                delete_ids(session, Answer, plan.answer_ids)
                delete_ids(session, Doubt, plan.doubt_ids)
                delete_ids(session, Submission, plan.submission_ids)
                delete_ids(session, CourseMaterial, plan.material_ids)
                delete_ids(session, Enrollment, plan.enrollment_ids)
                delete_ids(session, Assignment, plan.assignment_ids)
                delete_ids(session, Course, plan.course_ids)
                delete_ids(session, User, plan.user_ids)
        else:
            if engine.dialect.name == "postgresql":
                session.connection().exec_driver_sql("SET TRANSACTION READ ONLY")
            elif engine.dialect.name != "sqlite":
                raise RuntimeError("Dry-run read-only mode is unsupported for this database dialect")
            plan = build_plan(session)
            print_plan(plan, apply=False)
            session.rollback()


def main() -> None:
    parser = argparse.ArgumentParser(description="Review or remove explicitly scoped smoke-test rows.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete only the matched users and their related rows; default is read-only.",
    )
    args = parser.parse_args()
    run(apply=args.apply)


if __name__ == "__main__":
    main()
