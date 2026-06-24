from fastapi import APIRouter, Depends
from app.middlewares.admin import get_admin_user
from app.middlewares.auth import get_current_user
from app.schemas.user_schema import UpdateUserSchema
from app.config.db import db


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "name": current_user.get("name")
    }


@router.put("/me")
def update_me(
    data: UpdateUserSchema,
    current_user: dict = Depends(get_current_user)
):
    db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": data.dict(exclude_none=True)}
    )

    updated_user = db["users"].find_one(
        {"_id": current_user["_id"]}
    )

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": str(updated_user["_id"]), # type: ignore
            "email": updated_user["email"], # type: ignore
            "name": updated_user.get("name") # type: ignore
        }
    }
    
@router.get("/all-users")
def get_all_users(admin=Depends(get_admin_user)):

    users = list(db["users"].find())

    for user in users:
        user["_id"] = str(user["_id"])

    return users     
