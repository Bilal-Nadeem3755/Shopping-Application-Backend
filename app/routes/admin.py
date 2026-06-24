from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.routes.user import get_all_users
from app.config.db import db
from app.middlewares.admin import get_admin_user, require_admin

#  SINGLE ROUTER ONLY
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)]
)

# =========================
#  DASHBOARD STATS
# =========================
@router.get("/stats")
def get_dashboard_stats():

    total_orders = db["orders"].count_documents({})
    total_products = db["products"].count_documents({})
    total_users = db["users"].count_documents({})

    return {
        "total_orders": total_orders,
        "total_products": total_products,
        "total_users": total_users
    }


# =========================
#  ADMIN DASHBOARD
# =========================
@router.get("/dashboard")
def admin_dashboard():

    return {
        "message": "Welcome Admin 👑"
    }


# =========================
#  MAKE ADMIN
# =========================
@router.put("/make-admin/{user_id}")
def make_admin(user_id: str):
    
    admin=Depends(get_admin_user)

    result = db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": "admin"}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "message": "User promoted to admin successfully"
    }
# =========================
#  REMOVE ADMIN
# =========================
@router.put("/remove-admin/{user_id}")
def remove_admin(
    user_id: str,
    admin_user=Depends(get_admin_user)
):

    if str(admin_user["_id"]) == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin role"
        )

    user = db["users"].find_one(
        {"_id": ObjectId(user_id)}
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": "user"}}
    )

    return {
        "message": "Admin removed successfully"
    }