from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "AdSight"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    debug: bool = True

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://adsight:adsight_dev_password@postgres:5432/adsight"

    # Elasticsearch
    elasticsearch_url: str = "http://elasticsearch:9200"
    es_ads_index: str = "ads"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO / S3
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "adsight-media"
    minio_use_ssl: bool = False

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Meta Ad Library
    meta_access_token: str = ""
    meta_api_version: str = "v19.0"

    # TikTok
    tiktok_api_base_url: str = "https://ads.tiktok.com/creative_radar_api/v1"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_origins_str: str = ""  # Comma-separated, overrides cors_origins if set

    @property
    def allowed_origins(self) -> list[str]:
        if self.cors_origins_str:
            return [o.strip() for o in self.cors_origins_str.split(",")]
        return self.cors_origins

    # Database pool
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Celery
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
