from fastapi import APIRouter, Depends, HTTPException
from app.middlewares.admin import require_admin
from bson import ObjectId
from app.config.db import db

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)]
)


@router.get("/dashboard")
def admin_dashboard(): # type: ignore
    return {
        "message": "Welcome Admin 👑"
    }



router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)]
)


@router.get("/dashboard")
def admin_dashboard():
    return {"message": "Welcome Admin 👑"}


@router.put("/make-admin/{user_id}")
def make_admin(user_id: str):
    result = db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": "admin"}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "User promoted to admin successfully"
    }
