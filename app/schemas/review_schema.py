from pydantic import BaseModel, Field
from typing import Optional

class ReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    


class ReviewOut(BaseModel):
    id: str
    product_id: str
    user_id: str
    rating: int
    comment: Optional[str]
    
