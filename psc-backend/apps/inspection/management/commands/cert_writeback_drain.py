from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.certs.services.tracked_item_repository import TrackedItemRepository
from apps.inspection.audit.services.certs_writeback import drain_cert_writeback_outbox


class Command(BaseCommand):
    help = "Drain queued Audit external-audit Certs writeback outbox rows."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        result = drain_cert_writeback_outbox(
            repository=TrackedItemRepository(),
            limit=options["limit"],
        )
        self.stdout.write(
            "CERT_WRITEBACK_DRAIN "
            f"sent={result.sent} conflict={result.conflict} "
            f"retry={result.retry} dead_letter={result.dead_letter}"
        )
