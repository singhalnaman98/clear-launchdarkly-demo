from sqlalchemy.orm import Session
from app import models, schemas

def get_plans(db: Session):
    return db.query(models.Plan).all()

def get_plan_by_id(db: Session, plan_id: str):
    return db.query(models.Plan).filter(models.Plan.id == plan_id).first()

def get_user_by_id(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def create_plan(db: Session, plan: schemas.PlanBase):
    db_plan = models.Plan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def create_user(db: Session, user: schemas.UserBase):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
