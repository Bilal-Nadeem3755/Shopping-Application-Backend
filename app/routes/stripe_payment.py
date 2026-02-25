# import stripe
# from fastapi import APIRouter, Depends, HTTPException
# from bson import ObjectId
# from dotenv import load_dotenv
# import os

# from app.config.db import db
# from app.middlewares.auth import get_current_user

# load_dotenv()

# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# router = APIRouter(
#     prefix="/stripe",
#     tags=["Stripe Payment"]
# )

# @router.post("/checkout/{order_id}")
# def create_stripe_checkout(order_id: str, current_user=Depends(get_current_user)):

#     user_id = str(current_user["_id"])

#     order = db["orders"].find_one({
#         "_id": ObjectId(order_id),
#         "user_id": user_id
#     })

#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")

#     if order["status"] == "paid":
#         raise HTTPException(status_code=400, detail="Order already paid")

#     session = stripe.checkout.Session.create(
#         payment_method_types=["card"],
#         mode="payment",
#         line_items=[
#             {
#                 "price_data": {
#                     "currency": "usd",
#                     "product_data": {
#                         "name": "Order Payment"
#                     },
#                     "unit_amount": int(order["total"] * 100)
#                 },
#                 "quantity": 1
#             }
#         ],
#         success_url=os.getenv("FRONTEND_SUCCESS_URL"), # type: ignore
#         cancel_url=os.getenv("FRONTEND_CANCEL_URL"), # type: ignore
#         metadata={
#             "order_id": str(order["_id"])
#         }
#     )

#     return {
#         "checkout_url": session.url
#     }
import stripe
import os
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from dotenv import load_dotenv

from app.config.db import db
from app.middlewares.auth import get_current_user

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(
    prefix="/stripe",
    tags=["Stripe Payment"]
)


@router.post("/checkout/{order_id}")
def create_stripe_checkout(order_id: str, current_user=Depends(get_current_user)):

    try:
        order_object_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = db["orders"].find_one({
        "_id": order_object_id,
        "user_id": str(current_user["_id"])
    })

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] != "pending_payment":
        raise HTTPException(
            status_code=400,
            detail="Only pending_payment orders can be paid"
        )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Order #{order_id}"
                    },
                    "unit_amount": int(order["total_amount"] * 100)
                },
                "quantity": 1
            }
        ],
        success_url=os.getenv("FRONTEND_SUCCESS_URL"),
        cancel_url=os.getenv("FRONTEND_CANCEL_URL"),
        metadata={
            "order_id": order_id
        }
    )

    return {
        "checkout_url": session.url
    }
