import stripe
from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId  # type: ignore
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from app.services.email_service import send_email
from app.config.db import db

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/webhook")
logger = logging.getLogger(__name__)


@router.post("/stripe")
async def stripe_webhook(request: Request):

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=endpoint_secret
        )
    except stripe.error.SignatureVerificationError:  # type: ignore
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail="Webhook error")

    event_type = event["type"]
    data_object = event["data"]["object"]
    event_id = event["id"]

    # ===================================
    # 🧾 IDEMPOTENCY CHECK
    # ===================================
    existing_event = db["stripe_webhooks"].find_one({"event_id": event_id})
    if existing_event:
        return {"status": "already_processed"}

    db["stripe_webhooks"].insert_one({
        "event_id": event_id,
        "event_type": event_type,
        "payload": event,
        "created_at": datetime.utcnow()
    })

    # ===================================
    # ✅ PAYMENT SUCCESS
    # ===================================
    if event_type == "checkout.session.completed":

     order_id = data_object.get("metadata", {}).get("order_id")
    payment_intent_id = data_object.get("payment_intent")

    if not order_id: # type: ignore
        return {"status": "no_order_id"}

    order = db["orders"].find_one({"_id": ObjectId(order_id)})

    if not order:
        return {"status": "order_not_found"}

    if order["status"] != "pending_payment":
        return {"status": "already_processed"}

    # ✅ Deduct stock
    for item in order["items"]:
        db["products"].update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": -item["quantity"]}}
        )

    # ✅ Clear cart
    db["cart"].delete_many({"user_id": order["user_id"]})

    # ✅ Update order
    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "status": "placed",
                "payment_intent_id": payment_intent_id,
                "paid_at": datetime.utcnow()
            }
        }
    )


            # 🔥 Fetch updated order
    order = db["orders"].find_one({"_id": ObjectId(order_id)})

    if order:
                user = db["users"].find_one(
                    {"_id": ObjectId(order["user_id"])}
                )

                if user:
                    send_email(
                        to_email=user["email"],
                        subject="Payment Successful 🎉",
                        body=f"""
Hi {user.get('name', '')},

Your payment was successful.
Order ID: {order_id}
Total: ${order.get('total_amount', 0)}
Thank you for shopping with us!
"""
                    )

    # ===================================
    # 🔄 REFUND COMPLETED → RESTOCK + EMAIL
    # ===================================
    elif event_type == "charge.refunded":

        payment_intent_id = data_object.get("payment_intent")

        if payment_intent_id:

            order = db["orders"].find_one({
                "payment_intent_id": payment_intent_id
            })

            if order:

                # 🛑 Prevent double refund processing
                if order.get("status") == "refunded":
                    return {"status": "already_refunded"}

                refund_amount = data_object.get("amount_refunded", 0) / 100

                # ✅ Update order
                db["orders"].update_one(
                    {"_id": order["_id"]},
                    {
                        "$set": {
                            "status": "refunded",
                            "refunded_amount": refund_amount,
                            "refunded_at": datetime.utcnow()
                        }
                    }
                )

                # ✅ RESTOCK PRODUCTS
                for item in order["items"]:
                    db["products"].update_one(
                        {"_id": ObjectId(item["product_id"])},
                        {"$inc": {"stock": item["quantity"]}}
                    )

                # ✅ Update return request
                db["returns"].update_one(
                    {"order_id": str(order["_id"])},
                    {"$set": {"status": "completed"}}
                )

                # 🔥 SEND REFUND EMAIL
                user = db["users"].find_one(
                    {"_id": ObjectId(order["user_id"])}
                )

                if user:
                    send_email(
                        to_email=user["email"],
                        subject="Refund Processed 💰",
                        body=f"""
Hi {user.get('name', '')},

Your refund for order {order['_id']} has been processed.

Refund Amount: ${refund_amount}

Thank you.
"""
                    )

    return {"status": "success"}
