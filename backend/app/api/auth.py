"""
Authentication API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class SignupRequest(BaseModel):
    """Signup request model"""
    name: str
    email: str
    password: str
    department: str
    roll_id: str


class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str


class SignupResponse(BaseModel):
    """Signup response model"""
    success: bool
    message: str
    user_id: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response model"""
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    user_profile: Optional[dict] = None


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    """
    Register a new user
    
    - **name**: User full name
    - **email**: Must be @student.qu.edu.qa
    - **password**: Min 8 chars, uppercase, lowercase, digits
    - **department**: Department name
    - **roll_id**: Student ID/Roll number
    """
    result = await AuthService.signup(
        name=request.name,
        email=request.email,
        password=request.password,
        department=request.department,
        roll_id=request.roll_id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with email and password
    
    - **email**: User email
    - **password**: User password
    """
    result = await AuthService.login(
        email=request.email,
        password=request.password
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    return result


@router.post("/verify")
@router.get("/verify")
async def verify_token(authorization: str = Header(None)):
    """
    Verify access token
    
    Header: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header"
        )
    
    # Extract token from "Bearer <token>"
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    result = await AuthService.verify_token(token)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    return result


@router.post("/logout")
async def logout(authorization: str = Header(None)):
    """
    Logout user
    
    Header: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header"
        )
    
    # Extract token from "Bearer <token>"
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    result = await AuthService.logout(token)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result
