"""Celery-задачи: переоформление билета и уведомления."""
import logging
import requests
from celery import shared_task
from app.extensions import db
from app.models.reissue import ReissueRequest, ReissueStatus
from app.models.order import Order, OrderStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.listing import Listing, ListingStatus
from app.services.organizer import get_organizer_adapter
from app.services.audit import log_event

logger = logging.getLogger(__name__)

MAX_REISSUE_ATTEMPTS = 3


@shared_task(bind=True, max_retries=MAX_REISSUE_ATTEMPTS, default_retry_delay=60)
def process_reissue(self, reissue_request_id: str) -> dict:
    """
    Асинхронная задача переоформления билета.
    1. Загружает данные заказа, билета, организатора.
    2. Вызывает API организатора /reissueTicket.
    3. При успехе — обновляет статусы и сохраняет новый билет.
    4. При ошибке — retries с экспоненциальным интервалом.

    Идемпотентна: повторный запуск при SUCCESS не изменяет состояние.
    """
    reissue = ReissueRequest.query.get(reissue_request_id)
    if reissue is None:
        logger.error("ReissueRequest %s not found", reissue_request_id)
        return {"status": "error", "reason": "not_found"}

    # Идемпотентность: не повторять завершённые операции
    if reissue.status == ReissueStatus.SUCCESS:
        logger.info("ReissueRequest %s already SUCCESS — skipping", reissue_request_id)
        return {"status": "already_done"}

    order = Order.query.get(reissue.order_id)
    ticket = Ticket.query.get(reissue.ticket_id)
    listing = Listing.query.get(order.listing_id)

    if order.status != OrderStatus.PAID:
        logger.warning("Order %s is not PAID — aborting reissue", order.id)
        return {"status": "error", "reason": "order_not_paid"}

    reissue.attempts += 1
    db.session.commit()

    buyer = order.buyer
    adapter = get_organizer_adapter()

    result = adapter.reissue_ticket(
        organizer_id=ticket.organizer_id,
        old_external_ticket_id=ticket.external_ticket_id,
        buyer_name=buyer.full_name,
        buyer_email=buyer.email,
    )

    if result.success:
        # Обновляем старый билет
        ticket.status = TicketStatus.REISSUED
        ticket.owner_user_id = buyer.id

        # Скачиваем новый файл билета от организатора и загружаем в S3 (если URL предоставлен)
        new_s3_key = None
        if result.new_ticket_file_url:
            try:
                from flask import current_app
                from app.services.storage import storage_service
                file_bytes = requests.get(result.new_ticket_file_url, timeout=30).content
                new_s3_key = storage_service.upload_ticket_file(
                    file_bytes, f"ticket_{result.new_external_ticket_id}.pdf", str(buyer.id)
                )
            except Exception as e:
                logger.warning("Failed to download/store new ticket file: %s", e)

        reissue.status = ReissueStatus.SUCCESS
        reissue.external_new_ticket_id = result.new_external_ticket_id
        reissue.new_ticket_s3_key = new_s3_key

        # Переводим листинг в SOLD
        listing.status = ListingStatus.SOLD

        db.session.commit()

        log_event(
            action="REISSUE_SUCCESS",
            entity_type="reissue",
            entity_id=str(reissue.id),
            user_id=str(buyer.id),
            details={"new_external_ticket_id": result.new_external_ticket_id},
        )

        send_notification.delay(
            user_id=str(buyer.id),
            event_type="REISSUE_SUCCESS",
            payload={
                "order_id": str(order.id),
                "new_ticket_id": result.new_external_ticket_id,
            },
        )
        return {"status": "success", "new_ticket_id": result.new_external_ticket_id}
    else:
        logger.warning(
            "Reissue failed for request %s: %s %s",
            reissue_request_id, result.error_code, result.error_message,
        )
        reissue.error_code = result.error_code
        reissue.error_message = result.error_message

        if reissue.attempts >= MAX_REISSUE_ATTEMPTS:
            reissue.status = ReissueStatus.FAILED
            db.session.commit()
            log_event(
                action="REISSUE_FAILED",
                entity_type="reissue",
                entity_id=str(reissue.id),
                details={"error_code": result.error_code, "attempts": reissue.attempts},
            )
            return {"status": "failed", "error_code": result.error_code}
        else:
            db.session.commit()
            raise self.retry(exc=Exception(result.error_message), countdown=60 * (2 ** reissue.attempts))


@shared_task
def send_notification(user_id: str, event_type: str, payload: dict) -> None:
    """Отправка уведомлений пользователю (email/push).
    В прототипе логирует событие; реальный канал подключается через адаптер.
    """
    logger.info("[NOTIFY] user=%s event=%s payload=%s", user_id, event_type, payload)
    # TODO: реализовать через SendGrid / Firebase / SMS-провайдер
