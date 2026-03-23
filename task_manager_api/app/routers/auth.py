from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.common import DataResponse
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def register(request: Request, data: UserRegister, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    existing = auth_service.get_user_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed: Email already in use",
        )
    user = auth_service.register_user(data)
    return DataResponse(data=UserResponse.model_validate(user), message="User registered successfully")


@router.post("/login", response_model=DataResponse[TokenResponse])
@limiter.limit("5/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_access_token(subject=user.id)
    return DataResponse(
        data=TokenResponse(access_token=token),
        message="Login successful",
    )


@router.post("/logout", response_model=DataResponse[dict])
def logout(current_user: User = Depends(get_current_user)):
    # JWTs are stateless — invalidation is handled client-side by discarding the token.
    # A token blacklist would be required for server-side invalidation.
    return DataResponse(data={}, message="Logged out successfully")
