import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.exceptions import ConflictException, NotFoundException, UnauthorizedException
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse

logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession, settings: Settings):
        self.repo = UserRepository(db)
        self.settings = settings

    async def register(self, payload: RegisterRequest) -> UserResponse:
        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise ConflictException(f"Email '{payload.email}' is already registered")

        user = await self.repo.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        logger.info("User registered", user_id=str(user.id))
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_email(email)
        if not user:
            raise NotFoundException("User", email)

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")

        return TokenResponse(
            access_token=create_access_token(str(user.id), self.settings),
            refresh_token=create_refresh_token(str(user.id), self.settings),
        )

    async def get_current_user(self, user_id: str) -> UserResponse:
        user = await self.repo.get_by_id(uuid.UUID(user_id))
        if not user:
            raise UnauthorizedException("User not found")
        return UserResponse.model_validate(user)
