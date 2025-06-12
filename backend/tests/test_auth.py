import os
from datetime import datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from utils.logging import setup_logger

logger = setup_logger(__name__)


class TestAuth:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_telegram_auth_success(self, client: AsyncClient, mock_telegram_auth):
        """Test successful Telegram authentication."""
        logger.info("Testing successful Telegram auth")

        auth_data = {
            "id": 123456789,
            "first_name": "Test",
            "last_name": "User",
            "username": "test_user",
            "auth_date": int(datetime.utcnow().timestamp()),
            "hash": "mock_hash",
        }

        response = await client.post("/api/auth/telegram-auth", json=auth_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "test_user"

        logger.info("Telegram auth test passed")

    @pytest.mark.asyncio
    async def test_telegram_auth_invalid_hash(self, client: AsyncClient):
        """Test Telegram auth with invalid hash."""
        logger.info("Testing invalid hash scenario")

        auth_data = {
            "id": 123456789,
            "first_name": "Test",
            "last_name": "User",
            "username": "test_user",
            "auth_date": int(datetime.utcnow().timestamp()),
            "hash": "invalid_hash",
        }

        response = await client.post("/api/auth/telegram-auth", json=auth_data)

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication data"

        logger.info("Invalid hash test passed")

    @pytest.mark.asyncio
    async def test_telegram_auth_expired(self, client: AsyncClient, mock_telegram_auth):
        """Test Telegram auth with expired auth_date."""
        logger.info("Testing expired auth scenario")

        # Set auth_date to 2 hours ago
        expired_time = datetime.utcnow() - timedelta(hours=2)

        auth_data = {
            "id": 123456789,
            "first_name": "Test",
            "last_name": "User",
            "username": "test_user",
            "auth_date": int(expired_time.timestamp()),
            "hash": "mock_hash",
        }

        response = await client.post("/api/auth/telegram-auth", json=auth_data)

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication data expired"

        logger.info("Expired auth test passed")

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        logger.info("Testing protected endpoint without token")

        response = await client.get("/api/telegram/chats")

        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"

        logger.info("Protected endpoint test passed")

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token(
        self, client: AsyncClient, test_user
    ):
        """Test accessing protected endpoint with valid token."""
        logger.info("Testing protected endpoint with valid token")

        # Create valid JWT token
        payload = {
            "user_id": test_user.id,
            "tg_user_id": test_user.tg_user_id,
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        token = jwt.encode(
            payload,
            os.getenv("JWT_SECRET_KEY"),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        )

        # Test a simpler protected endpoint that doesn't use Telegram
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/timeline/", headers=headers)

        # Should succeed with authentication (200) or return empty list
        assert response.status_code == 200
        assert isinstance(response.json(), list)  # Should return a list

        logger.info("Valid token test passed")
