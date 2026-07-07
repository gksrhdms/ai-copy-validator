"""
app/main.py — FastAPI 진입점.

실행:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.routers import evaluate, generate_variants

app = FastAPI(title="ai-copy-validator")

app.include_router(generate_variants.router, tags=["generate-variants"])
app.include_router(evaluate.router, tags=["evaluate"])


@app.get("/health")
def health():
    return {"status": "ok"}
