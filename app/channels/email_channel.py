"""Email notification channel via aiosmtplib."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


def _build_html(title: str, body: str, source_url: str | None = None) -> str:
    """Build a minimal HTML email body."""
    source_block = ""
    if source_url:
        source_block = f'<p style="margin-top:20px"><a href="{source_url}" style="color:#FF1A1A">View Source →</a></p>'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#0a0000;font-family:'Helvetica Neue',Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0000;padding:40px 0">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#100000;border:1px solid #2d0808;border-radius:12px;overflow:hidden">
        <tr>
          <td style="background:linear-gradient(135deg,#1a0000,#0d0000);padding:28px 36px;border-bottom:1px solid #2d0808">
            <span style="font-size:22px;font-weight:700;color:#F2E8E8">🔔 Claw<span style="color:#FF1A1A">Ping</span></span>
          </td>
        </tr>
        <tr>
          <td style="padding:36px">
            <h2 style="margin:0 0 16px;font-size:22px;color:#F2E8E8;font-weight:700">{title}</h2>
            <p style="margin:0;font-size:15px;color:#9A7070;line-height:1.65">{body}</p>
            {source_block}
          </td>
        </tr>
        <tr>
          <td style="padding:20px 36px;border-top:1px solid #1c0404">
            <p style="margin:0;font-size:12px;color:#4A2525">Part of the Claw Ecosystem 🐾 — You are receiving this because a ping was configured for your email.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


async def send_email(
    to: str,
    subject: str,
    body: str,
    title: str | None = None,
    source_url: str | None = None,
) -> bool:
    """
    Send an HTML-formatted notification email.

    Args:
        to:         Recipient email address.
        subject:    Email subject line.
        body:       Plain-text body (also used as HTML content).
        title:      Optional heading shown in the HTML email.
        source_url: Optional link appended to HTML body.

    Returns:
        True if delivery succeeded, False otherwise.
    """
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password]):
        logger.warning("SMTP not configured — skipping email delivery")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to

    # Plain text fallback
    msg.attach(MIMEText(body, "plain"))

    # HTML version
    html_body = _build_html(
        title=title or subject,
        body=body,
        source_url=source_url,
    )
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info("Email sent to %s", to)
        return True
    except aiosmtplib.SMTPException as e:
        logger.error("SMTP error sending to %s: %s", to, str(e))
        return False
    except Exception as e:
        logger.error("Email delivery failed: %s", str(e))
        return False


async def test_connection(to: str | None = None) -> bool:
    """Send a test email to verify SMTP is configured correctly."""
    target = to or settings.email_to
    if not target:
        return False
    return await send_email(
        to=target,
        subject="ClawPing — Connection Test",
        body="Your email notifications are configured correctly.",
        title="ClawPing ✓",
    )
