"""Application configuration.

Every value the app needs from the outside world is declared here, once.
Nothing else in the codebase reads os.environ directly - it imports `settings`.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed view of the .env file.

    pydantic-settings reads each field from an environment variable with the
    same (case-insensitive) name. A missing field with no default raises an
    error at startup rather than producing None at runtime.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Authentication ---
    # No default: the app must refuse to start rather than sign tokens with a
    # predictable key. A leaked JWT_SECRET_KEY lets anyone impersonate anyone.
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # --- AI / LLM provider (unused until Milestone 6) ---
    # Every one of these is read from .env so the provider and model can be
    # swapped without touching code (BRD section 21). AI_API_KEY stays on the
    # server and is never sent to React.
    AI_PROVIDER: str = "groq"
    AI_BASE_URL: str = "https://api.groq.com/openai/v1"
    AI_API_KEY: str = ""
    AI_MODEL: str = "openai/gpt-oss-120b"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 1024
    AI_TIMEOUT_SECONDS: float = 30.0

    @property
    def database_url(self) -> str:
        """SQLAlchemy connection URL, assembled from the parts above.

        The `+psycopg` suffix tells SQLAlchemy to use the psycopg 3 driver.
        Without it, SQLAlchemy defaults to psycopg2, which we did not install.
        """
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS is one comma-separated string; the middleware wants a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Build Settings once and reuse it.

    lru_cache means the .env file is parsed on first call only. Tests can
    override this dependency to inject a different configuration.
    """
    return Settings()


settings = get_settings()
