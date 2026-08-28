from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError, JWSSignatureError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import get_logger
from app.core.security import decode_access_token
from app.models import User, RoleEnum

logger = get_logger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to validate JWT token and return the current logged-in user.

    **Architecture Reasoning:**
    This is a reusable dependency that extracts the user from a valid JWT token.
    It validates both the token signature (via decode_access_token) and ensures
    the user still exists in the database. By making this a dependency, any route
    can inject `get_current_user` to require authentication, and FastAPI will
    automatically handle missing/invalid tokens with 401 responses.

    Args:
        credentials: HTTP Bearer token from the request header
        db: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException(401): If token is invalid, expired, or user doesn't exist
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError:
        logger.warning("Token verification failed: token expired")
        payload = None
    except JWSSignatureError:
        logger.warning("Token verification failed: signature verification failed")
        payload = None
    except JWTClaimsError:
        logger.warning("Token verification failed: invalid claims")
        payload = None
    except JWTError as error:
        logger.warning("Token verification failed: malformed or invalid token (%s)", error)
        payload = None

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_claim = payload.get("sub")
    if user_id_claim is None:
        logger.warning("Token missing user_id claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_claim)
    except (TypeError, ValueError):
        logger.warning("Token contains malformed user_id claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"User {user_id} from token not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(required_role: RoleEnum):
    """
    Dependency factory to enforce role-based access control.

    **Architecture Reasoning:**
    This higher-order dependency is built on top of `get_current_user` and adds
    an additional authorization layer. It's implemented as a dependency factory
    (a function that returns a dependency function) so it can be parameterized
    with the required role. Routes use it like: `Depends(require_role(RoleEnum.ADMIN))`
    to restrict access to specific roles. This keeps authorization logic DRY and
    centralizes it in one place — changes to role checking don't require touching
    individual route handlers.

    Args:
        required_role: The role required to access the protected resource

    Returns:
        An async function that acts as a FastAPI dependency
    """

    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            logger.warning(
                f"Access denied for user {current_user.id} ({current_user.email}) "
                f"with role {current_user.role} requiring {required_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This resource requires {required_role} role",
            )
        return current_user

    return check_role
