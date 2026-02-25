# import stripe
# from fastapi import APIRouter, Depends, HTTPException
# from bson import ObjectId
# from dotenv import load_dotenv
# import os
# from datetime import datetime

# from app.config.db import db
# from app.middlewares.auth import get_current_user

# load_dotenv()

# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# router = APIRouter(
#     prefix="/refund",
#     tags=["Refund"]
# )


# @router.post("/{order_id}")
# def create_refund(order_id: str, current_user=Depends(get_current_user)):

#     user_id = str(current_user["_id"])

#     # 🔍 Find order
#     order = db["orders"].find_one({
#         "_id": ObjectId(order_id),
#         "user_id": user_id
#     })

#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")

#     if order.get("status") != "paid":
#         raise HTTPException(status_code=400, detail="Order is not paid")

#     if not order.get("payment_intent_id"):
#         raise HTTPException(status_code=400, detail="PaymentIntent not found")

#     try:
#         # 💳 Create refund from Stripe
#         refund = stripe.Refund.create(
#             payment_intent=order["payment_intent_id"]
#         )

#         # ⚠️ Note:
#         # Status update webhook handle karega (charge.refunded)

#         return {
#             "message": "Refund initiated successfully",
#             "refund_id": refund.id
#         }

#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

import stripe
import os
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from dotenv import load_dotenv
from datetime import datetime

from app.config.db import db
from app.middlewares.auth import get_current_user

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(
    prefix="/refund",
    tags=["Refund"]
)


@router.post("/{order_id}")
def create_refund(order_id: str, current_user=Depends(get_current_user)):

    try:
        order_object_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    # 🔍 Find order (ObjectId match)
    order = db["orders"].find_one({
        "_id": order_object_id,
        "user_id": current_user["_id"]
    })

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.get("status") != "paid":
        raise HTTPException(status_code=400, detail="Order is not paid")

    if not order.get("payment_intent_id"):
        raise HTTPException(status_code=400, detail="Payment information not found")

    try:
        # 💳 Create refund in Stripe
        refund = stripe.Refund.create(
            payment_intent=order["payment_intent_id"]
        )

        # ✅ Update order immediately
        db["orders"].update_one(
            {"_id": order_object_id},
            {
                "$set": {
                    "status": "refund_initiated",
                    "refund_id": refund.id,
                    "refund_requested_at": datetime.utcnow()
                }
            }
        )

        return {
            "message": "Refund initiated successfully",
            "refund_id": refund.id
        }

    except stripe.error.StripeError as e: # type: ignore
        raise HTTPException(status_code=400, detail=str(e))
