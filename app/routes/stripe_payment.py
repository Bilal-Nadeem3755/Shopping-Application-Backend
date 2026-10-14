
import logging
import os

import stripe
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv

from app.config.db import db
from app.middlewares.auth import get_current_user

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["Stripe Payment"])


@router.post("/checkout/{order_id}")
def create_stripe_checkout(
    order_id: str,
    current_user=Depends(get_current_user),
):
    try:
        # Check required Stripe configuration
        stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
        success_url = os.getenv("FRONTEND_SUCCESS_URL")
        cancel_url = os.getenv("FRONTEND_CANCEL_URL")

        if not stripe_secret_key:
            logger.error("STRIPE_SECRET_KEY environment variable is missing")
            raise HTTPException(
                status_code=500,
                detail="Payment configuration is missing",
            )

        if not success_url or not cancel_url:
            logger.error("Stripe success/cancel URL configuration is missing")
            raise HTTPException(
                status_code=500,
                detail="Payment URL configuration is missing",
            )

        stripe.api_key = stripe_secret_key

        # Validate order ID
        try:
            order_object_id = ObjectId(order_id)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid order ID",
            )

        # Find order belonging to the logged-in user
        order = db["orders"].find_one(
            {
                "_id": order_object_id,
                "user_id": current_user["_id"],
            }
        )

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )

        if order.get("status") != "pending_payment":
            raise HTTPException(
                status_code=400,
                detail="Only pending_payment orders can be paid",
            )

        # Validate order amount
        total_amount = float(order["total_amount"])

        if total_amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Order amount must be greater than zero",
            )

        amount_in_cents = round(total_amount * 100)

        logger.info(
            "Creating Stripe checkout session for order %s",
            order_id,
        )

        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"], 
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Order #{order_id}",
                        },
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"{success_url.rstrip('/')}/{order_id}",
            cancel_url=cancel_url,
            metadata={"order_id": order_id},
        )

        logger.info(
            "Stripe checkout session created successfully for order %s",
            order_id,
        )

        return {"checkout_url": session.url}

    except HTTPException:
        raise

    except stripe.error.StripeError: # type: ignore
        logger.exception("Stripe API error for order %s", order_id)
        raise HTTPException(
            status_code=502,
            detail="Stripe could not create the checkout session",
        )

    except Exception:
        logger.exception("Unexpected checkout error for order %s", order_id)
        raise HTTPException(
            status_code=500,
            detail="Unable to create checkout session. Check backend logs.",
        )