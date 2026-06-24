from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth_schema import SignupSchema
from app.controllers.auth_controller import (
    create_user,
    authenticate_user,
    forgot_password,
    reset_password,
    verify_email,
    resend_verification,
)

from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
)

from app.config.db import db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

users_collection = db["users"]

# ---------------- SIGNUP ----------------
@router.post("/signup")
def signup(user: SignupSchema):
    create_user(user.dict())
    return {"message": "User created successfully"}


# ---------------- LOGIN ----------------

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    db_user = authenticate_user(
        form_data.username,
        form_data.password
    )

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid Username or Password")

    # Create tokens with verified status
    access_token = create_access_token({
    "sub": db_user["email"],
    "user_id": str(db_user["_id"]),
    "is_verified": db_user.get("is_verified", False),  #  FIX
    "role": db_user.get("role", "user")
})

    refresh_token = create_refresh_token({
        "sub": db_user["email"]
    })

    # Save refresh token in DB
    users_collection.update_one(
        {"email": db_user["email"]},
        {"$set": {"refresh_token": refresh_token}}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# ---------------- FORGOT PASSWORD ----------------
@router.post("/forgot-password")
def forgot_password_route(email: str = Body(..., embed=True)):
    return forgot_password(email)


# ---------------- RESET PASSWORD ----------------
@router.post("/reset-password/{token}")
def reset_password_route(token: str, new_password: str = Body(..., embed=True)):
    return reset_password(token, new_password)


# ---------------- RESEND VERIFICATION ----------------
@router.post("/resend-verification")
def resend_verification_route(email: str = Body(..., embed=True)):
    return resend_verification(email)


# ---------------- REFRESH TOKEN ----------------
@router.post("/refresh")
def refresh_token_route(refresh_token: str = Body(..., embed=True)):

    payload = verify_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    email = payload.get("sub")

    user = users_collection.find_one({"email": email})

    if not user or user.get("refresh_token") != refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    #  ALSO ADD ROLE HERE
    new_access_token = create_access_token({
        "sub": email,
        "user_id": str(user["_id"]),
        "role": user.get("role", "user")   #  IMPORTANT
    })

    return {"access_token": new_access_token}


# ---------------- LOGOUT ----------------
@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):

    users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {"refresh_token": None}}
    )

    return {"message": "Logged out successfully"}

@router.get("/verify-email/{token}")
def verify_email_route(token: str):
    return verify_email(token)
