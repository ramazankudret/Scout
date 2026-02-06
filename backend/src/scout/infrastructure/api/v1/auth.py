"""
Authentication API Endpoints
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from pydantic import BaseModel

from scout.core.config import settings
from scout.core.security import create_access_token, get_password_hash, verify_password, ALGORITHM
from scout.infrastructure.database import get_db, User
from scout.infrastructure.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


from uuid import UUID

# Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: str | None = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str | None = None
    full_name: str | None = None
    is_active: bool
    timezone: str | None = None
    locale: str | None = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    timezone: str | None = None
    locale: str | None = None


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[AsyncSession, Depends(get_db)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if user is None:
        raise credentials_exception
    return user


async def require_superuser(current_user: Annotated[User, Depends(get_current_user)]):
    """Require current user to be superuser. Raise 403 otherwise."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser required",
        )
    return current_user


def _is_db_connection_error(exc: BaseException) -> bool:
    """True if the exception is due to DB being unreachable (e.g. PostgreSQL not running)."""
    if isinstance(exc, ConnectionRefusedError):
        return True
    if isinstance(exc, OSError) and getattr(exc, "winerror", None) == 1225:
        return True
    err_msg = str(exc).lower()
    return "1225" in err_msg or "connection refused" in err_msg or "could not connect" in err_msg


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    try:
        repo = UserRepository(db)
        if await repo.get_by_email(user_in.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        if await repo.get_by_username(user_in.username):
            raise HTTPException(status_code=400, detail="Username already taken")
        hashed_password = get_password_hash(user_in.password)
        user = await repo.create(
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            is_active=True,
            is_verified=False,
        )
        return user
    except HTTPException:
        raise
    except Exception as e:
        if _is_db_connection_error(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database_unavailable",
            ) from e
        raise


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """Get access token (Login)"""
    try:
        repo = UserRepository(db)
        user = await repo.get_by_username(form_data.username)
    except Exception as e:
        if _is_db_connection_error(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database_unavailable",
            ) from e
        raise

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user profile"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_users_me(
    body: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user profile"""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.timezone is not None:
        current_user.timezone = body.timezone
    if body.locale is not None:
        current_user.locale = body.locale
    await db.commit()
    await db.refresh(current_user)
    return current_user
