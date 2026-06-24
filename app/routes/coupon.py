from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.schemas.coupon_schema import CreateCouponSchema, ValidateCouponSchema
from app.config.db import db
from app.middlewares.admin import require_admin

router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"]
)


# =========================
#  ADMIN CREATE COUPON
# =========================
@router.post("/admin/create", dependencies=[Depends(require_admin)])
def create_coupon(data: CreateCouponSchema):

    code = data.code.upper()

    existing = db["coupons"].find_one({"code": code})
    if existing:
        raise HTTPException(status_code=400, detail="Coupon already exists")

    if data.discount_type not in ["percentage", "fixed"]:
        raise HTTPException(status_code=400, detail="Invalid discount type")

    coupon = {
        "code": code,
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "max_usage": data.max_usage,
        "used_count": 0,
        "expiry_date": data.expiry_date,
        "is_active": True,
        "created_at": datetime.utcnow()
    }

    db["coupons"].insert_one(coupon)

    return {"message": "Coupon created successfully"}
#VALIDATE COUPON

from app.middlewares.auth import get_current_user

# =========================
#  VALIDATE COUPON
# =========================
@router.post("/validate")
def validate_coupon(
    data: ValidateCouponSchema,
    current_user=Depends(get_current_user)
):

    code = data.code.upper()
    cart_total = data.cart_total

    coupon = db["coupons"].find_one({
        "code": code,
        "is_active": True
    })

    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon")

    #  Expiry check
    if coupon.get("expiry_date") and datetime.utcnow() > coupon["expiry_date"]:
        raise HTTPException(status_code=400, detail="Coupon expired")

    #  Usage limit check
    if coupon.get("max_usage") and coupon["used_count"] >= coupon["max_usage"]:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")

    #  One-time per user check
    already_used = db["coupon_usages"].find_one({
        "coupon_id": coupon["_id"],
        "user_id": current_user["_id"]
    })

    if already_used:
        raise HTTPException(status_code=400, detail="You already used this coupon")

    #  Calculate discount
    if coupon["discount_type"] == "percentage":
        discount_amount = cart_total * (coupon["discount_value"] / 100)
    else:
        discount_amount = coupon["discount_value"]

    discount_amount = min(discount_amount, cart_total)
    final_total = cart_total - discount_amount

    return {
        "valid": True,
        "coupon_code": code,
        "discount_amount": round(discount_amount, 2),
        "final_total": round(final_total, 2)
    }
