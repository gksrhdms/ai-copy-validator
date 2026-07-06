"""
db.py — Supabase(Postgres) 연결 헬퍼

필요 패키지:
    pip install sqlalchemy psycopg2-binary python-dotenv

사용 예 (FastAPI):

    from fastapi import Depends
    from db import get_db

    @app.get("/personas")
    def list_personas(db=Depends(get_db)):
        rows = db.execute(text("SELECT * FROM personas")).mappings().all()
        return list(rows)

단독 실행 시 (연결 테스트):
    python db.py
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL이 설정되지 않았습니다. .env 파일에 DATABASE_URL을 채워주세요 "
        "(.env.example 참고)."
    )

# pool_pre_ping=True: 커넥션이 죽어있으면(Supabase 무료 티어 일시정지 등)
# 자동으로 재연결을 시도합니다.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI Depends()용 제너레이터. 요청마다 세션을 열고 끝나면 닫습니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """스크립트(persona_eval_*.py 등)에서 with문으로 쓸 때용."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_connection() -> bool:
    """연결 + 스키마가 잘 반영됐는지 확인. personas 테이블 행 수를 출력합니다."""
    with engine.connect() as conn:
        tables = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        ).scalars().all()
        print("현재 public 스키마 테이블:", tables)

        expected = {"personas", "campaigns", "copy_variants", "evaluations"}
        missing = expected - set(tables)
        if missing:
            print(f"⚠️  누락된 테이블: {missing} — db_schema_draft.sql이 제대로 실행됐는지 확인하세요.")
            return False

        count = conn.execute(text("SELECT COUNT(*) FROM personas")).scalar()
        print(f"✅ 연결 성공. personas 테이블 현재 행 수: {count}")
        return True


if __name__ == "__main__":
    check_connection()
