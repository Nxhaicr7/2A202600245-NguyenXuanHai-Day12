"""
Production AI Agent — Kết hợp tất cả Day 12 concepts + Lab 11 Guardrails

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Stateless Rate limiting (Redis)
  ✅ Stateless Cost guard (Redis)
  ✅ Input validation (Pydantic)
  ✅ Input Guardrails (Injection & Topic filter)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
"""
import time
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.guardrails import detect_injection, topic_filter
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_and_record_cost

# Mock LLM
try:
    from utils.mock_llm import ask as llm_ask
except ImportError:
    # Fallback for local testing if utils is missing
    def llm_ask(q): return f"Mock response to: {q}"

# ─────────────────────────────────────────────────────────
# Logging & Storage
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# Try to ping redis for startup/readiness info
redis_connected = False
try:
    import redis
    redis_test = redis.from_url(settings.redis_url, decode_responses=True) if settings.redis_url else None
    if redis_test:
        redis_test.ping()
        redis_connected = True
        logger.info(json.dumps({"event": "redis_connected", "url": settings.redis_url}))
except Exception as e:
    logger.error(json.dumps({"event": "redis_error", "error": str(e)}))

START_TIME = time.time()
_is_ready = False

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "environment": settings.environment,
    }))
    _is_ready = True
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start = time.time()
    try:
        response: Response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        logger.error(json.dumps({"event": "exception", "error": str(e)}))
        raise

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    _key: str = Depends(verify_api_key),
):
    # 1. Rate limit
    check_rate_limit(_key[:8])

    # 2. Input Guardrails
    if detect_injection(body.question):
        logger.warning(json.dumps({"event": "guardrail_block", "reason": "injection"}))
        raise HTTPException(400, "Security block: Input pattern not allowed.")
    
    if topic_filter(body.question):
        logger.warning(json.dumps({"event": "guardrail_block", "reason": "off_topic"}))
        return AskResponse(
            question=body.question,
            answer="Xin lỗi, tôi chỉ có thể trả lời các câu hỏi liên quan đến dịch vụ ngân hàng VinBank.",
            model="guardrail",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # 3. Budget check
    input_tokens = len(body.question.split()) * 2
    check_and_record_cost(input_tokens, 0)

    # 4. LLM Call
    answer = llm_ask(body.question)

    # 5. Record response cost
    output_tokens = len(answer.split()) * 2
    check_and_record_cost(0, output_tokens)

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health", tags=["Operations"])
def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - START_TIME, 1),
        "redis": "connected" if redis_connected else "disconnected"
    }


@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    if not redis_connected and settings.redis_url:
        raise HTTPException(503, "Redis connection failed")
    return {"status": "ready"}


def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
