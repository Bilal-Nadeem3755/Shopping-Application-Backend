from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class AddressSchema(BaseModel):
    full_name: str
    phone: str
    city: str
    street: str
    postal_code: str
    country: str


class OrderItemSchema(BaseModel):
    product_id: str
    quantity: int


class CreateOrderSchema(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: AddressSchema
    items: List[OrderItemSchema]
    coupon_code: Optional[str] = None
