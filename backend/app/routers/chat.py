from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
from openai import OpenAI, AuthenticationError, RateLimitError, BadRequestError, APIError
import ldclient
from ldclient import Context
from ldai.client import LDAIClient, AICompletionConfigDefault
from app.database import SessionLocal
from app import crud

router = APIRouter()

openai_client = OpenAI(api_key=os.environ.get("OPENAI_ADMIN_KEY"))

FALLBACK_PROMPT = "You are a helpful assistant. Help the user make CLEAR subscription decisions."

class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/chat")
async def chat(request: Request, chat_request: ChatRequest):
    system_prompt = FALLBACK_PROMPT

    user_id = chat_request.user_id
    account_status = "unknown"
    airport = "unknown"

    db = SessionLocal()
    try:
        user = crud.get_user_by_id(db, user_id)
        if user:
            account_status = user.status or "unknown"
            airport = user.airport or "unknown"
    finally:
        db.close()

    try:
        aiclient = LDAIClient(ldclient.get())
        ld_context = Context.builder(user_id).kind("user").set("account_status", account_status).set("airport", airport).build()
        fallback_value = AICompletionConfigDefault(enabled=False)
        config = aiclient.completion_config(
            "clear-chat-assistant",
            ld_context,
            fallback_value,
            {"user_id": user_id, "account_status": account_status}
        )
        if (
            config
            and getattr(config, "enabled", False)
            and getattr(config, "messages", None)
            and len(config.messages) > 0
            and getattr(config.messages[0], "content", None)
        ):
            system_prompt = config.messages[0].content
            print(f"LD AI Config 'clear-chat-assistant' served: {system_prompt}")
        else:
            print("LD AI Config disabled or empty — using fallback prompt")
    except Exception as e:
        print(f"LaunchDarkly AI Config error — using fallback prompt: {e}")

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat_request.message}
            ]
        )
        reply = completion.choices[0].message.content
        return {"reply": reply}
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid OpenAI API key")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded")
    except BadRequestError:
        raise HTTPException(status_code=400, detail="Invalid request to OpenAI")
    except APIError as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
