from django.core.management.base import BaseCommand, CommandError

from apps.deliveries.models import DeliveryAttempt, DeliveryStatus
from apps.endpoints.models import WebhookEndpoint
from apps.deliveries.tasks import test_redis_connection


class Command(BaseCommand):
    help = "Show the query plan for delivery attempts for a webhook endpoint"

    task = test_redis_connection.delay()
    print(task.id)

    # def add_arguments(self, parser):
    #     parser.add_argument("--endpoint-id")
    #     parser.add_argument(
    #         "--status",
    #         choices=[choice.value for choice in DeliveryStatus],
    #         default=DeliveryStatus.FAILED,
    #     )
    #     parser.add_argument("--limit", type=int, default=50)
    #     parser.add_argument("--analyze", action="store_true")

    def handle(self, *args, **options):
        pass
    #     limit = options["limit"]
    #     if limit < 1:
    #         raise CommandError("--limit must be at least 1")

    #     try:
    #         endpoint = (
    #             WebhookEndpoint.objects.get(pk=options["endpoint_id"])
    #             if options.get("endpoint_id")
    #             else WebhookEndpoint.objects.first()
    #         )
    #     except (WebhookEndpoint.DoesNotExist, ValueError):
    #         raise CommandError(f"Endpoint not found: {options['endpoint_id']}")

    #     if endpoint is None:
    #         raise CommandError("No webhook endpoints found. Run `manage.py seed` first.")

    #     queryset = (
    #         DeliveryAttempt.objects
    #         .filter(endpoint=endpoint, status=options["status"])
    #         .order_by("-created_at")[:limit]
    #     )
    #     self.stdout.write(f"Endpoint: {endpoint.pk}")
    #     self.stdout.write(f"Status: {options['status']}; limit: {limit}")
    #     self.stdout.write(queryset.explain(analyze=options["analyze"]))
