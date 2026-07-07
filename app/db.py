"""
app/db.py — Supabase(Postgres) 연결 헬퍼.
이전에 루트에 만든 db.py와 동일하되, config.py의 settings를 사용하도록 정리한 버전입니다.
루트의 db.py는 이 파일로 대체하고 지워도 됩니다.
"""

from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

settings.validate()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
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
    """스크립트에서 with문으로 쓸 때용."""
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
    with engine.connect() as conn:
        tables = (
            conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )
            )
            .scalars()
            .all()
        )
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
