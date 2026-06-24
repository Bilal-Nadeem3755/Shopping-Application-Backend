from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException
from app.config.db import db

orders_collection = db["orders"]
products_collection = db["products"]
coupons_collection = db["coupons"]
coupon_usage_collection = db["coupon_usages"]


# =========================
#  Mongo Serializer
# =========================
def serialize_mongo(data):

    if isinstance(data, list):
        return [serialize_mongo(item) for item in data]

    if isinstance(data, dict):

        new_data = {}

        for key, value in data.items():

            if isinstance(value, ObjectId):
                new_data[key] = str(value)

            elif isinstance(value, (list, dict)):
                new_data[key] = serialize_mongo(value)

            else:
                new_data[key] = value

        return new_data

    return data


# =========================
#  CREATE ORDER
# =========================
def create_order(user_id: str, order_data):

    # =========================
    #  VALIDATE USER
    # =========================
    try:
        user_object_id = ObjectId(user_id)

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    total_amount = 0
    order_items = []

    # =========================
    #  PRODUCTS + STOCK CHECK
    # =========================
    for item in order_data.items:

        # VALIDATE PRODUCT ID
        try:
            product_object_id = ObjectId(item.product_id)

        except Exception:
            raise HTTPException(status_code=400, detail="Invalid product ID")

        # FIND PRODUCT
        product = products_collection.find_one({"_id": product_object_id})

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # STOCK CHECK
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=400, detail=f"Only {product['stock']} items left in stock"
            )

        # CALCULATE TOTAL
        total_amount += product["price"] * item.quantity

        # SAVE ORDER ITEMS
        order_items.append({"product_id": product_object_id, "quantity": item.quantity})

    # SAVE ORIGINAL TOTAL
    original_total = float(total_amount)

    # =========================
    #  COUPON LOGIC
    # =========================
    discount_amount = 0
    coupon_id = None

    if hasattr(order_data, "coupon_code") and order_data.coupon_code:

        coupon = coupons_collection.find_one(
            {"code": order_data.coupon_code.upper(), "is_active": True}
        )

        if not coupon:
            raise HTTPException(status_code=400, detail="Invalid coupon code")

        # EXPIRY CHECK
        if coupon.get("expiry_date") and datetime.utcnow() > coupon["expiry_date"]:
            raise HTTPException(status_code=400, detail="Coupon expired")

        # USAGE LIMIT CHECK
        if coupon.get("max_usage") and coupon["used_count"] >= coupon["max_usage"]:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")

        # ONE TIME USER CHECK
        already_used = coupon_usage_collection.find_one(
            {"coupon_id": coupon["_id"], "user_id": user_object_id}
        )

        if already_used:
            raise HTTPException(status_code=400, detail="You already used this coupon")

        # DISCOUNT
        if coupon["discount_type"] == "percentage":

            discount_amount = total_amount * (coupon["discount_value"] / 100)

        else:
            discount_amount = coupon["discount_value"]

        discount_amount = min(discount_amount, total_amount)

        total_amount -= discount_amount

        coupon_id = coupon["_id"]

        # INCREASE USAGE
        coupons_collection.update_one(
            {"_id": coupon["_id"]}, {"$inc": {"used_count": 1}}
        )

        # STORE USAGE RECORD
        coupon_usage_collection.insert_one(
            {
                "coupon_id": coupon["_id"],
                "user_id": user_object_id,
                "used_at": datetime.utcnow(),
            }
        )

    # =========================
    #  REDUCE STOCK
    # =========================
    if order_data.payment_method == "cod":

     for item in order_data.items:

        products_collection.update_one(
            {
                "_id": ObjectId(item.product_id)
            },
            {
                "$inc": {
                    "stock": -item.quantity
                }
            }
        )

    # =========================
    #  CREATE ORDER
    # =========================
    status = "pending_payment" if order_data.payment_method == "card" else "placed"
    new_order = {
        "user_id": user_object_id,
        "name": order_data.name,
        "email": order_data.email,
        "phone": order_data.phone,
        "address": order_data.address.dict(),
        "items": order_items,
        "coupon_id": coupon_id,
        "original_total": original_total,
        "discount_amount": float(discount_amount),
        "total_amount": float(total_amount),
        "status": status,
        "created_at": datetime.utcnow(),
        # "paid_at": datetime.utcnow()
    }

    result = orders_collection.insert_one(new_order)
    db["cart"].delete_many({"user_id": str(user_id)})

    return {
        "message": "Order placed successfully",
        "order_id": str(result.inserted_id),
        "original_total": original_total,
        "discount_amount": float(discount_amount),
        "final_total": float(total_amount),
    }


# =========================
# 👤 USER ORDERS
# =========================
def get_user_orders(user_id: str):

    try:
        user_object_id = ObjectId(user_id)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    orders = list(
        orders_collection.find(
            {"user_id": user_object_id}
        )
    )

    for order in orders:

        updated_items = []

        for item in order["items"]:

            product = db["products"].find_one(
                {"_id": item["product_id"]}
            )

            if product:

                updated_items.append(
                    {
                        "product_id": str(item["product_id"]),
                        "name": product.get("name"),
                        "image": product.get("image"),
                        "price": product.get("price"),
                        "quantity": item["quantity"],
                    }
                )

        order["items"] = updated_items

    return serialize_mongo(orders)
# =========================
# 👑 ADMIN ALL ORDERS
# =========================
def get_all_orders():

    orders = list(orders_collection.find())

    return serialize_mongo(orders)
