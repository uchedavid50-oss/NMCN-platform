from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"  # set to "production" on Railway

    database_url: str = "postgresql://nmcn_user:nmcn_pass@db:5432/nmcn_db"
    jwt_secret_key: str = "dev-only-change-this-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Comma-separated list, e.g. "https://your-frontend.up.railway.app,https://yourdomain.com"
    cors_allowed_origins: str = "http://localhost:3000"

    paystack_secret_key: str = ""
    paystack_base_url: str = "https://api.paystack.co"
    frontend_callback_url: str = "http://localhost:3000/payment/callback"

    google_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_thinking_level: str = "low"
    tutor_max_tokens: int = 1024

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
