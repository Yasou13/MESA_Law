from apps.api.core.errors import (
    ProblemException,
    global_exception_handler,
    problem_exception_handler,
)
from apps.api.core.middleware import TraceMiddleware
from apps.api.routers import (
    documents,
    draft_studio,
    firms,
    matters,
    parser,
    qa,
    reviews,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MESA Law API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TraceMiddleware)
app.add_exception_handler(ProblemException, problem_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include all routers under /api/v1
app.include_router(firms.router, prefix="/api/v1")
app.include_router(matters.router, prefix="/api/v1/matters")
app.include_router(documents.router, prefix="/api/v1/documents")
app.include_router(parser.router, prefix="/api/v1/parser")
app.include_router(reviews.router, prefix="/api/v1/reviews")
app.include_router(draft_studio.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
