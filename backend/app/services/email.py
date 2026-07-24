import httpx

from app.core.config import settings


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={
            # onboarding@resend.dev works without verifying a custom domain --
            # fine for this volume, though verifying your own domain later
            # improves deliverability and looks more professional.
            "from": "NMCN CBT Prep <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Reset your NMCN CBT Prep password",
            "html": (
                "<p>Someone requested a password reset for your NMCN CBT Prep account.</p>"
                f"<p><a href='{reset_link}'>Click here to reset your password</a></p>"
                "<p>This link expires in 1 hour. If you didn't request this, you can safely "
                "ignore this email — your password will not be changed.</p>"
            ),
        },
        timeout=10.0,
    )
    response.raise_for_status()
