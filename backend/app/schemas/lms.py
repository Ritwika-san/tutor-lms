from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=10000)


class CourseResponse(CourseCreate):
    id: int
    tutor_id: int
    created_at: datetime
    enrolled_count: int = 0

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=10000)
    due_date: datetime


class AssignmentResponse(AssignmentCreate):
    id: int
    course_id: int

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    file_url: str
    grade: Optional[int] = Field(default=None, ge=0, le=100)
    feedback: Optional[str] = None
    submitted_at: datetime

    class Config:
        from_attributes = True


class GradeSubmission(BaseModel):
    grade: int = Field(..., ge=0, le=100)
    feedback: Optional[str] = Field(default=None, max_length=10000)


class MaterialResponse(BaseModel):
    id: int
    course_id: int
    file_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class EnrolledStudent(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True