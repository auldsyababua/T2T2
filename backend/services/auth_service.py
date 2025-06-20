"""
Telegram authentication service using Telethon for full chat history access.
Handles phone number authentication and session management.
"""
import asyncio
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
    FloodWaitError,
)

from backend.utils.logging import setup_logger
from backend.db.database import get_db
from backend.models.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = setup_logger(__name__)


class TelegramAuthService:
    """Handles phone number authentication and session management for Telethon"""

    def __init__(self, api_id: int, api_hash: str):
        """Initialize the auth service with Telegram API credentials"""
        self.api_id = api_id
        self.api_hash = api_hash
        self._clients = {}  # Store active clients by phone number

        logger.info(f"[AUTH_SERVICE] Initialized with API ID: {api_id}")
        logger.info(f"[AUTH_SERVICE] API Hash last 4 chars: ...{api_hash[-4:]}")

    async def send_code(self, phone: str) -> Tuple[str, str]:
        """
        Send verification code to phone number.
        Returns: (phone_code_hash, session_string)
        """
        logger.info(f"[AUTH_SERVICE] Sending code to phone: {phone[:3]}...{phone[-2:]}")

        # Validate phone number format
        if not phone.startswith("+"):
            phone = "+" + phone
            logger.info(f"[AUTH_SERVICE] Added + prefix to phone number")

        # Create a new string session
        session = StringSession()
        client = TelegramClient(session, self.api_id, self.api_hash)

        try:
            logger.info(f"[AUTH_SERVICE] Connecting to Telegram...")
            await client.connect()

            if not await client.is_user_authorized():
                logger.info(f"[AUTH_SERVICE] User not authorized, sending code...")

                try:
                    # Send code request
                    sent_code = await client.send_code_request(phone)
                    phone_code_hash = sent_code.phone_code_hash

                    # Store client for later verification
                    self._clients[phone] = client

                    logger.info(f"[AUTH_SERVICE] Code sent successfully")
                    logger.info(
                        f"[AUTH_SERVICE] Phone code hash: {phone_code_hash[:10]}..."
                    )
                    logger.info(
                        f"[AUTH_SERVICE] Code type: {sent_code.type.__class__.__name__}"
                    )

                    # Get the session string to return
                    session_string = session.save()

                    return phone_code_hash, session_string

                except PhoneNumberInvalidError:
                    logger.error(f"[AUTH_SERVICE] Invalid phone number: {phone}")
                    raise ValueError("Invalid phone number format")

                except FloodWaitError as e:
                    logger.error(
                        f"[AUTH_SERVICE] Flood wait error: {e.seconds} seconds"
                    )
                    raise ValueError(
                        f"Too many attempts. Please wait {e.seconds} seconds"
                    )

            else:
                logger.warning(
                    f"[AUTH_SERVICE] User already authorized for phone {phone}"
                )
                raise ValueError("User already authorized")

        except Exception as e:
            logger.error(
                f"[AUTH_SERVICE] Error sending code: {type(e).__name__}: {str(e)}"
            )
            if phone in self._clients:
                await self._clients[phone].disconnect()
                del self._clients[phone]
            raise

    async def verify_code(
        self,
        phone: str,
        code: str,
        phone_code_hash: str,
        session_string: str,
        password: Optional[str] = None,
    ) -> Tuple[User, str]:
        """
        Verify the code and create/update user session.
        Returns: (user, encrypted_session_string)
        """
        logger.info(
            f"[AUTH_SERVICE] Verifying code for phone: {phone[:3]}...{phone[-2:]}"
        )
        logger.info(f"[AUTH_SERVICE] Code length: {len(code)}")
        logger.info(f"[AUTH_SERVICE] Phone code hash: {phone_code_hash[:10]}...")

        if not phone.startswith("+"):
            phone = "+" + phone

        # Get existing client or create new one with session
        client = self._clients.get(phone)
        if not client:
            logger.info(f"[AUTH_SERVICE] Creating new client from session string")
            session = StringSession(session_string)
            client = TelegramClient(session, self.api_id, self.api_hash)
            await client.connect()

        try:
            # Try to sign in with the code
            logger.info(f"[AUTH_SERVICE] Attempting to sign in...")

            try:
                user_info = await client.sign_in(
                    phone, code, phone_code_hash=phone_code_hash
                )
                logger.info(f"[AUTH_SERVICE] Sign in successful!")

            except SessionPasswordNeededError:
                logger.warning(f"[AUTH_SERVICE] 2FA password required")
                if not password:
                    raise ValueError("Two-factor authentication password required")

                logger.info(f"[AUTH_SERVICE] Attempting sign in with 2FA password...")
                user_info = await client.sign_in(password=password)
                logger.info(f"[AUTH_SERVICE] 2FA sign in successful!")

            except PhoneCodeInvalidError:
                logger.error(f"[AUTH_SERVICE] Invalid verification code")
                raise ValueError("Invalid verification code")

            except PhoneCodeExpiredError:
                logger.error(f"[AUTH_SERVICE] Verification code expired")
                raise ValueError("Verification code has expired")

            # Get user details
            me = await client.get_me()
            logger.info(f"[AUTH_SERVICE] Retrieved user info - ID: {me.id}")
            logger.info(f"[AUTH_SERVICE] Username: {me.username or 'None'}")
            logger.info(f"[AUTH_SERVICE] Name: {me.first_name} {me.last_name or ''}")

            # Get final session string
            final_session = client.session.save()
            logger.info(f"[AUTH_SERVICE] Session string length: {len(final_session)}")

            # Create or update user in database
            async with get_db() as db:
                # Check if user exists
                result = await db.execute(
                    select(User).where(User.tg_user_id == str(me.id))
                )
                user = result.scalar_one_or_none()

                if user:
                    logger.info(f"[AUTH_SERVICE] Updating existing user {user.id}")
                    user.phone_number = phone
                    user.session_string = final_session  # Will be encrypted by service
                    user.session_created_at = datetime.utcnow()
                    user.last_auth_at = datetime.utcnow()
                    user.username = me.username
                    user.first_name = me.first_name
                    user.last_name = me.last_name
                else:
                    logger.info(f"[AUTH_SERVICE] Creating new user")
                    user = User(
                        tg_user_id=str(me.id),
                        phone_number=phone,
                        session_string=final_session,  # Will be encrypted by service
                        session_created_at=datetime.utcnow(),
                        last_auth_at=datetime.utcnow(),
                        username=me.username,
                        first_name=me.first_name,
                        last_name=me.last_name,
                    )
                    db.add(user)

                await db.commit()
                await db.refresh(user)

                logger.info(f"[AUTH_SERVICE] User saved to database - ID: {user.id}")

            return user, final_session

        finally:
            # Clean up client
            if phone in self._clients:
                await self._clients[phone].disconnect()
                del self._clients[phone]
                logger.info(f"[AUTH_SERVICE] Cleaned up client for {phone}")

    async def get_client_from_session(self, session_string: str) -> TelegramClient:
        """Create a Telegram client from a session string"""
        logger.info(f"[AUTH_SERVICE] Creating client from session string")

        session = StringSession(session_string)
        client = TelegramClient(session, self.api_id, self.api_hash)

        await client.connect()

        if await client.is_user_authorized():
            logger.info(f"[AUTH_SERVICE] Client authorized successfully")
            return client
        else:
            logger.error(f"[AUTH_SERVICE] Client not authorized with provided session")
            raise ValueError("Session is not authorized")

    async def logout(self, session_string: str) -> bool:
        """Logout and destroy a session"""
        logger.info(f"[AUTH_SERVICE] Logging out session")

        try:
            client = await self.get_client_from_session(session_string)
            await client.log_out()
            await client.disconnect()
            logger.info(f"[AUTH_SERVICE] Logout successful")
            return True
        except Exception as e:
            logger.error(f"[AUTH_SERVICE] Logout error: {type(e).__name__}: {str(e)}")
            return False

    async def check_session_validity(self, session_string: str) -> bool:
        """Check if a session is still valid"""
        logger.info(f"[AUTH_SERVICE] Checking session validity")

        try:
            client = await self.get_client_from_session(session_string)
            me = await client.get_me()
            await client.disconnect()

            logger.info(f"[AUTH_SERVICE] Session valid for user {me.id}")
            return True
        except Exception as e:
            logger.error(
                f"[AUTH_SERVICE] Session invalid: {type(e).__name__}: {str(e)}"
            )
            return False
