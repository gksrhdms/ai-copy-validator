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

# ⬇️⬇️⬇️ 여기를 기존 스크립트의 PERSONAS 내용으로 그대로 채우세요 ⬇️⬇️⬇️
PERSONAS = [
    {
        "name": "가성비 대학생",
        "demographic": "",       # 예: "20대 초반, 여"
        "spending_type": "",     # 예: "가성비형"
        "ad_literacy": "",       # 예: "냉소적 (광고를 잘 신뢰하지 않음)"
        "channel": "",           # 예: "인스타 릴스"
    },
    {
        "name": "트렌드 얼리어답터",
        "demographic": "",
        "spending_type": "",
        "ad_literacy": "",
        "channel": "",
    },
    {
        "name": "프리미엄 지향 직장인",
        "demographic": "",
        "spending_type": "",
        "ad_literacy": "",
        "channel": "",
    },
    {
        "name": "육아맘 실속파",
        "demographic": "",
        "spending_type": "",
        "ad_literacy": "",
        "channel": "",
    },
    {
        "name": "보수적 소비 중년",
        "demographic": "",
        "spending_type": "",
        "ad_literacy": "",
        "channel": "",
    },
    {
        "name": "얼리 시니어 온라인쇼퍼",
        "demographic": "",
        "spending_type": "",
        "ad_literacy": "",
        "channel": "",
    },
    {
        "name": "Z세대 트렌드세터",
        "demographic": "",
        "spending_type": "",
        "ad_literacy": "",
        "channel": "",
    },
    {
        "name": "실용주의 자영업자",
        "demographic": "",
        "spending_type": "",
        "ad_literacy": "",
        "channel": "",
    },
]
# ⬆️⬆️⬆️ 여기까지 ⬆️⬆️⬆️


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
