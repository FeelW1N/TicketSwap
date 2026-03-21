"""
Seed script: creates demo users, events, tickets and listings.

Usage (inside container):
    flask --app run seed

Or directly:
    python seed.py
"""
import click
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.event import Event
from app.models.ticket import Ticket, TicketStatus
from app.models.listing import Listing, ListingStatus


EVENTS_DATA = [
    {
        "title": "Би-2: тур «Горизонт событий»",
        "description": "Большой концерт группы Би-2 в Москве",
        "venue": "Лужники, Большая спортивная арена",
        "city": "Москва",
        "event_date": datetime.now(timezone.utc) + timedelta(days=30),
        "organizer_id": "org-1",
        "external_event_id": "bi2-moscow-2026",
        "category": "concert",
    },
    {
        "title": "Imagine Dragons — Live in Moscow",
        "description": "Первый концерт Imagine Dragons в Москве за 5 лет",
        "venue": "VTB Арена",
        "city": "Москва",
        "event_date": datetime.now(timezone.utc) + timedelta(days=45),
        "organizer_id": "org-1",
        "external_event_id": "imagine-dragons-2026",
        "category": "concert",
    },
    {
        "title": "ЦСКА vs Спартак — Российская Премьер-Лига",
        "description": "Дерби двух топ-клубов российского футбола",
        "venue": "ВЭБ Арена",
        "city": "Москва",
        "event_date": datetime.now(timezone.utc) + timedelta(days=14),
        "organizer_id": "org-1",
        "external_event_id": "cska-spartak-2026",
        "category": "sport",
    },
    {
        "title": "Гарри Поттер и проклятое дитя — МХТ им. Чехова",
        "description": "Бродвейская постановка на московской сцене",
        "venue": "МХТ им. А.П. Чехова",
        "city": "Москва",
        "event_date": datetime.now(timezone.utc) + timedelta(days=7),
        "organizer_id": "org-1",
        "external_event_id": "hp-cursed-child-2026",
        "category": "theatre",
    },
    {
        "title": "Пикник «Афиши» 2026",
        "description": "Главный летний фестиваль страны",
        "venue": "Коломенское",
        "city": "Москва",
        "event_date": datetime.now(timezone.utc) + timedelta(days=90),
        "organizer_id": "org-1",
        "external_event_id": "afisha-picnic-2026",
        "category": "festival",
    },
]

TICKETS_DATA = [
    # Би-2
    {"event_idx": 0, "external_ticket_id": "TKT-BI2-001", "seat_info": "Сектор A, ряд 3, место 15",  "face_value": 5000},
    {"event_idx": 0, "external_ticket_id": "TKT-BI2-002", "seat_info": "Сектор B, ряд 7, место 22",  "face_value": 3500},
    # Imagine Dragons
    {"event_idx": 1, "external_ticket_id": "TKT-ID-001",  "seat_info": "Партер, зона 1, место 8",     "face_value": 8000},
    {"event_idx": 1, "external_ticket_id": "TKT-ID-002",  "seat_info": "Балкон, ряд 2, место 14",     "face_value": 4500},
    {"event_idx": 1, "external_ticket_id": "TKT-ID-003",  "seat_info": "VIP, ряд 1, место 3",         "face_value": 15000},
    # ЦСКА vs Спартак
    {"event_idx": 2, "external_ticket_id": "TKT-CSKA-001","seat_info": "Трибуна Север, ряд 10, место 44", "face_value": 2500},
    {"event_idx": 2, "external_ticket_id": "TKT-CSKA-002","seat_info": "VIP-ложа, место 5",           "face_value": 12000},
    # Гарри Поттер
    {"event_idx": 3, "external_ticket_id": "TKT-HP-001",  "seat_info": "Партер, ряд 5, место 12",     "face_value": 6000},
    # Пикник Афиши
    {"event_idx": 4, "external_ticket_id": "TKT-PIC-001", "seat_info": "Однодневный пропуск",         "face_value": 3000},
    {"event_idx": 4, "external_ticket_id": "TKT-PIC-002", "seat_info": "VIP-пропуск",                 "face_value": 8000},
]

LISTINGS_DATA = [
    # event_idx, ticket_idx, price, description
    (0, 0,  5500, "Продаю из-за командировки. Место с отличным обзором."),
    (0, 1,  3800, None),
    (1, 2,  9000, "Партер, первый ряд зоны — видно весь сеттлист. Брал за 8000, продаю чуть выше."),
    (1, 3,  5000, "Балкон, хорошая акустика. Срочно."),
    (1, 4, 16000, "VIP-место с отдельным входом и фуршетом. Цена номинала."),
    (2, 5,  2800, None),
    (2, 6, 13500, "VIP-ложа с обслуживанием. Дерби — не пропустите."),
    (3, 7,  6500, "Театральная постановка мирового уровня. Осталось мало мест."),
    (4, 8,  3200, None),
    (4, 9,  8500, "VIP включает backstage-зону и встречу с артистами."),
]


def run_seed():
    app = create_app()
    with app.app_context():
        # ---- Пользователи ----
        users_created = 0
        seller = User.query.filter_by(email="seller@test.com").first()
        if not seller:
            seller = User(email="seller@test.com", full_name="Иван Продавцов", phone="+7 (999) 100-00-01")
            seller.set_password("password1")
            db.session.add(seller)
            users_created += 1

        buyer = User.query.filter_by(email="buyer@test.com").first()
        if not buyer:
            buyer = User(email="buyer@test.com", full_name="Мария Покупателева", phone="+7 (999) 200-00-02")
            buyer.set_password("password1")
            db.session.add(buyer)
            users_created += 1

        admin = User.query.filter_by(email="admin@test.com").first()
        if not admin:
            admin = User(email="admin@test.com", full_name="Администратор", role="admin")
            admin.set_password("password1")
            db.session.add(admin)
            users_created += 1

        db.session.flush()

        # ---- События ----
        events = []
        events_created = 0
        for ed in EVENTS_DATA:
            existing = Event.query.filter_by(
                organizer_id=ed["organizer_id"],
                external_event_id=ed["external_event_id"]
            ).first()
            if existing:
                events.append(existing)
            else:
                event = Event(**ed)
                db.session.add(event)
                db.session.flush()
                events.append(event)
                events_created += 1

        # ---- Билеты ----
        tickets = []
        tickets_created = 0
        for td in TICKETS_DATA:
            event = events[td["event_idx"]]
            existing = Ticket.query.filter_by(
                organizer_id=event.organizer_id,
                external_ticket_id=td["external_ticket_id"]
            ).first()
            if existing:
                tickets.append(existing)
            else:
                ticket = Ticket(
                    external_ticket_id=td["external_ticket_id"],
                    organizer_id=event.organizer_id,
                    owner_user_id=seller.id,
                    event_id=event.id,
                    seat_info=td["seat_info"],
                    face_value=td["face_value"],
                    status=TicketStatus.ACTIVE,
                )
                db.session.add(ticket)
                db.session.flush()
                tickets.append(ticket)
                tickets_created += 1

        # ---- Листинги ----
        listings_created = 0
        for event_idx, ticket_idx, price, desc in LISTINGS_DATA:
            ticket = tickets[ticket_idx]
            existing = Listing.query.filter_by(ticket_id=ticket.id, status=ListingStatus.ACTIVE).first()
            if not existing:
                listing = Listing(
                    ticket_id=ticket.id,
                    event_id=events[event_idx].id,
                    seller_user_id=seller.id,
                    price=price,
                    description=desc,
                    status=ListingStatus.ACTIVE,
                )
                db.session.add(listing)
                listings_created += 1

        db.session.commit()

        print(f"✓ Seed done: {users_created} users, {events_created} events, "
              f"{tickets_created} tickets, {listings_created} listings")
        print("  seller@test.com  / password1")
        print("  buyer@test.com   / password1")
        print("  admin@test.com   / password1")


def register_seed_command(app):
    @app.cli.command("seed")
    def seed_command():
        """Populate DB with demo data."""
        run_seed()


if __name__ == "__main__":
    run_seed()
