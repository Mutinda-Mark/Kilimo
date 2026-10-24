"""
Application configuration.

Loads values from a local .env file (see .env.example for the template).
Every other module should import `settings` from here rather than calling
os.environ directly - this keeps all configuration in one place and gives
us validation for free via pydantic.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database (Supabase Postgres + pgvector) ---
    # Empty default so the app can still start (in a "degraded" state)
    # before .env is configured - get_pool()/health_check() handle the
    # empty-string case gracefully.
    database_url: str = ""

    # --- OpenAI (Phase 3+) ---
    openai_api_key: str = ""

    # --- Google Gemini (Phase 3+) ---
    # --- Google Gemini ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"

    # --- WhatsApp Cloud API (Phase 6) ---
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_api_version: str = "v26.0"

    # --- App ---
    environment: str = "development"
    admin_api_token: str = ""

    # --- Public API rate limiting ---
    predict_rate_limit_requests: int = 10
    predict_rate_limit_window_seconds: int = 60

    chat_rate_limit_requests: int = 20
    chat_rate_limit_window_seconds: int = 60

    # --- Huey background task queue ---
    huey_db_path: str = "huey.db"

PRODUCTION_ENVIRONMENTS = frozenset(
    {
        "production",
        "prod",
    }
)

KNOWN_ENVIRONMENTS = frozenset(
    {
        "development",
        "dev",
        "local",
        "test",
        "testing",
        "production",
        "prod",
    }
)


def validate_environment_name(
    settings: Settings,
) -> None:
    environment = (
        settings.environment
        or ""
    ).strip().lower()

    if environment not in KNOWN_ENVIRONMENTS:
        raise RuntimeError(
            "Invalid application environment."
        )


def missing_production_settings(
    settings: Settings,
) -> list[str]:
    """
    Return names of required production settings that are empty.

    Secret values are intentionally never included.
    """

    environment = (
        settings.environment
        or ""
    ).strip().lower()

    if (
        environment
        not in PRODUCTION_ENVIRONMENTS
    ):
        return []

    required = {
        "DATABASE_URL":
            settings.database_url,

        "GEMINI_API_KEY":
            settings.gemini_api_key,

        "WHATSAPP_ACCESS_TOKEN":
            settings.whatsapp_access_token,

        "WHATSAPP_PHONE_NUMBER_ID":
            settings.whatsapp_phone_number_id,

        "WHATSAPP_VERIFY_TOKEN":
            settings.whatsapp_verify_token,

        "WHATSAPP_APP_SECRET":
            settings.whatsapp_app_secret,

        "ADMIN_API_TOKEN":
            settings.admin_api_token,
    }

    return [
        name
        for name, value in required.items()
        if not (
            value
            or ""
        ).strip()
    ]


def validate_production_settings(
    settings: Settings,
) -> None:
    validate_environment_name(
        settings
    )

    missing = (
        missing_production_settings(
            settings
        )
    )

    if not missing:
        return

    missing_names = ", ".join(
        sorted(missing)
    )

    raise RuntimeError(
        "Production configuration is incomplete. "
        f"Missing settings: {missing_names}"
    )

settings = Settings()
