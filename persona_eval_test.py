import os
import json
import time
from google import genai
from google.genai.errors import APIError  # 신규 SDK 통합 에러 클래스

# ── 설정 ──────────────────────────────────────────────
# 환경 변수로부터 API Key 로드
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. 코랩 가이드를 확인하세요.")

client = genai.Client(api_key=api_key)

# 무료 티어에서 가장 널널하고 안정적인 2.5 flash-lite 지정
MODEL_NAME = "gemini-2.5-flash-lite"  
REQUEST_DELAY_SEC = 10  # 무료 티어 안전 확보를 위해 대기 시간을 10초로 늘립니다.
MAX_RETRIES = 5         # 429 발생 시 재시도 횟수를 늘립니다.

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
SYSTEM_TEMPLATE = """당신은 아래 정의된 특정 소비자 페르소나입니다. 이 페르소나의 입장에서만 생각하고 답하세요.

[페르소나]
- 이름: {name}
- 인구통계: {demo}
- 소비 성향: {spending}
- 광고 리터러시: {ad_literacy}
- 주로 접하는 채널: {channel}

다음 광고 카피를 보고, 이 페르소나가 실제로 느낄 반응을 평가하세요.

[광고 카피]
"{copy}"

아래 JSON 형식으로만 답하세요. 다른 설명이나 마크다운 코드블록 없이 순수 JSON만 출력하세요.

{{
  "click_intent": <1~5 정수, 클릭/더보기를 누르고 싶은 정도>,
  "trust": <1~5 정수, 이 광고를 신뢰하는 정도>,
  "brand_fit": <1~5 정수, 이 카피가 본인 취향/니즈와 맞는 정도>,
  "reasoning": "<이 페르소나 입장에서 왜 이런 점수를 줬는지 1~2문장 이유>"
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
            # google-genai 신규 SDK 올바른 호출 방식 원칙 고수
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            raw_text = response.text.strip()
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)

        except APIError as e:
            last_error = e
            # 429 레이트 리밋 혹은 구조적 할당량 부족일 때 대기 후 재시도
            if e.code == 429 or "RESOURCE_EXHAUSTED" in str(e).upper():
                wait = 20 * attempt  # 대기 시간을 대폭 늘려 지수 백오프 적용
                print(f"  [429 Quota Exceeded] {wait}초 대기 후 재시도합니다. ({attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            else:
                print(f"[API 에러 발생] {persona['name']}: {e}")
                break
        except json.JSONDecodeError:
            print(f"[파싱 실패] {persona['name']} 응답 비정상:\n{raw_text}\n")
            return {"click_intent": None, "trust": None, "brand_fit": None, "reasoning": "PARSE_ERROR"}
        except Exception as e:
            # 예기치 못한 다른 에러로 스크립트가 뻗는 것을 방지
            last_error = e
            print(f"[기타 에러] {persona['name']}: {e}")
            break

    print(f"[최종 실패] {persona['name']} 호출 불가능: {last_error}")
    return {"click_intent": None, "trust": None, "brand_fit": None, "reasoning": "API_ERROR"}


def run_single_test():
    print("── 단일 테스트 (키/쿼터 확인용) ──")
    test_persona = PERSONAS[0]
    result = evaluate_persona(test_persona, AD_COPY)
    print(f"[{test_persona['name']}] 결과: {result}\n")
    return result.get("click_intent") is not None


def main():
    print(f"테스트 카피: {AD_COPY}\n")

    if not run_single_test():
        print("⚠ 단일 테스트가 실패했습니다. Google AI Studio에서 새 프로젝트를 생성하고 API 키를 새로 발급받아 교체하는 것을 추천합니다.")
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

        # 각 호출 사이에 확실한 텀을 주어 분당 제한(RPM) 우회
        time.sleep(REQUEST_DELAY_SEC)

    print("=" * 80)
    click_scores = [r["click_intent"] for r in results if r["click_intent"] is not None]
    if click_scores:
        print(f"클릭의도 점수 분포: {min(click_scores)} ~ {max(click_scores)} "
              f"(점수폭이 좁으면 페르소나 프롬프트를 보완하세요.)")

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n결과 파일 저장 완료: eval_results.json")

if __name__ == "__main__":
    main()