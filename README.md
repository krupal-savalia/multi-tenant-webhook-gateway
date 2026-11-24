# Webhook Gateway

A Django-based webhook gateway for receiving, managing, and delivering webhook events for registered tenants.

## Project Status

This project is currently in the **development phase**. Foundation and endpoint-management features are implemented, while asynchronous delivery and production hardening are still in progress.

## Current Progress

### Implemented

- Django project structure with local and production settings
- PostgreSQL configuration through environment variables
- User registration, login, logout, and dashboard
- Tenant ownership and API-key generation
- Hashed API-key storage
- Webhook endpoint creation, listing, and soft deletion
- Tenant ownership protection for endpoints
- Endpoint URL and subscribed-event validation
- Wildcard subscriptions using `*`
- Incoming-event API foundation with API-key, event-type, idempotency, and JSON validation
- Optional endpoint targeting and event subscription matching
- Redis and Celery application configuration
- Basic Celery/Redis connectivity task
- Database models and migrations for tenants, endpoints, events, and delivery attempts

### In Progress

- Creating `DeliveryAttempt` records for accepted events
- Sending payloads to destination URLs
- Celery-based asynchronous delivery
- Retry and failure handling
- Delivery response and timing tracking
- Delivery history in the dashboard

### Planned

- Tenant rate limiting
- Request signatures and webhook verification
- Production SSRF protection before outbound delivery
- Endpoint secret encryption and rotation
- Background retry scheduling
- Automated API, security, idempotency, and delivery tests
- Production deployment configuration

## Current Workflow

1. A user registers and logs in.
2. A tenant is associated with the user.
3. The tenant generates an API key.
4. The tenant creates one or more webhook endpoints.
5. Each endpoint specifies a destination URL and subscribed event types.
6. An external service sends an event to the incoming-event API.
7. The API authenticates the tenant and validates the event.
8. The idempotency key prevents duplicate event processing.
9. The gateway selects the requested endpoint or all matching active endpoints.
10. The event is stored in PostgreSQL.
11. Celery will process delivery tasks through Redis.
12. Delivery results will be stored for monitoring and retries.

## API Endpoints

```text
GET    /api/v1/endpoints/
POST   /api/v1/endpoints/
DELETE /api/v1/endpoints/<endpoint_id>/
POST   /api/v1/events/
```

Incoming events require:

```text
X-API-Key: your-tenant-api-key
X-Event-Type: order.created
Idempotency-Key: unique-event-key
```

The optional `X-Endpoint` header targets one endpoint. If omitted, all active endpoints subscribed to the event type are selected.

## Local Setup

```powershell
.\anv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Start Celery separately:

```powershell
celery -A config worker --loglevel=INFO --pool=solo
```

Configure Redis in `.env`:

```env
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
```

## Important Note

Do not commit `.env`, API keys, endpoint secrets, database credentials, or other sensitive values. The project is not production-ready yet.
