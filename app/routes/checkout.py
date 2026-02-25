from fastapi import APIRouter, Depends, HTTPException
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from app.schemas.checkout_schema import CheckoutSchema
from app.config.db import db
from app.middlewares.auth import get_current_user

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
)

@router.post("/")
def checkout(
    data: CheckoutSchema,
    current_user=Depends(get_current_user)
):

    user_id = str(current_user["_id"])
    payment_method = data.payment_method
    coupon_code = data.coupon_code

    cart_items = list(db["cart"].find({"user_id": user_id}))

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = 0
    order_items = []

    # ==============================
    # CALCULATE CART TOTAL
    # ==============================
    for item in cart_items:

        try:
            product_id = ObjectId(item["product_id"])
        except InvalidId:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product ID format: {item['product_id']}"
            )

        product = db["products"].find_one({"_id": product_id})

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {item['product_id']}"
            )

        if product["stock"] < item["quantity"]:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product['name']}"
            )

        item_total = product["price"] * item["quantity"]
        total_amount += item_total

        order_items.append({
            "product_id": str(product_id),
            "name": product["name"],
            "price": product["price"],
            "quantity": item["quantity"],
            "item_total": item_total
        })

    original_total = total_amount
    discount_amount = 0
    coupon_id = None

    # ==============================
    # APPLY COUPON (IF PROVIDED)
    # ==============================
    if coupon_code:

        coupon = db["coupons"].find_one({
            "code": coupon_code.upper(),
            "is_active": True
        })

        if not coupon:
            raise HTTPException(status_code=400, detail="Invalid coupon")

        # Expiry check
        if coupon.get("expiry_date") and datetime.utcnow() > coupon["expiry_date"]:
            raise HTTPException(status_code=400, detail="Coupon expired")

        # Usage limit check
        if coupon.get("max_usage") and coupon["used_count"] >= coupon["max_usage"]:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")

        # One-time per user
        already_used = db["coupon_usages"].find_one({
            "coupon_id": coupon["_id"],
            "user_id": ObjectId(user_id)
        })

        if already_used:
            raise HTTPException(status_code=400, detail="You already used this coupon")

        # Calculate discount
        if coupon["discount_type"] == "percentage":
            discount_amount = total_amount * (coupon["discount_value"] / 100)
        else:
            discount_amount = coupon["discount_value"]

        discount_amount = min(discount_amount, total_amount)
        total_amount -= discount_amount
        coupon_id = coupon["_id"]

        # Increase usage count
        db["coupons"].update_one(
            {"_id": coupon["_id"]},
            {"$inc": {"used_count": 1}}
        )

        db["coupon_usages"].insert_one({
            "coupon_id": coupon["_id"],
            "user_id": ObjectId(user_id),
            "used_at": datetime.utcnow()
        })

    # ==============================
    # CREATE ORDER
    # ==============================
    order_status = "placed" if payment_method in ["cod", "bank"] else "pending_payment"

    order = {
        "user_id": user_id,
        "items": order_items,
        "original_total": original_total,
        "discount_amount": float(discount_amount),
        "total_amount": float(total_amount),
        "coupon_id": coupon_id,
        "payment_method": payment_method,
        "status": order_status,
        "created_at": datetime.utcnow()
    }

    order_result = db["orders"].insert_one(order)
    order_id = str(order_result.inserted_id)

    # ==============================
    # COD / BANK FLOW
    # ==============================
    if payment_method in ["cod", "bank"]:

        for item in cart_items:
            db["products"].update_one(
                {"_id": ObjectId(item["product_id"])},
                {"$inc": {"stock": -item["quantity"]}}
            )

        db["cart"].delete_many({"user_id": user_id})

        return {
            "message": "Order placed successfully",
            "order_id": order_id,
            "status": "placed",
            "original_total": original_total,
            "discount_amount": float(discount_amount),
            "final_total": float(total_amount)
        }

    # ==============================
    # CARD FLOW
    # ==============================
    return {
        "message": "Proceed to Stripe payment",
        "order_id": order_id,
        "status": "pending_payment",
        "original_total": original_total,
        "discount_amount": float(discount_amount),
        "final_total": float(total_amount)
    }
