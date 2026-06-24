import stripe
import os
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from dotenv import load_dotenv

from app.config.db import db
from app.middlewares.auth import get_current_user

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/stripe", tags=["Stripe Payment"])


@router.post("/checkout/{order_id}")
def create_stripe_checkout(order_id: str, current_user=Depends(get_current_user)):

    try:
        order_object_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = db["orders"].find_one(
        {"_id": order_object_id, "user_id": current_user["_id"]}
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] != "pending_payment":
        raise HTTPException(
            status_code=400, detail="Only pending_payment orders can be paid"
        )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Order #{order_id}"},
                    "unit_amount": int(order["total_amount"] * 100),
                },
                "quantity": 1,
            }
        ],
        success_url=f"{os.getenv('FRONTEND_SUCCESS_URL')}/{order_id}",
        cancel_url=os.getenv("FRONTEND_CANCEL_URL"), # type: ignore
        metadata={"order_id": order_id},
        
    )
    print("ORDER ID:", order_id)
    print("CURRENT USER:", current_user["_id"])
    print(
    db["orders"].find_one({"_id": order_object_id})
 )
    

    return {"checkout_url": session.url}
