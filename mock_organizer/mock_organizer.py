"""
Mock API организатора — имитирует внешний сервис для разработки и тестов.
Эндпоинты:
  POST /api/organizer/{organizer_id}/validateTicket
  POST /api/organizer/{organizer_id}/reissueTicket
"""
import uuid
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

VALID_TICKETS = {}  # ticket_id -> {"face_value": float, "owner_id": str}


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

    def do_POST(self):
        parts = self.path.strip("/").split("/")
        # /api/organizer/{organizer_id}/validateTicket
        if len(parts) == 4 and parts[3] == "validateTicket":
            body = self._read_body()
            ticket_id = body.get("ticket_id", "")
            # Все билеты считаем валидными, face_value = 1500
            VALID_TICKETS[ticket_id] = {"face_value": 1500.0}
            self._send_json({"is_valid": True, "owner_confirmed": True, "face_value": 1500.0})

        # /api/organizer/{organizer_id}/reissueTicket
        elif len(parts) == 4 and parts[3] == "reissueTicket":
            body = self._read_body()
            old_id = body.get("old_ticket_id", "unknown")
            new_id = f"REISSUED-{uuid.uuid4().hex[:8].upper()}"
            print(f"  Reissued: {old_id} → {new_id} for {body.get('new_owner_email')}")
            self._send_json({"new_ticket_id": new_id, "ticket_pdf_url": None})
        else:
            self._send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8001), Handler)
    print("Mock Organizer API running on port 8001")
    server.serve_forever()
