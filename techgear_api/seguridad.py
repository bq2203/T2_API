"""Hash de contraseñas (bcrypt) y tokens JWT."""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")

# Defínelo en techgear_api/.env:  JWT_SECRET=una-cadena-larga-y-aleatoria
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-cambiar-en-.env")
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", "60"))

# Emails que serán administradores. En .env:  ADMIN_EMAILS=admin@correo.com,otro@correo.com
ADMIN_EMAILS = {
    e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()
}


def es_email_admin(email: str) -> bool:
    return email.lower() in ADMIN_EMAILS


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar_password(password: str, hash_: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hash_.encode())
    except ValueError:
        return False


def crear_token(user_id: str) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> str:
    """Devuelve el id de usuario o lanza 401 si el token es inválido/expirado."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
