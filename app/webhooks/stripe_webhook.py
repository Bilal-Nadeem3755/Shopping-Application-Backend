import stripe
from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
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

    print("WEBHOOK HIT")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=400,
            detail="Missing Stripe signature"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=endpoint_secret
        )

    except stripe.error.SignatureVerificationError: # type: ignore
        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Webhook error"
        )

    event_type = event["type"]
    session = event["data"]["object"]
    event_id = event["id"]

    print("EVENT TYPE:", event_type)
    print("EVENT ID:", event_id)

    # ==========================
    # IDEMPOTENCY CHECK
    # ==========================
    existing_event = db["stripe_webhooks"].find_one(
        {"event_id": event_id}
    )

    if existing_event:
        return {"status": "already_processed"}

    db["stripe_webhooks"].insert_one(
    {
        "event_id": event_id,
        "event_type": event_type,
        "payload": {
            "id": event_id,
            "type": event_type
        },
        "created_at": datetime.utcnow(),
    }
)
    # ==================================================
    # PAYMENT SUCCESS
    # ==================================================
    if event_type == "checkout.session.completed":
        print("PAYMENT SUCCESS WEBHOOK RECEIVED")
        session = session.to_dict()

        order_id = (
            session
            .get("metadata", {})
            .get("order_id")
        )

        payment_intent_id = session.get(
            "payment_intent"
        )

        print("ORDER ID:", order_id)

        if not order_id:
            return {"status": "no_order_id"}

        order = db["orders"].find_one({
            "_id": ObjectId(order_id)
        })

        if not order:
            return {"status": "order_not_found"}

        if order["status"] != "pending_payment":
            return {"status": "already_processed"}

        # STOCK DEDUCT
        for item in order["items"]:

            db["products"].update_one(
                {
                    "_id": item["product_id"]
                },
                {
                    "$inc": {
                        "stock": -item["quantity"]
                    }
                }
            )

        # CLEAR CART
        db["cart"].delete_many({
            "user_id": str(order["user_id"])
        })

        # UPDATE ORDER
        db["orders"].update_one(
            {
                "_id": ObjectId(order_id)
            },
            {
                "$set": {
                    "status": "placed",
                    "payment_intent_id": payment_intent_id,
                    "paid_at": datetime.utcnow()
                }
            }
        )

        print("ORDER UPDATED")

        user = db["users"].find_one({
            "_id": order["user_id"]
        })

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

        return {"status": "payment_processed"}

    # ==================================================
    # REFUND
    # ==================================================
    elif event_type == "charge.refunded":

        payment_intent_id = session.get(
            "payment_intent"
        )

        if payment_intent_id:

            order = db["orders"].find_one({
                "payment_intent_id": payment_intent_id
            })

            if order:

                if order.get("status") == "refunded":
                    return {
                        "status": "already_refunded"
                    }

                refund_amount = (
                    session.get(
                        "amount_refunded",
                        0
                    ) / 100
                )

                db["orders"].update_one(
                    {
                        "_id": order["_id"]
                    },
                    {
                        "$set": {
                            "status": "refunded",
                            "refunded_amount": refund_amount,
                            "refunded_at": datetime.utcnow()
                        }
                    }
                )

                for item in order["items"]:

                    db["products"].update_one(
                        {
                            "_id": item["product_id"]
                        },
                        {
                            "$inc": {
                                "stock": item["quantity"]
                            }
                        }
                    )

                db["returns"].update_one(
                    {
                        "order_id": str(order["_id"])
                    },
                    {
                        "$set": {
                            "status": "completed"
                        }
                    }
                )

                user = db["users"].find_one({
                    "_id": order["user_id"]
                })

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

                return {"status": "refund_processed"}

    return {"status": "ignored"}