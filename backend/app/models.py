from sqlalchemy import Column, String, Boolean
from app.database import Base

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(String)
    period = Column(String)
    was_price = Column(String, nullable=True)
    badge_text = Column(String, nullable=True)
    badge_type = Column(String, nullable=True)
    featured = Column(Boolean, default=False)
    plan_type = Column(String)  # 'annual' or 'flex'


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    status = Column(String)
    airport = Column(String, nullable=True)
