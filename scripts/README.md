# scripts/

지금까지 작성한 `persona_eval_test_v2.py`, `persona_eval_ab_test.py`를 이 폴더로 옮기세요.

이 폴더는 **일회성 실험/검증용**입니다 (temperature, 프롬프트 문구를 빠르게 바꿔가며 터미널에서 돌려보는 용도).
반면 `app/`은 **서비스 코드**입니다 — 검증이 끝난 프롬프트/로직만 `app/prompts/`, `app/services/`로 옮겨서 정식으로 채택하세요.

즉 순서는:
1. `scripts/`에서 실험 → 결과 좋으면
2. `app/prompts/evaluate.py` 또는 `app/prompts/generate_variants.py`에 정식 반영 → API로 노출

`eval_results_*.json`도 결과물이니 이 폴더나 저장소 루트의 `results/` 폴더 등으로 옮겨서 정리해도 좋습니다.
