from pydantic import BaseModel
from typing import Optional

class PlanBase(BaseModel):
    id: str
    name: str
    description: str
    price: str
    period: str
    was_price: Optional[str] = None
    badge_text: Optional[str] = None
    badge_type: Optional[str] = None
    featured: bool = False
    plan_type: str

class Plan(PlanBase):
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    user_id: str
    status: str
    airport: Optional[str] = None

class User(UserBase):
    class Config:
        from_attributes = True
