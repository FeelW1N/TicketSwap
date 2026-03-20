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

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    owner_confirmed: bool
    face_value: Optional[float]
    error: Optional[str] = None


@dataclass
class ReissueResult:
    success: bool
    new_external_ticket_id: Optional[str]
    new_ticket_file_url: Optional[str]  # временная ссылка от организатора
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class OrganizerAdapter:
    """HTTP-адаптер к API организатора."""

    def validate_ticket(
        self,
        organizer_id: str,
        external_ticket_id: str,
        seller_user_id: str,
    ) -> ValidationResult:
        base_url = current_app.config["ORGANIZER_API_BASE_URL"]
        api_key = current_app.config["ORGANIZER_API_KEY"]
        try:
            resp = requests.post(
                f"{base_url}/api/organizer/{organizer_id}/validateTicket",
                json={"ticket_id": external_ticket_id, "owner_id": seller_user_id},
                headers={"X-Api-Key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return ValidationResult(
                is_valid=data.get("is_valid", False),
                owner_confirmed=data.get("owner_confirmed", False),
                face_value=data.get("face_value"),
            )
        except Exception as e:
            logger.warning("Organizer validate_ticket failed: %s", e)
            return ValidationResult(is_valid=False, owner_confirmed=False, face_value=None, error=str(e))

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

    def validate_ticket(self, organizer_id, external_ticket_id, seller_user_id):
        logger.info("[MOCK] validate_ticket: organizer=%s ticket=%s", organizer_id, external_ticket_id)
        return ValidationResult(
            is_valid=True,
            owner_confirmed=True,
            face_value=1500.0,
        )

    def reissue_ticket(self, organizer_id, old_external_ticket_id, buyer_name, buyer_email):
        import uuid as _uuid
        new_id = f"MOCK-{_uuid.uuid4().hex[:8].upper()}"
        logger.info(
            "[MOCK] reissue_ticket: organizer=%s old=%s → new=%s",
            organizer_id, old_external_ticket_id, new_id,
        )
        return ReissueResult(
            success=True,
            new_external_ticket_id=new_id,
            new_ticket_file_url=None,
        )


def get_organizer_adapter() -> OrganizerAdapter:
    """Фабрика адаптеров: Mock для dev, HTTP для prod."""
    use_mock = current_app.config.get("TESTING") or current_app.config.get("DEBUG")
    if use_mock:
        return MockOrganizerAdapter()
    return OrganizerAdapter()
