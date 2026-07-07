"""
app/models/schemas.py — FastAPI 요청/응답 바디 정의.
db_schema_draft.sql의 테이블 구조와 1:1로 맞춰뒀습니다.
"""

from typing import Optional

from pydantic import BaseModel, Field


# ── /generate-variants ──────────────────────────────
class GenerateVariantsRequest(BaseModel):
    campaign_id: Optional[int] = None  # 없으면 새 campaign을 만들어서 반환
    product_desc: str
    num_variants: int = Field(default=4, ge=1, le=8)
    angles: Optional[list[str]] = None  # 비우면 기본 4종(감성어필/근거중심/사회적증거/긴급성)


class VariantOut(BaseModel):
    label: str
    angle: str
    content: str


class GenerateVariantsResponse(BaseModel):
    campaign_id: int
    variants: list[VariantOut]


# ── /evaluate ────────────────────────────────────────
class EvaluateRequest(BaseModel):
    variant_id: int
    persona_ids: Optional[list[int]] = None  # 비우면 활성화된 페르소나 전체


class EvaluationOut(BaseModel):
    persona_id: int
    persona_name: str
    click_intent: Optional[int]
    trust: Optional[int]
    brand_fit: Optional[int]
    reasoning: Optional[str]
    status: str  # "ok" | "api_error" | "parse_error"


class EvaluateResponse(BaseModel):
    variant_id: int
    results: list[EvaluationOut]
