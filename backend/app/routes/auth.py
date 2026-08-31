from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import get_logger
from app.core.security import (
    create_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Invalid input or password does not meet requirements"},
    },
)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Register a new user.

    Validates password strength, checks for duplicate email, and creates user with hashed password.

    Args:
        request: Registration request with email, password, name, and role
        db: Database session

    Returns:
        TokenResponse with JWT access token and user info

    Raises:
        HTTPException(409): Email already registered
        HTTPException(422): Invalid input or weak password
    """
    logger.info("Registration request received for email=%s role=%s", request.email, request.role)

    # Validate password strength
    is_valid, error_message = validate_password_strength(request.password)
    if not is_valid:
        logger.info(f"Registration failed: weak password for email {request.email}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_message,
        )

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        logger.info(f"Registration failed: email {request.email} already registered")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    try:
        hashed_password = hash_password(request.password)
    except ValueError as exc:
        logger.warning("Registration failed for email=%s: %s", request.email, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=hashed_password,
        role=request.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {new_user.email} with role {new_user.role}")

    # Create access token
    access_token = create_access_token(data={"sub": new_user.id})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(new_user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"description": "Invalid email or password"},
        404: {"description": "User not found"},
    },
)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    Args:
        request: Login request with email and password
        db: Database session

    Returns:
        TokenResponse with JWT access token and user info

    Raises:
        HTTPException(401): Invalid credentials
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        logger.warning(f"Login failed: user {request.email} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        logger.warning(f"Login failed: invalid password for user {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    logger.info(f"User {user.email} logged in successfully")

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user's information.

    Args:
        current_user: Current authenticated user (injected via dependency)

    Returns:
        UserResponse with user's info
    """
    return UserResponse.model_validate(current_user)
