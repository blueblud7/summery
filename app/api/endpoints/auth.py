from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.db.database import get_db
from app.models.models import User
from app.utils.auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_active_user, get_premium_user, get_enterprise_user
)
from app.utils.oauth import (
    get_google_auth_url, get_facebook_auth_url,
    verify_google_token, verify_facebook_token
)
from app.schemas.user import UserCreate, UserSocialCreate, UserResponse, SubscriptionUpdate
import app.db.crud as crud
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

@router.post("/login", response_model=Dict[str, str])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """일반 로그인"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="소셜 로그인 계정이거나 계정이 존재하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 사용자 이름 또는 비밀번호",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    """일반 회원가입"""
    # 이메일 중복 확인
    db_user = crud.get_user_by_email(db, email=user_create.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다"
        )
    
    # 사용자 생성
    user = crud.create_user(
        db=db, 
        username=user_create.username, 
        email=user_create.email, 
        password=user_create.password
    )
    return user

@router.get("/google-login")
async def google_login():
    """구글 로그인 URL 반환"""
    redirect_url = await get_google_auth_url()
    return {"url": redirect_url}

@router.get("/facebook-login")
async def facebook_login():
    """페이스북 로그인 URL 반환"""
    redirect_url = await get_facebook_auth_url()
    return {"url": redirect_url}

@router.get("/callback")
async def oauth_callback(
    code: str, 
    state: str, 
    db: Session = Depends(get_db)
):
    """OAuth 콜백 처리"""
    try:
        if state == "google":
            user_id, email, name, profile_image = await verify_google_token(code)
            oauth_provider = "google"
        elif state == "facebook":
            user_id, email, name, profile_image = await verify_facebook_token(code)
            oauth_provider = "facebook"
        else:
            raise HTTPException(status_code=400, detail="Unknown OAuth provider")
        
        # 이미 존재하는 OAuth 사용자인지 확인
        user = crud.get_user_by_oauth(db, oauth_provider, user_id)
        
        # 존재하지 않으면 새로 생성
        if not user:
            # 이메일 중복 확인 (다른 방식으로 이미 가입된 경우)
            email_user = crud.get_user_by_email(db, email)
            if email_user:
                raise HTTPException(
                    status_code=400, 
                    detail="이미 다른 방식으로 가입된 이메일입니다"
                )
            
            # username 생성 (이메일에서 @ 앞부분)
            username = email.split('@')[0]
            
            # 사용자 생성
            user = crud.create_social_user(
                db=db,
                username=username,
                email=email,
                oauth_provider=oauth_provider,
                oauth_id=user_id,
                profile_image=profile_image
            )
        
        # 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # 인증 완료 후 리다이렉션할 URL (프론트엔드에서 처리)
        redirect_url = f"/auth-success?token={access_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_user_me(current_user: User = Depends(get_current_active_user)):
    """현재 로그인한 사용자 정보 반환"""
    return current_user

@router.post("/subscription", response_model=UserResponse)
async def update_subscription(
    subscription: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """사용자 구독 상태 업데이트"""
    # 실제 구현에서는 결제 처리 로직이 추가되어야 함
    
    # 구독 기간 (30일 또는 365일)
    duration = 30 if subscription.subscription_tier == "premium" else 365
    
    updated_user = crud.update_user_subscription(
        db=db,
        user_id=current_user.id,
        subscription_tier=subscription.subscription_tier,
        duration_days=duration
    )
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

@router.post("/create-admin")
async def create_admin(db: Session = Depends(get_db)):
    """관리자 계정 생성"""
    # 관리자 계정이 이미 존재하는지 확인
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists"
        )
    
    # 관리자 계정 생성
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("1234"),
        is_admin=True,
        subscription_tier="enterprise"
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return {"message": "Admin user created successfully"} 