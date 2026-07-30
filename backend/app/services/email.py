import httpx

from app.core.config import settings


def _send_email(to_email: str, subject: str, html: str) -> None:
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={
            # onboarding@resend.dev works without verifying a custom domain --
            # fine for this volume, though verifying your own domain later
            # improves deliverability and looks more professional.
            "from": "Cura <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html,
        },
        timeout=10.0,
    )
    response.raise_for_status()


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    _send_email(
        to_email,
        "Reset your Cura password",
        (
            "<p>Someone requested a password reset for your Cura account.</p>"
            f"<p><a href='{reset_link}'>Click here to reset your password</a></p>"
            "<p>This link expires in 1 hour. If you didn't request this, you can safely "
            "ignore this email — your password will not be changed.</p>"
        ),
    )


def send_admin_signup_notification(new_user_email: str) -> None:
    """Best-effort -- callers must never let a failure here block the
    signup flow itself (see the try/except around this call in auth.py)."""
    if not settings.admin_notification_email:
        return
    _send_email(
        settings.admin_notification_email,
        "New Cura signup",
        f"<p>A new student just created an account: <strong>{new_user_email}</strong></p>",
    )


def send_admin_payment_notification(payer_email: str, amount_kobo: int, plan: str) -> None:
    """Best-effort -- callers must never let a failure here block payment
    webhook processing (see the try/except around this call in payments.py)."""
    if not settings.admin_notification_email:
        return
    naira = amount_kobo / 100
    _send_email(
        settings.admin_notification_email,
        "New Cura payment",
        (
            f"<p><strong>{payer_email}</strong> just paid for the "
            f"<strong>{plan}</strong> plan — ₦{naira:,.2f}.</p>"
        ),
    )
