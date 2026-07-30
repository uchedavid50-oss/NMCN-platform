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
    gemini_model: str = "gemini-3.1-flash-lite"
    tutor_max_tokens: int = 1024
    resend_api_key: str = ""
    # Base URL used to build password-reset links, e.g. "https://nmcn-platform-production.up.railway.app"
    frontend_url: str = "http://localhost:3000"

    # Entrance-exam AI provider fallback chain (backend/app/services/ai_router.py).
    # All optional -- a provider with no key configured is skipped instantly.
    groq_api_key: str = ""
    cerebras_api_key: str = ""
    sambanova_api_key: str = ""
    together_api_key: str = ""
    fireworks_api_key: str = ""
    mistral_api_key: str = ""
    cohere_api_key: str = ""
    deepinfra_api_key: str = ""
    cf_api_key: str = ""
    cf_account_id: str = ""
    deepseek_api_key: str = ""
    hf_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
