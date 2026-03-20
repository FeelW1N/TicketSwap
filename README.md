# TicketSwap — платформа безопасной перепродажи электронных билетов

## Концепция

Ключевое отличие от Avito/ЮЛА: **атомарное переоформление** через API организатора.
После оплаты старый билет аннулируется, покупатель получает **новый** билет с его именем.

## Структура проекта

```
ticketswap/
├── backend/          # Flask API + Celery
│   ├── app/
│   │   ├── models/   # User, Event, Ticket, Listing, Order, Payment, ReissueRequest, AuditLog
│   │   ├── routes/   # auth, listings, orders, payments, tickets, events
│   │   ├── tasks/    # Celery: process_reissue, send_notification
│   │   └── services/ # StorageService (S3), OrganizerAdapter, audit
│   └── tests/
├── frontend/         # React + TypeScript + Tailwind
│   └── src/
│       ├── pages/    # Home, Listings, ListingDetail, Sell, Orders, OrderDetail, Login, Register
│       ├── api/      # axios-клиенты
│       └── store/    # Zustand (auth)
├── mock_organizer/   # Mock HTTP-сервер организатора
└── docker-compose.yml
```

## Стек

| Слой | Технологии |
|------|-----------|
| Backend | Flask 3.0, SQLAlchemy, PostgreSQL, Flask-JWT-Extended |
| Async | Celery + Redis |
| Платежи | Stripe Checkout |
| Файлы | AWS S3 (presigned URL) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand |

## Быстрый старт

### Локально

```bash
# 1. Backend
cd backend
cp .env.example .env   # заполните ключи Stripe, AWS
pip install -r requirements.txt
flask --app run db upgrade
python run.py

# 2. Celery worker
celery -A celery_worker.celery worker --loglevel=info

# 3. Mock Organizer
python mock_organizer/mock_organizer.py

# 4. Frontend
cd frontend
pnpm install
pnpm dev
```

### Docker

```bash
cp backend/.env.example backend/.env
docker-compose up --build
```

Сервисы:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Mock Organizer: http://localhost:8001

## API (основные эндпоинты)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Вход, получение JWT |
| GET | `/listings` | Список активных объявлений |
| POST | `/listings` | Публикация объявления (FR1) |
| POST | `/orders` | Создание заказа (FR3) |
| POST | `/payments/create` | Создание Stripe Checkout |
| POST | `/payments/webhook` | Stripe webhook → запуск reissue (FR4) |
| GET | `/orders/{id}` | Статус заказа + reissue (FR7) |
| GET | `/tickets/{id}/download` | Presigned URL на новый билет |

## Жизненный цикл

```
Listing: ACTIVE → BLOCKED → SOLD
Order:   PENDING_PAYMENT → PAID
Payment: CREATED → CONFIRMED
Reissue: PENDING → SUCCESS / FAILED
Ticket:  ACTIVE → REISSUED
```

## Тесты

```bash
cd backend
pytest tests/ -v
```
