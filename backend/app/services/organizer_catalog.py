"""Единый demo-каталог организаторов для test/dev логики backend."""

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


def list_organizers_data():
    return [{"id": org["id"], "name": org["name"]} for org in CATALOG.values()]


def list_events_data(organizer_id: str):
    organizer = CATALOG.get(organizer_id)
    if not organizer:
        return []

    items = []
    for event in organizer["events"]:
        item = {k: v for k, v in event.items() if k != "tickets"}
        item["sample_ticket_ids"] = list(event.get("tickets", {}).keys())[:3]
        items.append(item)
    return items


def get_event_data(organizer_id: str, external_event_id: str):
    organizer = CATALOG.get(organizer_id)
    if not organizer:
        return None
    return next(
        (event for event in organizer["events"] if event["id"] == external_event_id),
        None,
    )


def get_ticket_face_value(
    organizer_id: str, external_event_id: str, external_ticket_id: str
):
    event = get_event_data(organizer_id, external_event_id)
    if not event:
        return None
    return event.get("tickets", {}).get(external_ticket_id)
