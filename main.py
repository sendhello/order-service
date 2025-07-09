from contextlib import asynccontextmanager

from api import router as api_router
from core.settings import settings
from core.tracer import configure_tracer
from db import redis_db
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from middleware import required_request_id, exception_traceback_middleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from redis.asyncio import Redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_db.redis = Redis(host=settings.redis_host, port=settings.redis_port, db=0, decode_responses=True)
    yield

    await redis_db.redis.close()


app = FastAPI(
    lifespan=lifespan,
    title=settings.project_name,
    description="Order management service for courier delivery",
    version="1.0.0",
    docs_url="/api/orders/openapi",
    openapi_url="/api/orders/openapi.json",
    default_response_class=ORJSONResponse,
)

if settings.jaeger_trace:
    # Send telemetry to Jaeger
    configure_tracer()
    FastAPIInstrumentor.instrument_app(app)
    RedisInstrumentor().instrument()

if not settings.debug:
    # Make X-Request-Id header field mandatory
    app.middleware("http")(required_request_id)
else:
    # Enable detailed exception traceback in debug mode
    app.middleware("http")(exception_traceback_middleware)

app.include_router(api_router, prefix="/api")
