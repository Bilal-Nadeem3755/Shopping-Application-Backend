from app.config.db import db
from argon2 import PasswordHasher
from fastapi import HTTPException
from bson import ObjectId
import secrets
from app.services.email_service import send_email
from datetime import datetime, timedelta

ph = PasswordHasher()
users = db["users"]


# ✅ CREATE USER
def create_user(user_data: dict):

    # 🔐 hash password
    user_data["password"] = ph.hash(user_data["password"])

    # 🔐 generate verification token
    verification_token = secrets.token_urlsafe(32)
    verification_token_expiry = datetime.utcnow() + timedelta(minutes=15)

    user_data["is_verified"] = False
    user_data["verification_token"] = verification_token
    user_data["verification_token_expiry"] = verification_token_expiry

    users.insert_one(user_data)

    # 🔗 verification link
    verification_link = f"http://localhost:8000/auth/verify-email/{verification_token}"

    # 📧 send verification email
    send_email(
        to_email=user_data["email"],
        subject="Verify Your Email",
        body=f"""
Hi,

Click the link below to verify your account:

{verification_link}

This link will expire in 15 minutes.

If you did not sign up, ignore this email.
"""
    )

    return {"message": "User created. Verification email sent."}


# ✅ VERIFY EMAIL
def verify_email(token: str):

    user = users.find_one({"verification_token": token})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    expiry = user.get("verification_token_expiry")

    if not expiry:
        raise HTTPException(status_code=400, detail="Token expiry missing")

    # 🛑 Force datetime comparison
    if datetime.utcnow() > expiry:
        raise HTTPException(status_code=400, detail="Verification token expired")

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"is_verified": True},
            "$unset": {
                "verification_token": "",
                "verification_token_expiry": ""
            }
        }
    )

    return {"message": "Email verified successfully"}

# ✅ AUTHENTICATE USER
def authenticate_user(email: str, password: str):

    user = users.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        ph.verify(user["password"], password)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user.get("is_verified"):
        raise HTTPException(
            status_code=403,
            detail="Please verify your email first"
        )

    return user


# ✅ UPDATE USER
def update_user(user_id: str, data: dict):

    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": data}
    )

    return users.find_one(
        {"_id": ObjectId(user_id)},
        {"password": 0}
    )


# ✅ FORGOT PASSWORD
def forgot_password(email: str):

    user = users.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = secrets.token_urlsafe(32)
    reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_token": reset_token,
                "reset_token_expiry": reset_token_expiry
            }
        }
    )

    reset_link = f"http://localhost:8000/auth/reset-password/{reset_token}"

    send_email(
        to_email=email,
        subject="Reset Your Password",
        body=f"""
Hi,

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request this, ignore this email.
"""
    )

    return {"message": "Password reset email sent"}


# ✅ RESET PASSWORD
def reset_password(token: str, new_password: str):

    user = users.find_one({"reset_token": token})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    # ⏰ expiry check
    if user.get("reset_token_expiry") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")

    hashed_password = ph.hash(new_password)

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": hashed_password},
            "$unset": {
                "reset_token": "",
                "reset_token_expiry": ""
            }
        }
    )

    return {"message": "Password reset successfully"}

# ✅ RESEND VERIFICATION EMAIL

def resend_verification(email: str):

    user = users.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="Email already verified")

    # 🔐 generate new token
    verification_token = secrets.token_urlsafe(32)
    verification_token_expiry = datetime.utcnow() + timedelta(minutes=15)

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "verification_token": verification_token,
                "verification_token_expiry": verification_token_expiry
            }
        }
    )

    verification_link = f"http://localhost:8000/auth/verify-email/{verification_token}"

    send_email(
        to_email=email,
        subject="Resend Verification Email",
        body=f"""
Hi,

Click the link below to verify your account:

{verification_link}

This link will expire in 15 minutes.
"""
    )

    return {"message": "Verification email resent successfully"}
