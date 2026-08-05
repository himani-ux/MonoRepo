from django.core.management.base import BaseCommand

from apps.help_assistant.services import status_payload, upsert_help_chunks_to_qdrant


class Command(BaseCommand):
    help = "Build or refresh the external Qdrant index for the file-backed VIMS Help assistant."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Index only the first N chunks. Useful for smoke tests.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Load docs and generate embeddings without writing points to Qdrant.",
        )

    def handle(self, *args, **options):
        status = status_payload()
        self.stdout.write(
            f"Loaded {status['documents_indexed']} documents and {status['chunks_indexed']} chunks."
        )
        result = upsert_help_chunks_to_qdrant(
            limit=options["limit"],
            dry_run=options["dry_run"],
        )
        self.stdout.write(self.style.SUCCESS(f"Qdrant indexing result: {result}"))
