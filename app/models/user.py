from pydantic import BaseModel, EmailStr
from typing import Optional, List


# -----------------------------
# Address Schema (Reusable)
# -----------------------------
class Address(BaseModel):
    full_name: str
    phone: str
    city: str
    street: str
    postal_code: str
    country: str


# -----------------------------
# User Create Schema
# -----------------------------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


# -----------------------------
# User Update Schema
# -----------------------------
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


# -----------------------------
# Add Address Schema
# -----------------------------
class AddAddress(BaseModel):
    full_name: str
    phone: str
    city: str
    street: str
    postal_code: str
    country: str


# -----------------------------
# User Output Schema
# -----------------------------
class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    addresses: Optional[List[Address]] = []
