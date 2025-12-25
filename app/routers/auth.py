from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..services import mysql_adapter, auth_service

router = APIRouter(prefix="/auth")


class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
def register(body: RegisterIn):
    if mysql_adapter.get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    pw_hash = auth_service.hash_password(body.password)
    user_id = mysql_adapter.create_user(body.email, pw_hash)
    return {"id": user_id, "email": body.email}


@router.post("/login")
def login(body: LoginIn):
    row = mysql_adapter.get_user_by_email(body.email)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # row: (id, email, password_hash, role, created_at)
    user_id = row[0]
    email = row[1]
    password_hash = row[2]
    if not auth_service.verify_password(body.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth_service.create_access_token({"sub": email, "user_id": user_id})
    return {"access_token": token, "token_type": "bearer"}
