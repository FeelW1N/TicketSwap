# TicketSwap — платформа безопасной перепродажи электронных билетов

## Концепция

Ключевое отличие от Avito/ЮЛА: **атомарное переоформление** через API организатора.
После оплаты старый билет аннулируется, покупатель получает **новый** билет с его именем — мошенничество с перепродажей одного билета нескольким людям исключено.

## Структура проекта

```
ticketswap/
├── backend/          # Flask API + Celery
│   ├── app/
│   │   ├── models/   # User, Event, Ticket, Listing, Order, Payment, ReissueRequest, AuditLog, PasswordResetToken
│   │   ├── routes/   # auth, listings, orders, payments, tickets, events, wallet
│   │   ├── tasks/    # Celery: process_reissue
│   │   └── services/ # StorageService (MinIO/S3), OrganizerAdapter, email, audit
│   └── tests/
├── frontend/         # React + TypeScript + Tailwind CSS
│   └── src/
│       ├── pages/    # Home, Listings, ListingDetail, Sell, Orders, OrderDetail, Login, Register, ForgotPassword, ResetPassword
│       ├── api/      # axios-клиенты
│       └── store/    # Zustand (auth)
├── mock_organizer/   # Mock HTTP-сервер организатора (порт 8001)
└── docker-compose.yml
```

## Стек

| Слой | Технологии |
|------|-----------|
| Backend | Flask 3.0, SQLAlchemy, PostgreSQL, Flask-JWT-Extended |
| Async | Celery + Redis |
| Платежи | YooKassa (в dev-режиме — автоподтверждение без реальных денег) |
| Файлы | MinIO (S3-совместимое, self-hosted), presigned URL |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand |
| Инфраструктура | Docker Compose (Podman-совместимо) |

## Быстрый старт

### Docker / Podman

```bash
docker-compose up --build
# или
podman-compose up --build
```

Сервисы:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Mock Organizer: http://localhost:8001
- MinIO UI: http://localhost:9001 (admin / minioadmin)

### Тестовые данные

```bash
docker exec ticketswap_backend_1 flask --app run seed
```

Создаёт 3 пользователей, 5 мероприятий, 10 билетов и 10 активных объявлений.

| Email | Пароль | Роль |
|-------|--------|------|
| seller@test.com | password1 | продавец |
| buyer@test.com | password1 | покупатель |
| admin@test.com | password1 | админ |

## API (основные эндпоинты)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Вход, получение JWT |
| POST | `/auth/forgot-password` | Запрос сброса пароля |
| POST | `/auth/reset-password` | Сброс пароля по токену |
| GET | `/listings` | Список активных объявлений |
| POST | `/listings` | Публикация объявления |
| POST | `/orders` | Создание заказа |
| POST | `/payments/create` | Оплата (YooKassa / debug auto-confirm) |
| GET | `/orders/{id}` | Статус заказа + переоформление |
| GET | `/tickets/{id}/download` | Presigned URL на новый билет |
| GET | `/wallet/balance` | Баланс продавца |
| POST | `/wallet/withdraw` | Вывод средств (мин. 100 ₽) |

## Жизненный цикл сделки

```
Listing: ACTIVE → BLOCKED → SOLD
Order:   PENDING_PAYMENT → PAID
Payment: CREATED → CONFIRMED
Reissue: PENDING → SUCCESS / FAILED
Ticket:  ACTIVE → REISSUED
```

После успешного переоформления продавец получает на внутренний кошелёк сумму продажи за вычетом 5% комиссии платформы.

## Тесты

```bash
cd backend
pytest tests/ -v
```
