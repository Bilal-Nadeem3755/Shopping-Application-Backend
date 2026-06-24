from pydantic import BaseModel
from typing import Optional


class ProductCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int

    # NEW
    image: Optional[str] = None
    average_rating: Optional[float] = 0
    review_count: Optional[int] = 0


class ProductUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

    # NEW
    image: Optional[str] = None
    average_rating: Optional[float] = None
    review_count: Optional[int] = None