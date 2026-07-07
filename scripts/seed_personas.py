"""
scripts/seed_personas.py — 페르소나 8명을 personas 테이블에 INSERT합니다.

실행:
    python scripts/seed_personas.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.db import session_scope

# 원본 코드의 키(demo, spending)를 DB 컬럼명(demographic, spending_type)에 맞춰 옮겼습니다.
# id는 DB가 SERIAL로 자동 생성하므로 넣지 않습니다.
PERSONAS = [
    {"name": "가성비 대학생", "demographic": "20대 초반, 여", "spending_type": "가성비형", "ad_literacy": "냉소적 (광고를 잘 신뢰하지 않음)", "channel": "인스타 릴스"},
    {"name": "트렌드 얼리어답터", "demographic": "20대 후반, 성별무관", "spending_type": "트렌드추종형", "ad_literacy": "우호적 (신제품/신규 브랜드에 관심 많음)", "channel": "유튜브 숏폼"},
    {"name": "프리미엄 지향 직장인", "demographic": "30대 중반, 여", "spending_type": "프리미엄형", "ad_literacy": "중립적", "channel": "검색광고"},
    {"name": "육아맘 실속파", "demographic": "30대 후반, 여", "spending_type": "가성비형", "ad_literacy": "우호적 (정보성 광고 선호)", "channel": "인스타 릴스, 네이버 카페/블로그"},
    {"name": "보수적 소비 중년", "demographic": "40대 후반, 남", "spending_type": "프리미엄형 (브랜드 신뢰 중시)", "ad_literacy": "냉소적", "channel": "포털 배너"},
    {"name": "얼리 시니어 온라인쇼퍼", "demographic": "50대 초반, 여", "spending_type": "가성비형", "ad_literacy": "중립적 (최근 온라인쇼핑 입문)", "channel": "카카오톡 채널/배너"},
    {"name": "Z세대 트렌드세터", "demographic": "10대 후반~20대 초반", "spending_type": "트렌드추종형", "ad_literacy": "우호적이나 '광고 티' 나면 즉시 이탈", "channel": "틱톡/인스타 릴스"},
    {"name": "실용주의 자영업자", "demographic": "30~40대, 남", "spending_type": "가성비형 (ROI 민감)", "ad_literacy": "냉소적 (숫자/근거 없으면 무시)", "channel": "검색광고, 카카오톡비즈"},
]


def seed():
    with session_scope() as db:
        for p in PERSONAS:
            existing = db.execute(
                text("SELECT id FROM personas WHERE name = :name"),
                {"name": p["name"]},
            ).fetchone()
            if existing:
                print(f"↩️  '{p['name']}' 이미 존재 (id={existing[0]}) — 건너뜀")
                continue

            row = db.execute(
                text(
                    "INSERT INTO personas (name, demographic, spending_type, ad_literacy, channel) "
                    "VALUES (:name, :demographic, :spending_type, :ad_literacy, :channel) "
                    "RETURNING id"
                ),
                p,
            ).fetchone()
            print(f"✅ '{p['name']}' 추가 (id={row[0]})")


if __name__ == "__main__":
    seed()
