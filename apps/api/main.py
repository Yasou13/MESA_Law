from apps.api.core.config import settings
from apps.api.core.errors import (
    ProblemException,
    global_exception_handler,
    problem_exception_handler,
)
from apps.api.core.middleware import (
    IdempotencyMiddleware,
    OriginEnforcementMiddleware,
    SecurityHeadersMiddleware,
    TraceMiddleware,
)
from apps.api.core.observability import setup_observability
from apps.api.core.ratelimit import limiter
from apps.api.routers import (
    audit,
    dashboard,
    deadlines,
    documents,
    domain_data,
    draft_studio,
    firms,
    matters,
    mesa_bindings,
    notifications,
    operations,
    parser,
    qa,
    research,
    reviews,
    session,
    system,
    users,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="MESA Law API", version="0.1.0")

setup_observability(app)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(OriginEnforcementMiddleware)

app.add_middleware(TraceMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.state.limiter = limiter
app.add_exception_handler(ProblemException, problem_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, global_exception_handler)


# Include all routers under /api/v1
@app.get("/")
async def root():
    return {"status": "ok", "message": "MESA Law API is running"}


app.include_router(firms.router, prefix="/api/v1")
app.include_router(session.router, prefix="/api/v1")
app.include_router(matters.router, prefix="/api/v1/matters")
app.include_router(mesa_bindings.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1/documents")
app.include_router(domain_data.router, prefix="/api/v1")
app.include_router(parser.router, prefix="/api/v1/parser")
app.include_router(reviews.router, prefix="/api/v1/reviews")
app.include_router(draft_studio.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1/research")
app.include_router(users.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(deadlines.router, prefix="/api/v1/deadlines")
app.include_router(dashboard.router)
app.include_router(system.router)
app.include_router(operations.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
