from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import plans, user, chat
from contextlib import asynccontextmanager
import ldclient
from ldclient.config import Config
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging
logger = logging.getLogger("uvicorn.error")

load_dotenv()

logger = logging.getLogger("uvicorn.error")

openai_client = OpenAI(api_key=os.environ.get("OPENAI_ADMIN_KEY"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    ldclient.set_config(Config(os.environ.get("LD_SDK_KEY")))
    ld_client = ldclient.get()
    app.state.ld = ld_client  # attach to app.state so routers can access it
    user_context = ldclient.ContextBuilder("unknown-user").kind("user").set("account_status", "unknown").set("airport", "unknown").build()
    all_flags = ld_client.all_flags_state(context=user_context)
    print("=== LaunchDarkly flags loaded ===")
    for flag_key, flag_value in all_flags.to_values_map().items():
        print(f"  {flag_key}: {flag_value}")
    print("=================================")
    logger.warning("LaunchDarkly client initialized with flags:")

    
    yield
    ld_client.close()  # clean shutdown — flushes any pending LD events



app = FastAPI(
    title="Plans API",
    description="API for managing subscription plans and user statuses",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware to allow front-end requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your front-end URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Plans API is running"}
