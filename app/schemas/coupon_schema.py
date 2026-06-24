from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CreateCouponSchema(BaseModel):
    code: str
    discount_type: str  # percentage | fixed
    discount_value: float
    max_usage: Optional[int] = None
    expiry_date: Optional[datetime] = None

# =========================
#  VALIDATE COUPON
# =========================
class ValidateCouponSchema(BaseModel):
    code: str
    cart_total: float    
