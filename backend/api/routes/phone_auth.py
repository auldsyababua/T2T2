"""
Phone authentication routes for Telethon-based authentication.
Replaces Mini App authentication with phone number verification.
"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.models.models import User
from backend.services.auth_service import TelegramAuthService
from backend.services.session_service import SessionService
from backend.api.dependencies import get_current_user
from backend.utils.auth import create_access_token
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Initialize services
api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
api_hash = os.getenv("TELEGRAM_API_HASH", "")

if not api_id or not api_hash:
    logger.error("[PHONE_AUTH] Missing TELEGRAM_API_ID or TELEGRAM_API_HASH")
    raise ValueError("Telegram API credentials not configured")

auth_service = TelegramAuthService(api_id, api_hash)
session_service = SessionService()


# Request/Response models
class SendCodeRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number with country code (e.g., +1234567890)")


class SendCodeResponse(BaseModel):
    phone_code_hash: str
    session_string: str
    message: str = "Verification code sent"


class VerifyCodeRequest(BaseModel):
    phone_number: str
    code: str = Field(..., description="Verification code received via SMS/Telegram")
    phone_code_hash: str
    session_string: str
    password: Optional[str] = Field(None, description="2FA password if required")


class VerifyCodeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[dict] = None
    session_valid: bool = False


@router.post("/send-code", response_model=SendCodeResponse)
async def send_verification_code(
    request: SendCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send verification code to phone number.
    This initiates the Telegram authentication process.
    """
    logger.info(f"[PHONE_AUTH] Send code request for phone: {request.phone_number[:3]}...{request.phone_number[-2:]}")
    
    try:
        # Send code via Telethon
        phone_code_hash, session_string = await auth_service.send_code(request.phone_number)
        
        logger.info(f"[PHONE_AUTH] Code sent successfully")
        
        return SendCodeResponse(
            phone_code_hash=phone_code_hash,
            session_string=session_string
        )
        
    except ValueError as e:
        logger.error(f"[PHONE_AUTH] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[PHONE_AUTH] Error sending code: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code"
        )


@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify the code and complete authentication.
    Returns JWT token for subsequent API calls.
    """
    logger.info(f"[PHONE_AUTH] Verify code request for phone: {request.phone_number[:3]}...{request.phone_number[-2:]}")
    
    try:
        # Verify code and get user
        user, session_string = await auth_service.verify_code(
            phone=request.phone_number,
            code=request.code,
            phone_code_hash=request.phone_code_hash,
            session_string=request.session_string,
            password=request.password
        )
        
        logger.info(f"[PHONE_AUTH] Code verified successfully for user {user.id}")
        
        # Encrypt session for storage
        encrypted_session = session_service.encrypt_session(session_string, {
            'user_id': str(user.id),
            'phone': request.phone_number
        })
        
        # Update user with encrypted session
        user.session_string = encrypted_session
        await db.commit()
        
        logger.info(f"[PHONE_AUTH] Session encrypted and saved")
        
        # Create JWT token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"[PHONE_AUTH] JWT token created for user {user.id}")
        
        # Return response
        return VerifyCodeResponse(
            access_token=access_token,
            user={
                "id": str(user.id),
                "telegram_id": user.tg_user_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number[:3] + "..." + user.phone_number[-2:]  # Masked
            }
        )
        
    except ValueError as e:
        logger.error(f"[PHONE_AUTH] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[PHONE_AUTH] Error verifying code: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify code"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and destroy Telegram session.
    """
    logger.info(f"[PHONE_AUTH] Logout request for user {current_user.id}")
    
    try:
        if current_user.session_string:
            # Decrypt session
            decrypted_session = session_service.decrypt_session(current_user.session_string)
            
            # Logout from Telegram
            await auth_service.logout(decrypted_session)
            
            # Clear session from database
            current_user.session_string = None
            current_user.session_created_at = None
            await db.commit()
            
            logger.info(f"[PHONE_AUTH] User {current_user.id} logged out successfully")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"[PHONE_AUTH] Error during logout: {type(e).__name__}: {str(e)}")
        # Still clear the session even if Telegram logout fails
        current_user.session_string = None
        current_user.session_created_at = None
        await db.commit()
        
        return {"message": "Logged out (with errors)"}


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check authentication status and session validity.
    """
    logger.info(f"[PHONE_AUTH] Status check request")
    
    if not current_user:
        logger.info(f"[PHONE_AUTH] No authenticated user")
        return AuthStatusResponse(authenticated=False)
    
    logger.info(f"[PHONE_AUTH] User {current_user.id} is authenticated")
    
    # Check session validity
    session_valid = False
    if current_user.session_string:
        try:
            decrypted_session = session_service.decrypt_session(current_user.session_string)
            session_valid = await auth_service.check_session_validity(decrypted_session)
            logger.info(f"[PHONE_AUTH] Session validity: {session_valid}")
        except Exception as e:
            logger.error(f"[PHONE_AUTH] Error checking session: {e}")
    
    return AuthStatusResponse(
        authenticated=True,
        user={
            "id": str(current_user.id),
            "telegram_id": current_user.tg_user_id,
            "username": current_user.username,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number[:3] + "..." + current_user.phone_number[-2:] if current_user.phone_number else None
        },
        session_valid=session_valid
    )