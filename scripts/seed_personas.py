"""
scripts/seed_personas.py — 기존 스크립트에 하드코딩되어 있던 PERSONAS를
personas 테이블에 INSERT합니다.

사용법:
1. 아래 PERSONAS 리스트를, persona_eval_test_v2.py (또는 ab_test.py)에 있는
   실제 PERSONAS 딕셔너리 내용을 그대로 복사해서 아래 형식에 맞게 채워 넣으세요.
   (키 이름이 name/demographic/spending_type/ad_literacy/channel과 다르면
    맞춰서 바꾸면 됩니다)
2. 실행:
       python scripts/seed_personas.py
3. 중복 실행해도 안전하도록 name 기준으로 이미 있으면 건너뜁니다.
"""

import sys
from pathlib import Path

# 레포 루트에서 실행하지 않아도 app 모듈을 찾을 수 있도록
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.db import session_scope

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


def seed():
    with session_scope() as db:
        for p in PERSONAS:
            if not p["demographic"]:
                print(f"⚠️  '{p['name']}' 필드가 비어있습니다 — 원본 스크립트에서 값을 채워주세요.")
                continue

            existing = db.execute(
                text("SELECT id FROM personas WHERE name = :name"),
                {"name": p["name"]},
            ).fetchone()
            if existing:
                print(f"↩️  '{p['name']}' 이미 존재 (id={existing[0]}) — 건너뜀")
                continue

            db.execute(
                text(
                    "INSERT INTO personas (name, demographic, spending_type, ad_literacy, channel) "
                    "VALUES (:name, :demographic, :spending_type, :ad_literacy, :channel)"
                ),
                p,
            )
            print(f"✅ '{p['name']}' 추가")


if __name__ == "__main__":
    seed()
