from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app import crud, models, schemas
from app.database import SessionLocal, engine
import logging
logger = logging.getLogger("uvicorn.error")
# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ALL_USERS = [
    {"user_id": "user1",        "status": "free",    "airport": "jfk"},
    {"user_id": "user2",        "status": "expired", "airport": "sfo"},
    {"user_id": "user3",        "status": "active",  "airport": "jfk"},
    {"user_id": "jfk-expired-1","status": "expired", "airport": "jfk"},
    {"user_id": "jfk-expired-2","status": "expired", "airport": "jfk"},
    {"user_id": "jfk-expired-3","status": "expired", "airport": "jfk"},
    {"user_id": "sfo-expired-1","status": "expired", "airport": "sfo"},
    {"user_id": "sfo-expired-2","status": "expired", "airport": "sfo"},
    {"user_id": "sfo-expired-3","status": "expired", "airport": "sfo"},
    {"user_id": "jfk-free-1",   "status": "free",    "airport": "jfk"},
    {"user_id": "jfk-free-2",   "status": "free",    "airport": "jfk"},
    {"user_id": "jfk-free-3",   "status": "free",    "airport": "jfk"},
    {"user_id": "sfo-free-1",   "status": "free",    "airport": "sfo"},
    {"user_id": "sfo-free-2",   "status": "free",    "airport": "sfo"},
    {"user_id": "sfo-free-3",   "status": "free",    "airport": "sfo"},
]

def populate_users(db: Session):
    for user_data in ALL_USERS:
        existing = crud.get_user_by_id(db, user_data["user_id"])
        if existing:
            existing.airport = user_data["airport"]
            existing.status = user_data["status"]
            db.commit()
        else:
            crud.create_user(db, schemas.UserBase(**user_data))
            logger.info(f"Created user: {user_data['user_id']}")

@router.get("/user")
def read_user(
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    requested_user_id = user_id or x_user_id
    if not requested_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    populate_users(db)
    user = crud.get_user_by_id(db, requested_user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"User '{requested_user_id}' not found")

    return {"user_id": user.user_id, "status": user.status, "airport": user.airport}
