"""
Seed script: creates demo users and organizer-aligned demo inventory.

Usage (inside container):
    flask --app run seed

Or directly:
    python seed.py
"""

from datetime import datetime

from app import create_app
from app.extensions import db
from app.models.event import Event
from app.models.listing import Listing, ListingStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.services.organizer_catalog import CATALOG


DEMO_ORGANIZERS = {"redkassa", "concert-ru", "qtickets"}
LEGACY_DEMO_ORGANIZERS = {"org-1", "org-orders", "org-wallet"}

LISTING_CONFIG = {
    ("redkassa", "rk-bi2-2026", "RK-BI2-1001"): {
        "seat_info": "Сектор A, ряд 3, место 15",
        "list_for_sale": True,
        "price": 5500,
        "description": "Отличный обзор сцены. Продаю, потому что уезжаю.",
    },
    ("redkassa", "rk-bi2-2026", "RK-BI2-1002"): {
        "seat_info": "Сектор B, ряд 7, место 22",
        "list_for_sale": False,
    },
    ("redkassa", "rk-picnic-2026", "RK-PIC-2001"): {
        "seat_info": "Входной билет, зона фестиваля",
        "list_for_sale": True,
        "price": 3600,
        "description": "Обычный билет на полный день фестиваля.",
    },
    ("redkassa", "rk-picnic-2026", "RK-PIC-2002"): {
        "seat_info": "Улучшенный вход, fast track",
        "list_for_sale": False,
    },
    ("concert-ru", "cr-imagine-2026", "CR-ID-3001"): {
        "seat_info": "Партер, зона 1, место 8",
        "list_for_sale": True,
        "price": 8200,
        "description": "Партер, хороший угол к сцене.",
    },
    ("concert-ru", "cr-imagine-2026", "CR-ID-3002"): {
        "seat_info": "Партер, зона 2, место 11",
        "list_for_sale": False,
    },
    ("concert-ru", "cr-noize-2026", "CR-NZ-3101"): {
        "seat_info": "Танцпол",
        "list_for_sale": True,
        "price": 4300,
        "description": "Пойду на другой день тура, этот билет продаю.",
    },
    ("concert-ru", "cr-noize-2026", "CR-NZ-3102"): {
        "seat_info": "Балкон, ряд 2, место 4",
        "list_for_sale": False,
    },
    ("qtickets", "qt-cska-2026", "QT-CSKA-4001"): {
        "seat_info": "Трибуна Север, ряд 10, место 44",
        "list_for_sale": True,
        "price": 2700,
        "description": "Хорошее место на дерби, ближе к центру сектора.",
    },
    ("qtickets", "qt-cska-2026", "QT-CSKA-4002"): {
        "seat_info": "Трибуна Юг, ряд 6, место 18",
        "list_for_sale": False,
    },
    ("qtickets", "qt-hp-2026", "QT-HP-4101"): {
        "seat_info": "Партер, ряд 5, место 12",
        "list_for_sale": True,
        "price": 6400,
        "description": "Театральный билет, хорошие места по центру.",
    },
    ("qtickets", "qt-hp-2026", "QT-HP-4102"): {
        "seat_info": "Партер, ряд 7, место 9",
        "list_for_sale": False,
    },
}


def _catalog_events_data():
    items = []
    for organizer in CATALOG.values():
        for event in organizer["events"]:
            items.append(
                {
                    "organizer_id": organizer["id"],
                    "external_event_id": event["id"],
                    "title": event["title"],
                    "description": event.get("description"),
                    "venue": event.get("venue"),
                    "city": event.get("city"),
                    "event_date": event["event_date"],
                    "category": event.get("category"),
                }
            )
    return items


def _catalog_tickets_data():
    items = []
    for organizer in CATALOG.values():
        for event in organizer["events"]:
            for ticket_id, face_value in event.get("tickets", {}).items():
                config = LISTING_CONFIG.get(
                    (organizer["id"], event["id"], ticket_id), {}
                )
                items.append(
                    {
                        "organizer_id": organizer["id"],
                        "external_event_id": event["id"],
                        "external_ticket_id": ticket_id,
                        "seat_info": config.get("seat_info"),
                        "face_value": face_value,
                        "list_for_sale": config.get("list_for_sale", False),
                        "price": config.get("price"),
                        "description": config.get("description"),
                    }
                )
    return items


EVENTS_DATA = _catalog_events_data()
TICKETS_DATA = _catalog_tickets_data()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _upsert_demo_users() -> tuple[User, User, User, int]:
    users_created = 0

    seller = User.query.filter_by(email="seller@test.com").first()
    if not seller:
        seller = User(
            email="seller@test.com",
            full_name="Иван Продавцов",
            phone="+7 (999) 100-00-01",
        )
        seller.set_password("password1")
        db.session.add(seller)
        users_created += 1

    buyer = User.query.filter_by(email="buyer@test.com").first()
    if not buyer:
        buyer = User(
            email="buyer@test.com",
            full_name="Мария Покупателева",
            phone="+7 (999) 200-00-02",
        )
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
    return seller, buyer, admin, users_created


def _sync_demo_events() -> tuple[dict[tuple[str, str], Event], int]:
    events_created = 0
    events: dict[tuple[str, str], Event] = {}

    for event_data in EVENTS_DATA:
        key = (event_data["organizer_id"], event_data["external_event_id"])
        event = Event.query.filter_by(
            organizer_id=event_data["organizer_id"],
            external_event_id=event_data["external_event_id"],
        ).first()

        if not event:
            event = Event(
                organizer_id=event_data["organizer_id"],
                external_event_id=event_data["external_event_id"],
                title=event_data["title"],
                description=event_data["description"],
                venue=event_data["venue"],
                city=event_data["city"],
                event_date=_parse_dt(event_data["event_date"]),
                category=event_data["category"],
            )
            db.session.add(event)
            db.session.flush()
            events_created += 1
        else:
            event.title = event_data["title"]
            event.description = event_data["description"]
            event.venue = event_data["venue"]
            event.city = event_data["city"]
            event.event_date = _parse_dt(event_data["event_date"])
            event.category = event_data["category"]

        events[key] = event

    db.session.flush()
    return events, events_created


def _deactivate_stale_demo_inventory(
    seller: User, desired_seeded_ticket_ids: set[tuple[str, str]]
) -> int:
    stale_count = 0
    demo_organizers = DEMO_ORGANIZERS.union(LEGACY_DEMO_ORGANIZERS)

    stale_listings = (
        Listing.query.join(Ticket, Listing.ticket_id == Ticket.id)
        .join(Event, Listing.event_id == Event.id)
        .filter(Listing.seller_user_id == seller.id)
        .filter(Ticket.owner_user_id == seller.id)
        .filter(
            db.or_(
                Ticket.organizer_id.in_(demo_organizers),
                Event.organizer_id.in_(demo_organizers),
            )
        )
        .all()
    )

    for listing in stale_listings:
        key = (listing.ticket.organizer_id, listing.ticket.external_ticket_id)
        if key in desired_seeded_ticket_ids:
            continue
        if listing.status == ListingStatus.ACTIVE:
            listing.status = ListingStatus.BLOCKED
            stale_count += 1
        if listing.ticket.status == TicketStatus.ACTIVE:
            listing.ticket.status = TicketStatus.CANCELLED

    db.session.flush()
    return stale_count


def _sync_demo_tickets_and_listings(
    seller: User, events: dict[tuple[str, str], Event]
) -> tuple[int, int, int]:
    tickets_created = 0
    listings_created = 0
    listings_deactivated = 0

    desired_seeded_ticket_ids = {
        (ticket_data["organizer_id"], ticket_data["external_ticket_id"])
        for ticket_data in TICKETS_DATA
        if ticket_data.get("list_for_sale")
    }

    listings_deactivated = _deactivate_stale_demo_inventory(
        seller, desired_seeded_ticket_ids
    )

    for ticket_data in TICKETS_DATA:
        event = events[(ticket_data["organizer_id"], ticket_data["external_event_id"])]
        ticket = Ticket.query.filter_by(
            organizer_id=ticket_data["organizer_id"],
            external_ticket_id=ticket_data["external_ticket_id"],
        ).first()

        if not ticket:
            ticket = Ticket(
                organizer_id=ticket_data["organizer_id"],
                external_ticket_id=ticket_data["external_ticket_id"],
                owner_user_id=seller.id,
                event_id=event.id,
                seat_info=ticket_data["seat_info"],
                face_value=ticket_data["face_value"],
                status=TicketStatus.ACTIVE,
            )
            db.session.add(ticket)
            db.session.flush()
            tickets_created += 1
        else:
            ticket.owner_user_id = seller.id
            ticket.event_id = event.id
            ticket.seat_info = ticket_data["seat_info"]
            ticket.face_value = ticket_data["face_value"]
            ticket.status = TicketStatus.ACTIVE

        active_listing = Listing.query.filter_by(
            ticket_id=ticket.id,
            seller_user_id=seller.id,
            status=ListingStatus.ACTIVE,
        ).first()

        if ticket_data.get("list_for_sale"):
            if not active_listing:
                listing = Listing(
                    ticket_id=ticket.id,
                    event_id=event.id,
                    seller_user_id=seller.id,
                    price=ticket_data["price"],
                    description=ticket_data.get("description"),
                    status=ListingStatus.ACTIVE,
                )
                db.session.add(listing)
                listings_created += 1
            else:
                active_listing.event_id = event.id
                active_listing.price = ticket_data["price"]
                active_listing.description = ticket_data.get("description")
                active_listing.status = ListingStatus.ACTIVE
        else:
            if active_listing:
                active_listing.status = ListingStatus.BLOCKED

    db.session.flush()
    return tickets_created, listings_created, listings_deactivated


def run_seed():
    app = create_app()
    with app.app_context():
        seller, buyer, admin, users_created = _upsert_demo_users()
        events, events_created = _sync_demo_events()
        tickets_created, listings_created, listings_deactivated = (
            _sync_demo_tickets_and_listings(seller, events)
        )

        db.session.commit()

        listed_now = sum(1 for ticket in TICKETS_DATA if ticket.get("list_for_sale"))
        free_for_manual_demo = sum(
            1 for ticket in TICKETS_DATA if not ticket.get("list_for_sale")
        )

        print(
            f"✓ Seed done: {users_created} users, {events_created} events, "
            f"{tickets_created} tickets, {listings_created} listings created, "
            f"{listings_deactivated} stale listings deactivated"
        )
        print("  seller@test.com  / password1")
        print("  buyer@test.com   / password1")
        print("  admin@test.com   / password1")
        print(f"  Demo listings available now: {listed_now}")
        print(f"  Demo tickets left for manual sale flow: {free_for_manual_demo}")


def register_seed_command(app):
    @app.cli.command("seed")
    def seed_command():
        """Populate DB with demo data aligned with organizer mock API."""
        run_seed()


if __name__ == "__main__":
    run_seed()
