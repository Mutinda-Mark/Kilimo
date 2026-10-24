import pytest

from app.config import (
    Settings,
    missing_production_settings,
    validate_environment_name,
    validate_production_settings,
)


def production_settings(
    **overrides,
):
    values = {
        "environment":
            "production",

        "database_url":
            "postgresql://example",

        "gemini_api_key":
            "test-gemini-key",

        "whatsapp_access_token":
            "test-access-token",

        "whatsapp_phone_number_id":
            "test-phone-id",

        "whatsapp_verify_token":
            "test-verify-token",

        "whatsapp_app_secret":
            "test-app-secret",

        "admin_api_token":
            "test-admin-token",
    }

    values.update(
        overrides
    )

    return Settings(
        _env_file=None,
        **values,
    )


def test_development_does_not_require_production_secrets():

    settings = Settings(
        _env_file=None,
        environment="development",
    )

    assert (
        missing_production_settings(
            settings
        )
        == []
    )

    validate_production_settings(
        settings
    )


def test_complete_production_configuration_is_valid():

    settings = production_settings()

    assert (
        missing_production_settings(
            settings
        )
        == []
    )

    validate_production_settings(
        settings
    )


def test_production_detects_missing_database_url():

    settings = production_settings(
        database_url="",
    )

    assert (
        "DATABASE_URL"
        in missing_production_settings(
            settings
        )
    )


def test_production_detects_missing_whatsapp_secret():

    settings = production_settings(
        whatsapp_app_secret="",
    )

    assert (
        "WHATSAPP_APP_SECRET"
        in missing_production_settings(
            settings
        )
    )


def test_production_detects_missing_admin_token():

    settings = production_settings(
        admin_api_token="",
    )

    assert (
        "ADMIN_API_TOKEN"
        in missing_production_settings(
            settings
        )
    )


def test_incomplete_production_configuration_fails():

    settings = production_settings(
        gemini_api_key="",
    )

    with pytest.raises(
        RuntimeError,
        match="Production configuration is incomplete",
    ):
        validate_production_settings(
            settings
        )


def test_unknown_environment_is_rejected():

    settings = Settings(
        _env_file=None,
        environment="something-strange",
    )

    with pytest.raises(
        RuntimeError,
        match="Invalid application environment",
    ):
        validate_environment_name(
            settings
        )