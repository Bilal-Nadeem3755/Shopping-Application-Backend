# 

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timedelta
from app.config.db import db
from app.middlewares.auth import get_current_user
from app.middlewares.admin import get_admin_user
import stripe
from dotenv import load_dotenv
import os

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(
    prefix="/returns",
    tags=["Returns"]
)


# ===============================
# 🧾 USER CREATE RETURN REQUEST
# ===============================
@router.post("/{order_id}")
def create_return_request(
    order_id: str,
    reason: str,
    current_user=Depends(get_current_user)
):

    try:
        order_object_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    # 🔍 Check order exists (ObjectId match)
    order = db["orders"].find_one({
        "_id": order_object_id,
        "user_id": current_user["_id"]
    })

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.get("status") != "paid":
        raise HTTPException(status_code=400, detail="Only paid orders can be returned")

    # =========================
    # ⏳ 7 DAYS RETURN WINDOW
    # =========================
    paid_at = order.get("paid_at")

    if not paid_at:
        raise HTTPException(status_code=400, detail="Payment date not found")

    if datetime.utcnow() > paid_at + timedelta(days=7):
        raise HTTPException(
            status_code=400,
            detail="Return window expired (7 days limit)"
        )

    # 🔁 Prevent duplicate return
    existing_return = db["returns"].find_one({
        "order_id": order_object_id
    })

    if existing_return:
        raise HTTPException(status_code=400, detail="Return already requested")

    return_doc = {
        "order_id": order_object_id,
        "user_id": current_user["_id"],
        "reason": reason,
        "status": "pending",   # pending | approved | rejected
        "admin_note": "",
        "created_at": datetime.utcnow(),
        "approved_at": None
    }

    db["returns"].insert_one(return_doc)

    return {"message": "Return request submitted successfully"}

# ===================================
# 👨‍💼 ADMIN APPROVE RETURN
# ===================================
@router.put("/admin/approve/{return_id}")
def approve_return(
    return_id: str,
    admin_note: str = "",
    admin_user=Depends(get_admin_user)
):

    try:
        return_object_id = ObjectId(return_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid return ID")

    return_request = db["returns"].find_one({
        "_id": return_object_id
    })

    if not return_request:
        raise HTTPException(status_code=404, detail="Return request not found")

    if return_request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Return already processed")

    order = db["orders"].find_one({
        "_id": return_request["order_id"]
    })

    if not order or not order.get("payment_intent_id"):
        raise HTTPException(status_code=400, detail="Payment information not found")

    try:
        # 💳 Stripe Refund
        refund = stripe.Refund.create(
            payment_intent=order["payment_intent_id"]
        )

        # 📝 Update return
        db["returns"].update_one(
            {"_id": return_object_id},
            {
                "$set": {
                    "status": "approved",
                    "admin_note": admin_note,
                    "admin_user": admin_user["_id"],
                    "approved_at": datetime.utcnow(),
                    "refund_id": refund.id
                }
            }
        )

        # 🔄 Update order status
        db["orders"].update_one(
            {"_id": order["_id"]},
            {
                "$set": {
                    "status": "refund_initiated"
                }
            }
        )

        return {
            "message": "Return approved and refund initiated",
            "refund_id": refund.id
        }

    except stripe.error.StripeError as e: # type: ignore
        raise HTTPException(status_code=400, detail=str(e))

# ===================================
# 👨‍💼 ADMIN REJECT RETURN
# ===================================
@router.put("/admin/reject/{return_id}")
def reject_return(
    return_id: str,
    admin_note: str = "",
    admin_user=Depends(get_admin_user)
):

    try:
        return_object_id = ObjectId(return_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid return ID")

    return_request = db["returns"].find_one({
        "_id": return_object_id
    })

    if not return_request:
        raise HTTPException(status_code=404, detail="Return request not found")

    if return_request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Return already processed")

    db["returns"].update_one(
        {"_id": return_object_id},
        {
            "$set": {
                "status": "rejected",
                "admin_note": admin_note,
                "admin_user": admin_user["_id"],
                "approved_at": datetime.utcnow()
            }
        }
    )

    return {
        "message": "Return request rejected successfully"
    }
