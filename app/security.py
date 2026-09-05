from datetime import datetime, timedelta, timezone
import os

import jwt
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(email: str) -> str:
    secret_key = os.getenv("TRAINER_APP_SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "TRAINER_APP_SECRET_KEY environment variable is not set"
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": email,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=ALGORITHM,
    )
