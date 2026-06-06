from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = "https://your-domain.com"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/tibbiyot_novatorlari"
    SYNC_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/tibbiyot_novatorlari"

    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "tibbiyot-files"
    S3_REGION: str = "us-east-1"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@tibbiyotnovatorlari.uz"

    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "https://your-domain.com,https://t.me"
    API_PREFIX: str = "/api/v1"

    EXPERT_IDS: str = ""  # comma-separated Telegram user IDs, e.g. "123456789,987654321"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def expert_ids_set(self) -> set:
        if not self.EXPERT_IDS.strip():
            return set()
        return {int(x.strip()) for x in self.EXPERT_IDS.split(",") if x.strip().isdigit()}


settings = Settings()
