import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import ConflictException
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_duplicate_email_raises_conflict():
    mock_db = AsyncMock()
    mock_settings = MagicMock()

    service = AuthService(mock_db, mock_settings)
    service.repo = AsyncMock()
    service.repo.get_by_email.return_value = MagicMock()  # simulate existing user

    with pytest.raises(ConflictException):
        await service.register(RegisterRequest(email="test@example.com", password="password123"))
