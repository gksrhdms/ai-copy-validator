"""
config.py — 환경변수를 한 곳에서 관리.
db.py, services/llm_client.py 등에서 os.environ을 직접 읽지 않고
여기서 import해서 쓰면, 나중에 값 하나 바뀔 때 여러 파일 안 뒤져도 됩니다.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    MODEL_NAME: str = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

    def validate(self) -> None:
        missing = [
            name
            for name in ("DATABASE_URL", "GEMINI_API_KEY")
            if not getattr(self, name)
        ]
        if missing:
            raise RuntimeError(
                f"필수 환경변수가 없습니다: {missing}. .env 파일을 확인하세요 (.env.example 참고)."
            )


settings = Settings()
