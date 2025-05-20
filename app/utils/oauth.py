import httpx
from fastapi import HTTPException
import json
from urllib.parse import urlencode
from app.core.config import settings
from typing import Dict, Any, Tuple, Optional

async def get_google_auth_url() -> str:
    """Google OAuth 로그인 URL을 생성합니다."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URL,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
        "state": "google"
    }
    return f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"

async def get_facebook_auth_url() -> str:
    """Facebook OAuth 로그인 URL을 생성합니다."""
    params = {
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URL,
        "response_type": "code",
        "scope": "email,public_profile",
        "state": "facebook"
    }
    return f"https://www.facebook.com/v17.0/dialog/oauth?{urlencode(params)}"

async def verify_google_token(code: str) -> Tuple[str, str, str, Optional[str]]:
    """Google OAuth 코드를 검증하고 사용자 정보를 반환합니다."""
    # 액세스 토큰 얻기
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.OAUTH_REDIRECT_URL,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Google OAuth token validation failed")
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        
        # 사용자 정보 얻기
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = await client.get(user_info_url, headers=headers)
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google user info")
        
        user_info = user_response.json()
        user_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        profile_image = user_info.get("picture")
        
        return user_id, email, name, profile_image

async def verify_facebook_token(code: str) -> Tuple[str, str, str, Optional[str]]:
    """Facebook OAuth 코드를 검증하고 사용자 정보를 반환합니다."""
    # 액세스 토큰 얻기
    token_url = "https://graph.facebook.com/v17.0/oauth/access_token"
    token_params = {
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "client_secret": settings.FACEBOOK_CLIENT_SECRET,
        "redirect_uri": settings.OAUTH_REDIRECT_URL,
        "code": code
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.get(token_url, params=token_params)
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Facebook OAuth token validation failed")
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        
        # 사용자 정보 얻기
        user_info_url = "https://graph.facebook.com/me"
        params = {
            "fields": "id,email,name,picture.type(large)",
            "access_token": access_token
        }
        user_response = await client.get(user_info_url, params=params)
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Facebook user info")
        
        user_info = user_response.json()
        user_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        profile_image = user_info.get("picture", {}).get("data", {}).get("url")
        
        return user_id, email, name, profile_image 