"""
Mock API организаторов — имитирует внешние системы для разработки.

Эндпоинты:
  GET  /api/organizers
  GET  /api/organizer/{organizer_id}/events
  POST /api/organizer/{organizer_id}/validateTicket
  POST /api/organizer/{organizer_id}/reissueTicket
"""

import json
import uuid
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer


CATALOG = {
    "redkassa": {
        "id": "redkassa",
        "name": "RedKassa",
        "events": [
            {
                "id": "rk-bi2-2026",
                "title": "Би-2: Горизонт событий",
                "description": "Большой концерт Би-2 в Лужниках",
                "venue": "Лужники",
                "city": "Москва",
                "event_date": "2026-07-20T19:00:00+03:00",
                "category": "concert",
                "image_url": None,
                "tickets": {
                    "RK-BI2-1001": 5000.0,
                    "RK-BI2-1002": 5200.0,
                    "RK-BI2-1003": 4700.0,
                },
            },
            {
                "id": "rk-picnic-2026",
                "title": "Пикник Афиши 2026",
                "description": "Летний фестиваль в Коломенском",
                "venue": "Коломенское",
                "city": "Москва",
                "event_date": "2026-08-15T14:00:00+03:00",
                "category": "festival",
                "image_url": None,
                "tickets": {
                    "RK-PIC-2001": 3500.0,
                    "RK-PIC-2002": 3900.0,
                },
            },
        ],
    },
    "concert-ru": {
        "id": "concert-ru",
        "name": "Concert.ru",
        "events": [
            {
                "id": "cr-imagine-2026",
                "title": "Imagine Dragons Live in Moscow",
                "description": "Большое шоу Imagine Dragons",
                "venue": "ВТБ Арена",
                "city": "Москва",
                "event_date": "2026-09-10T20:00:00+03:00",
                "category": "concert",
                "image_url": None,
                "tickets": {
                    "CR-ID-3001": 8000.0,
                    "CR-ID-3002": 7800.0,
                    "CR-ID-3003": 9200.0,
                },
            },
            {
                "id": "cr-noize-2026",
                "title": "Noize MC: Электрический тур",
                "description": "Концертный тур Noize MC",
                "venue": "Adrenaline Stadium",
                "city": "Москва",
                "event_date": "2026-10-05T19:30:00+03:00",
                "category": "concert",
                "image_url": None,
                "tickets": {
                    "CR-NZ-3101": 4200.0,
                    "CR-NZ-3102": 4500.0,
                },
            },
        ],
    },
    "qtickets": {
        "id": "qtickets",
        "name": "Qtickets",
        "events": [
            {
                "id": "qt-cska-2026",
                "title": "ЦСКА vs Спартак",
                "description": "Главное московское дерби",
                "venue": "ВЭБ Арена",
                "city": "Москва",
                "event_date": "2026-06-12T18:00:00+03:00",
                "category": "sport",
                "image_url": None,
                "tickets": {
                    "QT-CSKA-4001": 2500.0,
                    "QT-CSKA-4002": 2700.0,
                    "QT-CSKA-4003": 6000.0,
                },
            },
            {
                "id": "qt-hp-2026",
                "title": "Гарри Поттер и проклятое дитя",
                "description": "Театральная постановка",
                "venue": "МХТ им. Чехова",
                "city": "Москва",
                "event_date": "2026-05-18T19:00:00+03:00",
                "category": "theatre",
                "image_url": None,
                "tickets": {
                    "QT-HP-4101": 6200.0,
                    "QT-HP-4102": 6100.0,
                },
            },
        ],
    },
}


def _find_event(organizer_id: str, event_id: str):
    organizer = CATALOG.get(organizer_id)
    if not organizer:
        return None
    return next(
        (event for event in organizer["events"] if event["id"] == event_id), None
    )


def _find_ticket(organizer_id: str, ticket_id: str):
    organizer = CATALOG.get(organizer_id)
    if not organizer:
        return None, None
    for event in organizer["events"]:
        if ticket_id in event["tickets"]:
            return event, event["tickets"][ticket_id]
    return None, None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[MockOrganizer] {format % args}")

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parts = self.path.strip("/").split("/")

        if parts == ["api", "organizers"]:
            items = [{"id": org["id"], "name": org["name"]} for org in CATALOG.values()]
            self._send_json({"items": items})
            return

        if (
            len(parts) == 4
            and parts[:2] == ["api", "organizer"]
            and parts[3] == "events"
        ):
            organizer = CATALOG.get(parts[2])
            if not organizer:
                self._send_json({"error": "organizer not found"}, 404)
                return

            items = []
            for event in organizer["events"]:
                event_data = deepcopy(event)
                event_data["sample_ticket_ids"] = list(
                    event_data.get("tickets", {}).keys()
                )[:3]
                event_data.pop("tickets", None)
                items.append(event_data)
            self._send_json({"items": items})
            return

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        parts = self.path.strip("/").split("/")

        if (
            len(parts) == 4
            and parts[:2] == ["api", "organizer"]
            and parts[3] == "validateTicket"
        ):
            organizer_id = parts[2]
            body = self._read_body()
            ticket_id = body.get("ticket_id", "")
            event_id = body.get("event_id")

            event, face_value = _find_ticket(organizer_id, ticket_id)
            if not event:
                self._send_json(
                    {"is_valid": False, "owner_confirmed": False, "face_value": None},
                    404,
                )
                return

            if event_id and event["id"] != event_id:
                self._send_json(
                    {"is_valid": False, "owner_confirmed": False, "face_value": None},
                    422,
                )
                return

            self._send_json(
                {
                    "is_valid": True,
                    "owner_confirmed": True,
                    "face_value": face_value,
                    "event": {
                        "id": event["id"],
                        "title": event["title"],
                        "description": event["description"],
                        "venue": event["venue"],
                        "city": event["city"],
                        "event_date": event["event_date"],
                        "category": event["category"],
                        "image_url": event["image_url"],
                    },
                }
            )
            return

        if (
            len(parts) == 4
            and parts[:2] == ["api", "organizer"]
            and parts[3] == "reissueTicket"
        ):
            organizer_id = parts[2]
            body = self._read_body()
            old_id = body.get("old_ticket_id", "unknown")
            event, _ = _find_ticket(organizer_id, old_id)
            if not event:
                self._send_json(
                    {"error_code": "TICKET_NOT_FOUND", "error": "ticket not found"}, 404
                )
                return

            new_id = f"{organizer_id.upper()}-RE-{uuid.uuid4().hex[:8].upper()}"
            print(f"  Reissued: {old_id} -> {new_id} for {body.get('new_owner_email')}")
            self._send_json({"new_ticket_id": new_id, "ticket_pdf_url": None})
            return

        self._send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8001), Handler)
    print("Mock Organizer API running on port 8001")
    server.serve_forever()
