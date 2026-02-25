from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from app.schemas.order_schema import CreateOrderSchema
from app.services.order_service import (
    create_order,
    get_user_orders,
    get_all_orders
)
from app.middlewares.auth import get_current_user
from app.middlewares.admin import require_admin, get_admin_user
from app.config.db import db
from app.utils.order_status import can_update_status
from app.services.email_service import send_email

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# =========================
# 👤 USER - GET MY ORDERS
# =========================
@router.get("/")
def get_my_orders(current_user=Depends(get_current_user)):
    return get_user_orders(current_user["_id"])


# =========================
# 👑 ADMIN - GET ALL ORDERS
# =========================
@router.get("/all", dependencies=[Depends(require_admin)])
def admin_get_all_orders():
    return get_all_orders()


# =========================
# 🔄 ADMIN - UPDATE STATUS
# =========================
@router.put("/admin/update-status/{order_id}")
def update_order_status(
    order_id: str,
    new_status: str,
    admin_user=Depends(get_admin_user)
):

    try:
        order_object_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = db["orders"].find_one({"_id": order_object_id})

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    current_status = order.get("status")

    if not can_update_status(current_status, new_status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from {current_status} to {new_status}"
        )

    db["orders"].update_one(
        {"_id": order_object_id},
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
        }
    )

    user = db["users"].find_one({"_id": order["user_id"]})

    if user:

        if new_status == "shipped":
            send_email(
                to_email=user["email"],
                subject="Your Order Has Been Shipped 🚚",
                body=f"Hi {user.get('name', '')}, your order has been shipped."
            )

        elif new_status == "delivered":
            send_email(
                to_email=user["email"],
                subject="Order Delivered 📦",
                body=f"Hi {user.get('name', '')}, your order has been delivered."
            )

    return {"message": f"Order status updated to {new_status}"}


# =========================
# 🛒 PLACE ORDER
# =========================
@router.post("/place")
def place_order(
    order: CreateOrderSchema,
    current_user: dict = Depends(get_current_user)
):
    return create_order(current_user["_id"], order)
