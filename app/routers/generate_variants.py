"""
app/routers/generate_variants.py

TODO: 아래 세 곳을 채우면 완성됩니다.
1. campaign_id가 없으면 campaigns 테이블에 새로 insert
2. call_llm_json 결과를 copy_variants 테이블에 insert (source='ai_generated')
3. 실패(status != 'ok') 처리 — 몇 번째 variant가 실패했는지 응답에 남길지 결정
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import GenerateVariantsRequest, GenerateVariantsResponse, VariantOut
from app.prompts.generate_variants import build_generate_variants_prompt
from app.services.llm_client import call_llm_json

router = APIRouter()


@router.post("/generate-variants", response_model=GenerateVariantsResponse)
def generate_variants(req: GenerateVariantsRequest, db: Session = Depends(get_db)):
    prompt = build_generate_variants_prompt(
        product_desc=req.product_desc,
        num_variants=req.num_variants,
        angles=req.angles,
    )

    parsed, status = call_llm_json(prompt, temperature=1.2)
    if status != "ok" or parsed is None:
        raise HTTPException(status_code=502, detail=f"LLM 호출 실패: {status}")

    # TODO: campaign_id 없으면 새로 생성
    campaign_id = req.campaign_id
    if campaign_id is None:
        row = db.execute(
            text(
                "INSERT INTO campaigns (name, product_desc) "
                "VALUES (:name, :desc) RETURNING id"
            ),
            {"name": req.product_desc[:50], "desc": req.product_desc},
        ).fetchone()
        campaign_id = row[0]
        db.commit()

    variants_out = []
    for v in parsed.get("variants", []):
        db.execute(
            text(
                "INSERT INTO copy_variants (campaign_id, label, content, angle, source) "
                "VALUES (:campaign_id, :label, :content, :angle, 'ai_generated')"
            ),
            {
                "campaign_id": campaign_id,
                "label": v["label"],
                "content": v["content"],
                "angle": v["angle"],
            },
        )
        variants_out.append(VariantOut(**v))
    db.commit()

    return GenerateVariantsResponse(campaign_id=campaign_id, variants=variants_out)
