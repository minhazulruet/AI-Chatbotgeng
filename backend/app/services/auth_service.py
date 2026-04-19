"""
Authentication Service with Simple Email/Password Storage
"""
import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Optional, Dict
import re
from passlib.context import CryptContext
import uuid

# Password hashing - using pbkdf2 instead of bcrypt (more stable)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Initialize Supabase Client
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None


class AuthService:
    """Handle authentication operations with simple email/password storage"""
    
    VALID_EMAIL_DOMAIN = "@student.qu.edu.qa"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format and domain"""
        # Check if email ends with valid domain
        if not email.endswith(AuthService.VALID_EMAIL_DOMAIN):
            return False
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@student\.qu\.edu\.qa$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and digits"
        
        return True, "Password is valid"
    
    @staticmethod
    async def signup(
        name: str,
        email: str,
        password: str,
        department: str,
        roll_id: str
    ) -> Dict:
        """
        Register a new user by storing email/password in database
        
        Args:
            name: User full name
            email: User email (@student.qu.edu.qa)
            password: User password
            department: Department name
            roll_id: Student roll/ID number
        
        Returns:
            Dict with success status and message
        """
        try:
            # Validate email
            if not AuthService.validate_email(email):
                return {
                    "success": False,
                    "message": "Invalid email. Please use @student.qu.edu.qa email address."
                }
            
            # Validate password
            is_valid, message = AuthService.validate_password(password)
            if not is_valid:
                return {
                    "success": False,
                    "message": message
                }
            
            if not supabase:
                return {
                    "success": False,
                    "message": "Database connection error"
                }
            
            # Check if user already exists
            existing_user = supabase.table("users").select("id").eq("email", email).execute()
            if existing_user.data:
                return {
                    "success": False,
                    "message": "Email already registered"
                }
            
            # Hash the password
            hashed_password = AuthService.hash_password(password)
            
            # Create user in database
            user_id = str(uuid.uuid4())
            user_data = {
                "id": user_id,
                "email": email,
                "password": hashed_password,
                "name": name,
                "department": department,
                "roll_id": roll_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("users").insert(user_data).execute()
            
            return {
                "success": True,
                "message": "User registered successfully",
                "user_id": user_id
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Signup error: {str(e)}"
            }
    
    @staticmethod
    async def login(email: str, password: str) -> Dict:
        """
        Authenticate user by checking email and password in database
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dict with success status, token, and user info
        """
        try:
            if not supabase:
                return {
                    "success": False,
                    "message": "Database connection error"
                }
            
            # Get user from database
            response = supabase.table("users").select("*").eq("email", email).execute()
            
            if not response.data:
                return {
                    "success": False,
                    "message": "Email not found"
                }
            
            user = response.data[0]
            
            # Verify password
            if not AuthService.verify_password(password, user.get("password", "")):
                return {
                    "success": False,
                    "message": "Password is incorrect"
                }
            
            # Generate simple token (can be JWT in production)
            token = str(uuid.uuid4())
            
            return {
                "success": True,
                "message": "Login successful",
                "access_token": token,
                "refresh_token": token,
                "user_id": user["id"],
                "email": email,
                "user_profile": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "department": user.get("department", ""),
                    "roll_id": user.get("roll_id", "")
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Login error: {str(e)}"
            }
    
    @staticmethod
    async def verify_token(token: str) -> Dict:
        """
        Verify token (simple UUID-based token)
        
        Args:
            token: Access token
        
        Returns:
            Dict with verification status
        """
        try:
            # For now, just accept any non-empty token as valid
            # In production, use proper JWT verification
            if token and len(token) > 0:
                return {
                    "success": True,
                    "message": "Token is valid"
                }
            else:
                return {
                    "success": False,
                    "message": "Invalid or expired token"
                }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Token verification error: {str(e)}"
            }
    
    @staticmethod
    async def logout(token: str) -> Dict:
        """
        Logout user
        
        Args:
            token: Access token
        
        Returns:
            Dict with logout status
        """
        try:
            # Simple logout - just return success
            # In production, invalidate the token in database
            return {
                "success": True,
                "message": "Logged out successfully"
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Logout error: {str(e)}"
            }
