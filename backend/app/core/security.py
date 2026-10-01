"""
DataGuard Security & Cryptography
Password hashing with native bcrypt and JWT bearer tokens with python-jose.
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from typing import Any
import bcrypt
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dataguard_secret_key_2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h default for demo convenience


def hash_password(password: str) -> str:
    """
    Hashes a password using native bcrypt with automatic salt.
    """
    pwd_bytes = password[:72].encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the stored bcrypt hash.
    """
    try:
        plain_bytes = plain_password[:72].encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Generates a signed JWT access token containing subject and claims.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decodes and validates a JWT token. Returns payload or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def compute_canonical_hash(payload: Any) -> str:
    """
    Computes deterministic SHA-256 hex digest of a JSON-serializable object
    using canonical formatting (sorted keys, compact separators).
    """
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def compute_canonical_hmac(payload: Any, secret: str = SECRET_KEY) -> str:
    """
    Computes HMAC-SHA256 hex digest of a JSON-serializable object using
    the secret key.
    """
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), canonical_bytes, hashlib.sha256).hexdigest()


def compute_file_sha256(filepath: str) -> str:
    """
    Computes SHA-256 hex digest of a file on disk.
    """
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

