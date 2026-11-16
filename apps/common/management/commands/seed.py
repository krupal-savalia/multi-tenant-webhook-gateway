# apps/deliveries/management/commands/seed.py
import hashlib
import random
import secrets

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from faker import Faker

from apps.tenants.models import Tenant
from apps.endpoints.models import WebhookEndpoint
from apps.events.models import IncomingEvent
from apps.deliveries.models import DeliveryAttempt

fake = Faker()

EVENT_TYPES = ["order.paid", "user.created", "invoice.failed", "payment.succeeded"]
STATUSES = ["success", "failed", "pending", "exhausted"]
STATUS_WEIGHTS = [80, 12, 5, 3]


class Command(BaseCommand):
    help = "Seed fake data for EXPLAIN ANALYZE experiments"

    def add_arguments(self, parser):
        parser.add_argument("--events", type=int, default=100_000)
        parser.add_argument("--tenants", type=int, default=20)

    def handle(self, *args, **opts):
        n_events, n_tenants = opts["events"], opts["tenants"]
        if n_events < 0 or n_tenants < 1:
            raise CommandError("--events must be non-negative and --tenants must be at least 1")

        run_id = secrets.token_hex(4)

        # 1. Tenants
        tenants = []
        for i in range(n_tenants):
            raw_key = "wh_live_" + secrets.token_hex(16)
            tenants.append(Tenant(
                name=f"{fake.company()} {i}",          # name is unique
                slug=f"tenant-{run_id}-{i}",
                api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
                api_key_prefix=raw_key[:12],
            ))
        Tenant.objects.bulk_create(tenants)

        # 2. Endpoints: 3 per tenant, grouped by tenant for fast lookup
        endpoints_by_tenant = {}
        all_endpoints = []
        for t in tenants:
            eps = [
                WebhookEndpoint(
                    tenant=t,
                    target_url=f"https://example.com/hooks/{secrets.token_hex(4)}",
                    secret="whsec_" + secrets.token_hex(16),
                    subscribed_events=["*"],
                )
                for _ in range(3)
            ]
            endpoints_by_tenant[t.id] = eps
            all_endpoints += eps
        WebhookEndpoint.objects.bulk_create(all_endpoints)

        # 3. Events + attempts, in batches. UUIDs are generated in Python,
        #    so we don't need to re-read events from the DB.
        # Uneven weights: tenant 0 gets most traffic, like real life.
        weights = [50] + [1] * (n_tenants - 1)
        BATCH = 5000
        done = 0
        while done < n_events:
            size = min(BATCH, n_events - done)
            events, attempts = [], []
            for _ in range(size):
                t = random.choices(tenants, weights)[0]
                e = IncomingEvent(
                    tenant=t,
                    event_type=random.choice(EVENT_TYPES),
                    idempotency_key=secrets.token_hex(12),
                    payload={"data": {
                        "amount": random.randint(100, 50000),
                        "currency": "usd",
                        "email": fake.email(),
                    }},
                )
                events.append(e)
                status = random.choices(STATUSES, STATUS_WEIGHTS)[0]
                attempts.append(DeliveryAttempt(
                    tenant=t,
                    endpoint=random.choice(endpoints_by_tenant[t.id]),
                    event=e,
                    status=status,
                    attempt_number=random.randint(1, 5),
                    response_status_code=200 if status == "success" else random.choice([500, 502, 404]),
                    response_time_ms=random.randint(20, 3000),
                ))
            IncomingEvent.objects.bulk_create(events)
            DeliveryAttempt.objects.bulk_create(attempts)
            done += size
            self.stdout.write(f"{done}/{n_events}")

        # 4. Spread created_at over the last 30 days (auto_now_add made them all "now")
        with connection.cursor() as cur:
            for model in (IncomingEvent, DeliveryAttempt):
                cur.execute(
                    f"UPDATE {model._meta.db_table} "
                    f"SET created_at = now() - random() * interval '30 days'"
                )
            cur.execute("ANALYZE;")   # refresh planner statistics

        self.stdout.write(self.style.SUCCESS("Done"))
