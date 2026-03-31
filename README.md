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
| Платежи | Внутренний кошелёк с учебным пополнением без реальных денег |
| Файлы | MinIO (S3-совместимое, self-hosted), presigned URL |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand |
| Инфраструктура | Docker Compose (Podman-совместимо) |

## Быстрый старт

### Docker / Podman

```bash
cp backend/.env.example backend/.env
docker compose up --build
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
docker compose run --rm backend flask --app run seed
```

Создаёт 3 пользователей и синхронизирует demo-данные под текущий каталог mock organizer:

- 6 мероприятий
- 15 demo-билетов
- 6 активных объявлений
- 9 свободных demo-билетов для ручного сценария продажи

| Email | Пароль | Роль |
|-------|--------|------|
| seller@test.com | password1 | продавец |
| buyer@test.com | password1 | покупатель |
| admin@test.com | password1 | админ |

### Demo flow продажи

Публикация объявления теперь идёт через пользовательский flow:

1. выбрать организатора;
2. выбрать мероприятие;
3. указать номер билета;
4. задать цену и опубликовать объявление.

Примеры demo-номеров для ручной проверки формы `Продать билет`:

- `RedKassa` -> `Би-2: Горизонт событий` -> `RK-BI2-1002`
- `Concert.ru` -> `Imagine Dragons Live in Moscow` -> `CR-ID-3002`
- `Qtickets` -> `ЦСКА vs Спартак` -> `QT-CSKA-4002`

## API (основные эндпоинты)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Вход, получение JWT |
| POST | `/auth/forgot-password` | Запрос сброса пароля |
| POST | `/auth/reset-password` | Сброс пароля по токену |
| GET | `/organizers` | Список доступных организаторов |
| GET | `/organizers/{id}/events` | Список мероприятий организатора |
| GET | `/listings` | Список активных объявлений |
| POST | `/listings` | Публикация объявления |
| POST | `/orders` | Создание заказа |
| POST | `/payments/create` | Оплата заказа из внутреннего кошелька |
| GET | `/orders/{id}` | Статус заказа + переоформление |
| GET | `/tickets/{id}/download` | Presigned URL на новый билет |
| GET | `/wallet/balance` | Текущий баланс кошелька |
| POST | `/wallet/topup` | Учебное пополнение кошелька |
| POST | `/wallet/withdraw` | Вывод средств (мин. 100 ₽) |

## Жизненный цикл сделки

```
Listing: ACTIVE → BLOCKED → SOLD
Order:   PENDING_PAYMENT → PAID
Payment: CREATED → CONFIRMED
Reissue: PENDING → SUCCESS / FAILED
Ticket:  ACTIVE → REISSUED
```

Покупатель оплачивает заказ из внутреннего кошелька. После успешного переоформления продавец получает на внутренний кошелёк сумму продажи за вычетом 5% комиссии платформы. Если переоформление не удалось, деньги возвращаются покупателю.

## Organizer model

Источник истины для мероприятий и проверки билета — organizer API.

- `/organizers` и `/organizers/{id}/events` отдают внешний каталог;
- локальная таблица `events` хранит cached-копии событий, уже известных платформе;
- при публикации объявления backend сам находит или создаёт локальный `Event` по данным организатора.

Маршрут `POST /events` оставлен как legacy/internal endpoint и не нужен обычному пользователю.

## Тесты

```bash
docker compose run --rm backend pytest tests -q
```
