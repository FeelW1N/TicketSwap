"""Адаптер к API организаторов мероприятий.

Реализует интерфейс взаимодействия:
- validate_ticket  — проверка действительности билета и принадлежности продавцу
- reissue_ticket   — атомарное переоформление (аннулирование старого + выпуск нового)

В прототипе используется Mock-реализация, которую можно заменить реальными адаптерами.
"""

import logging
import requests
from dataclasses import dataclass
from typing import Optional
from flask import current_app
from app.services.organizer_catalog import (
    get_event_data,
    get_ticket_face_value,
    list_events_data,
    list_organizers_data,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    owner_confirmed: bool
    face_value: Optional[float]
    event: Optional[dict] = None
    error_code: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None


@dataclass
class ReissueResult:
    success: bool
    new_external_ticket_id: Optional[str]
    new_ticket_file_url: Optional[str]  # временная ссылка от организатора
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class OrganizerInfo:
    id: str
    name: str


@dataclass
class OrganizerEventInfo:
    id: str
    title: str
    description: Optional[str]
    venue: Optional[str]
    city: Optional[str]
    event_date: str
    category: Optional[str]
    image_url: Optional[str]
    sample_ticket_ids: Optional[list[str]] = None


class OrganizerAdapter:
    """HTTP-адаптер к API организатора."""

    def list_organizers(self) -> list[OrganizerInfo]:
        base_url = current_app.config["ORGANIZER_API_BASE_URL"]
        api_key = current_app.config["ORGANIZER_API_KEY"]
        try:
            resp = requests.get(
                f"{base_url}/api/organizers",
                headers={"X-Api-Key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return [OrganizerInfo(**item) for item in resp.json().get("items", [])]
        except Exception as e:
            logger.warning("Organizer list_organizers failed: %s", e)
            raise RuntimeError("organizer catalog is unavailable") from e

    def list_events(self, organizer_id: str) -> list[OrganizerEventInfo]:
        base_url = current_app.config["ORGANIZER_API_BASE_URL"]
        api_key = current_app.config["ORGANIZER_API_KEY"]
        try:
            resp = requests.get(
                f"{base_url}/api/organizer/{organizer_id}/events",
                headers={"X-Api-Key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return [OrganizerEventInfo(**item) for item in resp.json().get("items", [])]
        except Exception as e:
            logger.warning(
                "Organizer list_events failed: organizer=%s error=%s", organizer_id, e
            )
            raise RuntimeError("organizer events are unavailable") from e

    def validate_ticket(
        self,
        organizer_id: str,
        external_event_id: str,
        external_ticket_id: str,
        seller_user_id: str,
    ) -> ValidationResult:
        base_url = current_app.config["ORGANIZER_API_BASE_URL"]
        api_key = current_app.config["ORGANIZER_API_KEY"]
        try:
            resp = requests.post(
                f"{base_url}/api/organizer/{organizer_id}/validateTicket",
                json={
                    "ticket_id": external_ticket_id,
                    "event_id": external_event_id,
                    "owner_id": seller_user_id,
                },
                headers={"X-Api-Key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return ValidationResult(
                is_valid=data.get("is_valid", False),
                owner_confirmed=data.get("owner_confirmed", False),
                face_value=data.get("face_value"),
                event=data.get("event"),
            )
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            try:
                err_data = e.response.json()
            except Exception:
                err_data = {}

            error_code = err_data.get("error_code")
            if not error_code:
                if status_code == 404:
                    error_code = "TICKET_NOT_FOUND"
                elif status_code == 422:
                    error_code = "EVENT_MISMATCH"
                else:
                    error_code = "VALIDATION_HTTP_ERROR"

            return ValidationResult(
                is_valid=False,
                owner_confirmed=False,
                face_value=None,
                event=None,
                error_code=error_code,
                status_code=status_code,
                error=err_data.get("error") or str(e),
            )
        except Exception as e:
            logger.warning("Organizer validate_ticket failed: %s", e)
            return ValidationResult(
                is_valid=False,
                owner_confirmed=False,
                face_value=None,
                event=None,
                error_code="VALIDATION_UNAVAILABLE",
                status_code=502,
                error=str(e),
            )

    def reissue_ticket(
        self,
        organizer_id: str,
        old_external_ticket_id: str,
        buyer_name: str,
        buyer_email: str,
    ) -> ReissueResult:
        base_url = current_app.config["ORGANIZER_API_BASE_URL"]
        api_key = current_app.config["ORGANIZER_API_KEY"]
        try:
            resp = requests.post(
                f"{base_url}/api/organizer/{organizer_id}/reissueTicket",
                json={
                    "old_ticket_id": old_external_ticket_id,
                    "new_owner_name": buyer_name,
                    "new_owner_email": buyer_email,
                },
                headers={"X-Api-Key": api_key},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return ReissueResult(
                success=True,
                new_external_ticket_id=data["new_ticket_id"],
                new_ticket_file_url=data.get("ticket_pdf_url"),
            )
        except requests.HTTPError as e:
            try:
                err_data = e.response.json()
            except Exception:
                err_data = {}
            return ReissueResult(
                success=False,
                new_external_ticket_id=None,
                new_ticket_file_url=None,
                error_code=err_data.get("error_code", "HTTP_ERROR"),
                error_message=str(e),
            )
        except Exception as e:
            return ReissueResult(
                success=False,
                new_external_ticket_id=None,
                new_ticket_file_url=None,
                error_code="NETWORK_ERROR",
                error_message=str(e),
            )


class MockOrganizerAdapter(OrganizerAdapter):
    """Mock-адаптер для разработки и тестирования."""

    def list_organizers(self) -> list[OrganizerInfo]:
        return [OrganizerInfo(**item) for item in list_organizers_data()]

    def list_events(self, organizer_id: str) -> list[OrganizerEventInfo]:
        return [OrganizerEventInfo(**item) for item in list_events_data(organizer_id)]

    def validate_ticket(
        self, organizer_id, external_event_id, external_ticket_id, seller_user_id
    ):
        logger.info(
            "[MOCK] validate_ticket: organizer=%s event=%s ticket=%s",
            organizer_id,
            external_event_id,
            external_ticket_id,
        )

        event = get_event_data(organizer_id, external_event_id)
        if not event:
            return ValidationResult(
                is_valid=False,
                owner_confirmed=False,
                face_value=None,
                event=None,
                error_code="EVENT_NOT_FOUND",
                status_code=404,
                error="event not found",
            )

        face_value = get_ticket_face_value(
            organizer_id, external_event_id, external_ticket_id
        )
        if face_value is None:
            # В тестовом режиме допускаем произвольный номер билета в рамках
            # существующего мероприятия, но сохраняем реалистичный номинал.
            sample_tickets = event.get("tickets", {})
            face_value = next(iter(sample_tickets.values()), 1500.0)

        return ValidationResult(
            is_valid=True,
            owner_confirmed=True,
            face_value=face_value,
            event={
                "id": external_event_id,
                "title": event["title"],
                "description": event.get("description"),
                "venue": event.get("venue"),
                "city": event.get("city"),
                "event_date": event["event_date"],
                "category": event.get("category"),
                "image_url": event.get("image_url"),
            },
        )

    def reissue_ticket(
        self, organizer_id, old_external_ticket_id, buyer_name, buyer_email
    ):
        import uuid as _uuid

        new_id = f"MOCK-{_uuid.uuid4().hex[:8].upper()}"
        logger.info(
            "[MOCK] reissue_ticket: organizer=%s old=%s → new=%s",
            organizer_id,
            old_external_ticket_id,
            new_id,
        )
        return ReissueResult(
            success=True,
            new_external_ticket_id=new_id,
            new_ticket_file_url=None,
        )


def get_organizer_adapter() -> OrganizerAdapter:
    """Фабрика адаптеров: Mock для dev, HTTP для prod."""
    use_mock = current_app.config.get("TESTING")
    if use_mock:
        return MockOrganizerAdapter()
    return OrganizerAdapter()
