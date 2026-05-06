from fastapi import APIRouter, Depends, HTTPException, Request, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, models, schemas
from app.database import SessionLocal, engine
import ldclient
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

# Populate initial data if DB is empty
def populate_initial_data(db: Session):
    if db.query(models.Plan).count() == 0:
        initial_plans = [
            {
                "id": "annual",
                "name": "Annual membership",
                "description": "Full year of CLEAR access at airports nationwide",
                "price": "$189",
                "period": "/ year",
                "was_price": None,
                "badge_text": None,
                "badge_type": None,
                "featured": False,
                "plan_type": "annual"
            },
            {
                "id": "day",
                "name": "Day pass",
                "description": "Perfect for a single trip",
                "price": "$9",
                "period": "/ day",
                "was_price": "$16/day if annual",
                "badge_text": "New",
                "badge_type": "new",
                "featured": False,
                "plan_type": "flex"
            },
            {
                "id": "week",
                "name": "Week pass",
                "description": "Great for business travel",
                "price": "$29",
                "period": "/ week",
                "was_price": "$36/week if annual",
                "badge_text": "Most popular",
                "badge_type": "popular",
                "featured": True,
                "plan_type": "flex"
            },
            {
                "id": "month",
                "name": "Month pass",
                "description": "Frequent flyer flexibility",
                "price": "$49",
                "period": "/ month",
                "was_price": "$58/month if annual",
                "badge_text": "Save 16%",
                "badge_type": "save",
                "featured": False,
                "plan_type": "flex"
            },
            {
                "id": "annual-flex",
                "name": "Annual membership",
                "description": "Best value for regulars",
                "price": "$189",
                "period": "/ year",
                "was_price": None,
                "badge_text": None,
                "badge_type": None,
                "featured": False,
                "plan_type": "flex"
            }
        ]
        for plan_data in initial_plans:
            crud.create_plan(db, schemas.PlanBase(**plan_data))

@router.get("/plans")
def read_plans(
    request: Request,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Determine the user_id from query param or header
    requested_user_id = user_id or x_user_id
    
    if not requested_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    account_status = "unknown"
    airport = "unknown"
    user = crud.get_user_by_id(db, requested_user_id)
    if user:
        account_status = user.status
        airport = user.airport or "unknown"
        logger.info(f"Retrieved user {requested_user_id} with status: {account_status}, airport: {airport}")
    else:
        logger.warning(f"User {requested_user_id} not found, using unknown status/airport")
    
    # populate_initial_data(db)  # Ensure data is there
    plans = crud.get_plans(db)
    annual = None
    flex = []
    for plan in plans:
        if plan.plan_type == "annual":
            annual = plan
        elif plan.plan_type == "flex":
            flex.append(plan)
    
    # Evaluate LaunchDarkly flag with account_status targeting
    ld_client = request.app.state.ld
    
    # Create a context with the actual user_id as key
    context_builder = ldclient.ContextBuilder(requested_user_id)
    context_builder.kind("user")
    context_builder.set("account_status", account_status)
    context_builder.set("airport", airport)
    context = context_builder.build()
    
    flex_enabled = ld_client.variation("flex-subscription-enabled", context, False)
    logger.warning(f"LaunchDarkly flag 'flex-subscription-enabled' evaluated to: {flex_enabled} for user {requested_user_id} with account_status: {account_status}")
    
    if not flex_enabled:
        flex = []
    
    return {"annual": annual, "flex": flex}
