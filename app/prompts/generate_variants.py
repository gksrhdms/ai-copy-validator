"""
app/prompts/generate_variants.py — 카피 변형 생성 프롬프트.
(design 문서: generate_variants_prompt.md 참고)
"""

DEFAULT_ANGLES = ["감성어필", "근거중심", "사회적증거", "긴급성/할인"]

GENERATE_VARIANTS_PROMPT_TEMPLATE = """\
당신은 광고 카피라이터입니다. 아래 제품/캠페인 정보를 바탕으로,
서로 다른 설득 각도(angle)를 가진 광고 카피를 {num_variants}개 작성하세요.

[제품/캠페인 정보]
{product_desc}

[작성해야 할 각도 목록]
{angle_list}

[작성 규칙]
1. 각 카피는 위 각도 목록의 순서와 정확히 1:1로 대응해야 합니다.
   같은 각도인데 문구만 다른 카피를 여러 개 만들지 마세요.
2. 각 카피는 40자 내외의 실제 광고 카피 형태로 작성하세요.
   (해시태그, 이모지 남발 금지. 실제 매체에 게재 가능한 수준의 문장)
3. 각도끼리 실제로 뚜렷하게 구분되어야 합니다.
4. 과장/허위 효능(의학적 효과 단정 등)은 넣지 마세요.

아래 JSON 형식으로만 답하세요. 다른 설명이나 마크다운 코드블록 없이 순수 JSON만 출력하세요.

{{
  "variants": [
    {{
      "label": "<A, B, C ... 순서대로>",
      "angle": "<위 각도 목록 중 하나>",
      "content": "<실제 카피 문구>"
    }}
  ]
}}
"""


def build_generate_variants_prompt(
    product_desc: str, num_variants: int, angles: list[str] | None = None
) -> str:
    angles = angles or DEFAULT_ANGLES[:num_variants]
    angle_list = "\n".join(f"- {a}" for a in angles)
    return GENERATE_VARIANTS_PROMPT_TEMPLATE.format(
        product_desc=product_desc,
        num_variants=num_variants,
        angle_list=angle_list,
    )
