from pydantic import BaseModel, EmailStr
from typing import Optional

class UpdateUserSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
