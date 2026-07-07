"""
app/services/llm_client.py — Gemini 호출 공통 래퍼.

TODO: persona_eval_ab_test.py에 있던 재시도(backoff) 로직을 이 파일로 옮겨서
      evaluate 라우터와 generate-variants 라우터가 같은 함수를 재사용하게 만드세요.
      지금은 그 구조를 예시로 보여주는 스켈레톤입니다 — 실제 재시도 파라미터
      (MAX_RETRIES, 대기시간 공식 등)는 기존 스크립트 값 그대로 맞춰서 채워 넣으면 됩니다.

사용 예:
    result = call_llm_json(prompt=my_prompt, temperature=1.1)
    # result: (parsed_dict, status)  status는 "ok" | "api_error" | "parse_error"
"""

import json
import time
from typing import Any, Optional

import google.generativeai as genai

from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

MAX_RETRIES = 5
BASE_WAIT_SEC = 15


def _strip_json_fence(raw_text: str) -> str:
    return raw_text.replace("```json", "").replace("```", "").strip()


def call_llm_json(
    prompt: str,
    temperature: float = 1.1,
    model_name: Optional[str] = None,
) -> tuple[Optional[dict[str, Any]], str]:
    """
    LLM을 호출하고 JSON으로 파싱해서 돌려줍니다.
    반환값: (파싱된 dict 또는 None, status)
    status: "ok" | "api_error" | "parse_error"
    """
    model = genai.GenerativeModel(model_name or settings.MODEL_NAME)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"temperature": temperature},
            )
            raw_text = response.text
            break
        except Exception as e:
            error_str = str(e)
            is_retryable = any(
                keyword in error_str
                for keyword in ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE")
            )
            if is_retryable and attempt < MAX_RETRIES:
                time.sleep(BASE_WAIT_SEC * attempt)
                continue
            # 재시도 불가능한 에러이거나 마지막 시도까지 실패
            print(f"[llm_client] 최종 실패 (attempt={attempt}): {error_str}")
            return None, "api_error"
    else:
        return None, "api_error"

    try:
        parsed = json.loads(_strip_json_fence(raw_text))
        return parsed, "ok"
    except json.JSONDecodeError as e:
        print(f"[llm_client] JSON 파싱 실패: {e} / raw_text={raw_text[:200]}")
        return None, "parse_error"
