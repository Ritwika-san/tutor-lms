import os
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import get_logger
from app.dependencies import get_current_user, require_role
from app.models import Assignment, Course, CourseMaterial, Enrollment, RoleEnum, Submission, User
from app.schemas import (
    AssignmentCreate,
    AssignmentResponse,
    CourseCreate,
    CourseResponse,
    EnrolledStudent,
    GradeSubmission,
    MaterialResponse,
    SubmissionResponse,
)
from app.services.ingestion import extract_pdf_text, index_material

router = APIRouter(tags=["lms"])
logger = get_logger(__name__)


def course_or_404(course_id: int, db: Session) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def owned_course(course_id: int, tutor: User, db: Session) -> Course:
    course = course_or_404(course_id, db)
    # A tutor role permits the operation type; ownership limits it to their resource.
    if course.tutor_id != tutor.id:
        logger.warning("Tutor %s attempted to access course %s owned by %s", tutor.id, course_id, course.tutor_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this course")
    return course


def enrolled(course_id: int, student_id: int, db: Session) -> bool:
    return db.query(Enrollment).filter_by(course_id=course_id, student_id=student_id).first() is not None


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(request: CourseCreate, tutor: User = Depends(require_role(RoleEnum.TUTOR)), db: Session = Depends(get_db)):
    course = Course(tutor_id=tutor.id, title=request.title.strip(), description=request.description.strip())
    db.add(course)
    db.commit()
    db.refresh(course)
    logger.info("Tutor %s created course %s", tutor.id, course.id)
    return CourseResponse.model_validate(course).model_copy(update={"enrolled_count": 0})


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Course)
    if current_user.role == RoleEnum.TUTOR:
        query = query.filter(Course.tutor_id == current_user.id)
    elif current_user.role == RoleEnum.STUDENT:
        query = query.outerjoin(Enrollment, (Enrollment.course_id == Course.id) & (Enrollment.student_id == current_user.id)).filter(Enrollment.id.is_(None))
    courses = query.order_by(Course.created_at.desc()).all()
    return [CourseResponse.model_validate(course).model_copy(update={"enrolled_count": len(course.enrollments)}) for course in courses]


@router.get("/courses/enrolled", response_model=List[CourseResponse])
async def list_enrolled_courses(student: User = Depends(require_role(RoleEnum.STUDENT)), db: Session = Depends(get_db)):
    courses = db.query(Course).join(Enrollment).filter(Enrollment.student_id == student.id).order_by(Course.created_at.desc()).all()
    return [CourseResponse.model_validate(course).model_copy(update={"enrolled_count": len(course.enrollments)}) for course in courses]


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = course_or_404(course_id, db)
    return CourseResponse.model_validate(course).model_copy(update={"enrolled_count": len(course.enrollments)})


@router.post("/courses/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll(course_id: int, student: User = Depends(require_role(RoleEnum.STUDENT)), db: Session = Depends(get_db)):
    course_or_404(course_id, db)
    if enrolled(course_id, student.id, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You are already enrolled in this course")
    db.add(Enrollment(course_id=course_id, student_id=student.id))
    db.commit()
    logger.info("Student %s enrolled in course %s", student.id, course_id)
    return {"message": "Enrolled successfully"}


@router.post("/courses/{course_id}/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(course_id: int, request: AssignmentCreate, tutor: User = Depends(require_role(RoleEnum.TUTOR)), db: Session = Depends(get_db)):
    owned_course(course_id, tutor, db)
    assignment = Assignment(course_id=course_id, title=request.title.strip(), description=request.description.strip(), due_date=request.due_date)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/courses/{course_id}/assignments", response_model=List[AssignmentResponse])
async def list_assignments(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = course_or_404(course_id, db)
    if current_user.role == RoleEnum.STUDENT and not enrolled(course.id, current_user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in this course to view assignments")
    if current_user.role == RoleEnum.TUTOR and course.tutor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this course")
    return db.query(Assignment).filter_by(course_id=course_id).order_by(Assignment.due_date).all()


@router.post("/assignments/{assignment_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(assignment_id: int, file_url: str, student: User = Depends(require_role(RoleEnum.STUDENT)), db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter_by(id=assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    if not enrolled(assignment.course_id, student.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be enrolled in the course to submit work")
    submission = Submission(assignment_id=assignment_id, student_id=student.id, file_url=file_url)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.patch("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(submission_id: int, request: GradeSubmission, tutor: User = Depends(require_role(RoleEnum.TUTOR)), db: Session = Depends(get_db)):
    submission = db.query(Submission).filter_by(id=submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    owned_course(submission.assignment.course_id, tutor, db)
    submission.grade = request.grade
    submission.feedback = request.feedback
    db.commit()
    db.refresh(submission)
    logger.info("Tutor %s graded submission %s", tutor.id, submission_id)
    return submission


@router.get("/courses/{course_id}/submissions", response_model=List[SubmissionResponse])
async def list_submissions(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    course = course_or_404(course_id, db)
    if current_user.role == RoleEnum.TUTOR:
        if course.tutor_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this course")
    elif current_user.role == RoleEnum.STUDENT:
        if not enrolled(course_id, current_user.id, db):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be enrolled in this course")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This resource is not available to admins")
    query = db.query(Submission).join(Assignment).filter(Assignment.course_id == course_id)
    if current_user.role == RoleEnum.STUDENT:
        query = query.filter(Submission.student_id == current_user.id)
    return query.order_by(Submission.submitted_at.desc()).all()


@router.get("/courses/{course_id}/students", response_model=List[EnrolledStudent])
async def list_enrolled_students(course_id: int, tutor: User = Depends(require_role(RoleEnum.TUTOR)), db: Session = Depends(get_db)):
    course = owned_course(course_id, tutor, db)
    return [enrollment.student for enrollment in course.enrollments]


@router.post("/courses/{course_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(course_id: int, file: UploadFile = File(...), tutor: User = Depends(require_role(RoleEnum.TUTOR)), db: Session = Depends(get_db)):
    owned_course(course_id, tutor, db)
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only PDF materials are supported")
    upload_dir = Path("uploads") / "materials"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / f"{uuid4()}.pdf"
    contents = await file.read()
    target.write_bytes(contents)
    try:
        text = extract_pdf_text(target)
        material = CourseMaterial(course_id=course_id, file_url=str(target).replace(os.sep, "/"))
        db.add(material)
        db.commit()
        db.refresh(material)
        index_material(course_id, material.id, text)
    except ValueError as error:
        db.rollback()
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except RuntimeError as error:
        db.rollback()
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except Exception as error:
        db.rollback()
        target.unlink(missing_ok=True)
        logger.exception("Material ingestion failed for course %s", course_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Material ingestion failed") from error
    logger.info("Tutor %s uploaded material %s to course %s", tutor.id, material.id, course_id)
    return material