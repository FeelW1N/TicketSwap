"""Сервис отправки email.

В DEBUG-режиме выводит письмо в лог и возвращает токен в ответе API.
В prod подключается через SMTP / SendGrid (достаточно вписать переменные окружения).
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, full_name: str, reset_token: str) -> None:
    """Отправляет письмо со ссылкой для сброса пароля."""
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    subject = "Сброс пароля — TicketSwap"
    body_text = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Для сброса пароля перейдите по ссылке:\n{reset_link}\n\n"
        f"Ссылка действительна 1 час.\n"
        f"Если вы не запрашивали сброс — просто проигнорируйте это письмо.\n\n"
        f"— Команда TicketSwap"
    )
    body_html = f"""
    <div style="font-family: sans-serif; max-width: 480px;">
      <h2>Сброс пароля</h2>
      <p>Здравствуйте, {full_name}!</p>
      <p>Для сброса пароля нажмите кнопку:</p>
      <a href="{reset_link}" style="display:inline-block;background:#2563eb;color:#fff;
         padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">
        Сбросить пароль
      </a>
      <p style="color:#6b7280;font-size:12px;margin-top:16px;">
        Ссылка действительна 1 час. Если вы не запрашивали сброс — проигнорируйте письмо.
      </p>
    </div>
    """

    smtp_host = current_app.config.get("SMTP_HOST")
    if not smtp_host:
        # Dev-режим: просто логируем
        logger.info(
            "[EMAIL] To: %s | Subject: %s | Reset link: %s",
            to_email, subject, reset_link,
        )
        return

    # Prod: отправка через SMTP
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = current_app.config.get("SMTP_FROM", "noreply@ticketswap.ru")
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, current_app.config.get("SMTP_PORT", 587)) as server:
            server.starttls()
            server.login(
                current_app.config["SMTP_USER"],
                current_app.config["SMTP_PASSWORD"],
            )
            server.sendmail(msg["From"], [to_email], msg.as_string())
        logger.info("[EMAIL] Sent password reset to %s", to_email)
    except Exception as e:
        logger.error("[EMAIL] Failed to send to %s: %s", to_email, e)
        raise
