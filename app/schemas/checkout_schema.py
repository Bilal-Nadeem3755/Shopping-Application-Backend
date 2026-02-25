from pydantic import BaseModel
from typing import Literal, Optional


class CheckoutSchema(BaseModel):
    payment_method: Literal["cod", "bank", "card"]
    coupon_code: Optional[str] = None
