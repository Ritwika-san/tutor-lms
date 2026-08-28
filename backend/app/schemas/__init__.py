from app.schemas.user import (
    ErrorResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from app.schemas.lms import (
    AssignmentCreate,
    AssignmentResponse,
    CourseCreate,
    CourseResponse,
    EnrolledStudent,
    GradeSubmission,
    MaterialResponse,
    SubmissionResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "ErrorResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "CourseCreate",
    "CourseResponse",
    "AssignmentCreate",
    "AssignmentResponse",
    "SubmissionResponse",
    "GradeSubmission",
    "MaterialResponse",
    "EnrolledStudent",
]
