"""
app/routers/evaluate.py

TODO:
1. persona_ids가 없으면 personas WHERE is_active=TRUE 전체 조회
2. 각 페르소나마다 call_llm_json 호출 (순차 or 병렬 — 리스크 노트의
   "병렬/배치 처리" 항목 참고해서 결정)
3. evaluations 테이블에 결과 insert (status 포함, api_error/parse_error도 기록)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import EvaluateRequest, EvaluateResponse, EvaluationOut
from app.prompts.evaluate import build_evaluate_prompt
from app.services.llm_client import call_llm_json

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest, db: Session = Depends(get_db)):
    variant_row = db.execute(
        text("SELECT id, content FROM copy_variants WHERE id = :id"),
        {"id": req.variant_id},
    ).fetchone()
    if variant_row is None:
        raise HTTPException(status_code=404, detail="variant_id를 찾을 수 없습니다.")

    if req.persona_ids:
        persona_rows = db.execute(
            text(
                "SELECT id, name, demographic, spending_type, ad_literacy, channel "
                "FROM personas WHERE id = ANY(:ids)"
            ),
            {"ids": req.persona_ids},
        ).mappings().all()
    else:
        persona_rows = db.execute(
            text(
                "SELECT id, name, demographic, spending_type, ad_literacy, channel "
                "FROM personas WHERE is_active = TRUE"
            )
        ).mappings().all()

    results = []
    for persona in persona_rows:
        prompt = build_evaluate_prompt(dict(persona), variant_row.content)
        parsed, status = call_llm_json(prompt, temperature=1.1)

        click_intent = parsed.get("click_intent") if parsed else None
        trust = parsed.get("trust") if parsed else None
        brand_fit = parsed.get("brand_fit") if parsed else None
        reasoning = parsed.get("reasoning") if parsed else None

        db.execute(
            text(
                "INSERT INTO evaluations "
                "(variant_id, persona_id, click_intent, trust, brand_fit, reasoning, status, model_name, temperature) "
                "VALUES (:variant_id, :persona_id, :click_intent, :trust, :brand_fit, :reasoning, :status, :model_name, :temperature)"
            ),
            {
                "variant_id": req.variant_id,
                "persona_id": persona["id"],
                "click_intent": click_intent,
                "trust": trust,
                "brand_fit": brand_fit,
                "reasoning": reasoning,
                "status": status,
                "model_name": "gemini-2.5-flash",
                "temperature": 1.1,
            },
        )

        results.append(
            EvaluationOut(
                persona_id=persona["id"],
                persona_name=persona["name"],
                click_intent=click_intent,
                trust=trust,
                brand_fit=brand_fit,
                reasoning=reasoning,
                status=status,
            )
        )

    db.commit()
    return EvaluateResponse(variant_id=req.variant_id, results=results)
