import hashlib
import hmac

from app.whatsapp.webhook import (
    verify_webhook_signature,
)


TEST_SECRET = (
    "test-meta-app-secret"
)


def make_signature(
    body: bytes,
    secret: str = TEST_SECRET,
) -> str:

    digest = hmac.new(
        key=secret.encode(
            "utf-8"
        ),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return (
        f"sha256={digest}"
    )


def test_valid_signature_is_accepted():

    body = (
        b'{"object":"whatsapp_business_account"}'
    )

    signature = make_signature(
        body
    )

    assert (
        verify_webhook_signature(
            raw_body=body,
            signature_header=signature,
            app_secret=TEST_SECRET,
        )
        is True
    )


def test_modified_payload_invalidates_signature():

    original_body = (
        b'{"message":"hello"}'
    )

    modified_body = (
        b'{"message":"changed"}'
    )

    signature = make_signature(
        original_body
    )

    assert (
        verify_webhook_signature(
            raw_body=modified_body,
            signature_header=signature,
            app_secret=TEST_SECRET,
        )
        is False
    )


def test_wrong_secret_is_rejected():

    body = (
        b'{"message":"hello"}'
    )

    signature = make_signature(
        body
    )

    assert (
        verify_webhook_signature(
            raw_body=body,
            signature_header=signature,
            app_secret="wrong-secret",
        )
        is False
    )


def test_missing_signature_is_rejected():

    assert (
        verify_webhook_signature(
            raw_body=b"{}",
            signature_header=None,
            app_secret=TEST_SECRET,
        )
        is False
    )


def test_signature_without_sha256_prefix_is_rejected():

    body = b"{}"

    digest = hmac.new(
        key=TEST_SECRET.encode(
            "utf-8"
        ),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    assert (
        verify_webhook_signature(
            raw_body=body,
            signature_header=digest,
            app_secret=TEST_SECRET,
        )
        is False
    )


def test_short_signature_is_rejected():

    assert (
        verify_webhook_signature(
            raw_body=b"{}",
            signature_header="sha256=abcd",
            app_secret=TEST_SECRET,
        )
        is False
    )


def test_non_hex_signature_is_rejected():

    invalid_digest = (
        "z" * 64
    )

    assert (
        verify_webhook_signature(
            raw_body=b"{}",
            signature_header=(
                f"sha256={invalid_digest}"
            ),
            app_secret=TEST_SECRET,
        )
        is False
    )


def test_missing_app_secret_is_rejected():

    body = b"{}"

    signature = make_signature(
        body
    )

    assert (
        verify_webhook_signature(
            raw_body=body,
            signature_header=signature,
            app_secret="",
        )
        is False
    )