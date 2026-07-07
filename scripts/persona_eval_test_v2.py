import os
import json
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ── 설정 ──────────────────────────────────────────────
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. 코랩 가이드를 확인하세요.")

client = genai.Client(api_key=api_key)

# 트래픽 과부하가 덜한 표준 모델로 변경합니다.
MODEL_NAME = "gemini-2.5-flash"
REQUEST_DELAY_SEC = 10
MAX_RETRIES = 5

GEN_CONFIG = types.GenerateContentConfig(temperature=1.1)

# ── 테스트할 카피 ─────────────────────────────────────
AD_COPY = "지친 하루 끝, 5분 스킨케어로 내일의 피부를 준비하세요. 지금 첫 구매 시 30% 할인."

# ── 페르소나 정의 (8명) ─────────────────────────────────
PERSONAS = [
    {"id": 1, "name": "가성비 대학생", "demo": "20대 초반, 여", "spending": "가성비형", "ad_literacy": "냉소적 (광고를 잘 신뢰하지 않음)", "channel": "인스타 릴스"},
    {"id": 2, "name": "트렌드 얼리어답터", "demo": "20대 후반, 성별무관", "spending": "트렌드추종형", "ad_literacy": "우호적 (신제품/신규 브랜드에 관심 많음)", "channel": "유튜브 숏폼"},
    {"id": 3, "name": "프리미엄 지향 직장인", "demo": "30대 중반, 여", "spending": "프리미엄형", "ad_literacy": "중립적", "channel": "검색광고"},
    {"id": 4, "name": "육아맘 실속파", "demo": "30대 후반, 여", "spending": "가성비형", "ad_literacy": "우호적 (정보성 광고 선호)", "channel": "인스타 릴스, 네이버 카페/블로그"},
    {"id": 5, "name": "보수적 소비 중년", "demo": "40대 후반, 남", "spending": "프리미엄형 (브랜드 신뢰 중시)", "ad_literacy": "냉소적", "channel": "포털 배너"},
    {"id": 6, "name": "얼리 시니어 온라인쇼퍼", "demo": "50대 초반, 여", "spending": "가성비형", "ad_literacy": "중립적 (최근 온라인쇼핑 입문)", "channel": "카카오톡 채널/배너"},
    {"id": 7, "name": "Z세대 트렌드세터", "demo": "10대 후반~20대 초반", "spending": "트렌드추종형", "ad_literacy": "우호적이나 '광고 티' 나면 즉시 이탈", "channel": "틱톡/인스타 릴스"},
    {"id": 8, "name": "실용주의 자영업자", "demo": "30~40대, 남", "spending": "가성비형 (ROI 민감)", "ad_literacy": "냉소적 (숫자/근거 없으면 무시)", "channel": "검색광고, 카카오톡비즈"},
]

# ── 프롬프트 템플릿 ──────────────────────────────────────
SYSTEM_TEMPLATE = """당신은 아래 정의된 특정 소비자 페르소나 그 자체입니다. 이 사람의 나이, 말투, 소비 습관을 완전히 빙의해서 1인칭으로 생각하세요.

[페르소나]
- 이름: {name}
- 인구통계: {demo}
- 소비 성향: {spending}
- 광고 리터러시: {ad_literacy}
- 주로 접하는 채널: {channel}

[상황]
당신은 지금 평소처럼 {channel}을(를) 보다가, 아래 광고 카피를 우연히 마주쳤습니다.
이 채널의 특성(예: 릴스면 빠르게 스크롤 중, 검색광고면 능동적으로 뭔가 찾던 중)을 고려해서 반응하세요.

[광고 카피]
"{copy}"

점수는 아래 기준을 참고해서 매기세요. 다른 페르소나라면 다른 반응이 나오는 게 정상이니, 애매하면 중간값(3)으로 뭉개지 말고 이 페르소나라면 실제로 느낄 법한 극단값(1, 5)도 적극적으로 사용하세요.

- 1점: 전혀 안 끌림 / 광고인 걸 알자마자 스킵함
- 2점: 별 감흥 없음
- 3점: 그냥 그럼, 볼 수도 있고 안 볼 수도 있음
- 4점: 꽤 끌림, 더 보고 싶음
- 5점: 매우 끌림, 바로 클릭/구매 고려함

아래 JSON 형식으로만 답하세요. 다른 설명이나 마크다운 코드블록 없이 순수 JSON만 출력하세요.

{{
  "click_intent": <1~5 정수>,
  "trust": <1~5 정수>,
  "brand_fit": <1~5 정수>,
  "reasoning": "<이 페르소나의 말투로, 왜 이 점수를 줬는지 1~2문장. 가능하면 지금 보고 있는 채널({channel}) 상황을 언급할 것>"
}}
"""

def evaluate_persona(persona: dict, copy: str) -> dict:
    prompt = SYSTEM_TEMPLATE.format(
        name=persona["name"],
        demo=persona["demo"],
        spending=persona["spending"],
        ad_literacy=persona["ad_literacy"],
        channel=persona["channel"],
        copy=copy,
    )

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=GEN_CONFIG,
            )
            raw_text = response.text.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)

        except APIError as e:
            last_error = e
            # 429(할당량 초과) 또는 503(서버 일시적 과부하)이 발생하면 잠시 쉬었다가 재시도합니다.
            if e.code in [429, 503] or "RESOURCE_EXHAUSTED" in str(e).upper() or "UNAVAILABLE" in str(e).upper():
                wait = 15 * attempt
                print(f"  [{e.code} 에러 확인] 서버 혼잡 또는 제한으로 인해 {wait}초 대기 후 재시도합니다. ({attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            else:
                print(f"[API 에러 발생] {persona['name']}: {e}")
                break
        except json.JSONDecodeError:
            print(f"[파싱 실패] {persona['name']} 응답 비정상:\n{raw_text}\n")
            return {"click_intent": None, "trust": None, "brand_fit": None, "reasoning": "PARSE_ERROR"}
        except Exception as e:
            last_error = e
            print(f"[기타 에러] {persona['name']}: {e}")
            break

    print(f"[최종 실패] {persona['name']} 호출 불가능: {last_error}")
    return {"click_intent": None, "trust": None, "brand_fit": None, "reasoning": "API_ERROR"}


def run_single_test():
    print("── 단일 테스트 (키/쿼터 및 서버 확인용) ──")
    test_persona = PERSONAS[0]
    result = evaluate_persona(test_persona, AD_COPY)
    print(f"[{test_persona['name']}] 결과: {result}\n")
    return result.get("click_intent") is not None


def main():
    print(f"테스트 카피: {AD_COPY}\n")

    if not run_single_test():
        print("⚠ 단일 테스트가 실패했습니다. 구글 서버 트래픽이 여전히 혼잡하거나 API 키가 올바르지 않습니다.")
        return

    print("✓ 단일 테스트 성공. 나머지 페르소나 평가를 순차 진행합니다.\n")
    print("=" * 80)

    results = []
    for persona in PERSONAS:
        result = evaluate_persona(persona, AD_COPY)
        result["persona_name"] = persona["name"]
        results.append(result)

        print(f"[{persona['name']}] "
              f"클릭의도={result['click_intent']} "
              f"신뢰도={result['trust']} "
              f"적합도={result['brand_fit']}")
        print(f"  이유: {result['reasoning']}\n")

        time.sleep(REQUEST_DELAY_SEC)

    print("=" * 80)
    click_scores = [r["click_intent"] for r in results if r["click_intent"] is not None]
    if click_scores:
        print(f"클릭의도 점수 분포: {min(click_scores)} ~ {max(click_scores)} "
              f"(v2 적용 완료: 분산도가 개선되었는지 확인하세요.)")

    with open("eval_results_v2.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n결과 파일 저장 완료: eval_results_v2.json")


if __name__ == "__main__":
    main()
