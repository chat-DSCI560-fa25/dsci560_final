import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))
ALGORITHM = "HS256"

def _truncate_password_bytes(password: str) -> bytes:
    """Truncate password to 72 bytes (not characters) for bcrypt compatibility."""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = _truncate_password_bytes(password)
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string (bcrypt hashes are base64 encoded)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    password_bytes = _truncate_password_bytes(plain_password)
    hash_bytes = password_hash.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, TypeError) as e:
        # Handle any bcrypt errors gracefully
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
