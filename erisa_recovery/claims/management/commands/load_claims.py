import json
from pathlib import Path
import csv
from django.core.management.base import BaseCommand
from claims.models import Claim, ClaimDetail


class Command(BaseCommand):
    help = "Load claims and claim details from JSON files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--claims",
            type=str,
            required=True,
            help="Path to claims JSON or CSV file",
        )
        parser.add_argument(
            "--details",
            type=str,
            required=True,
            help="Path to claim details JSON or CSV file",
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["overwrite", "append"],
            default="overwrite",
            help="Whether to overwrite (default) or append data. Overwrite will delete all existing claims and details.",
        )

    def handle(self, *args, **options):
        claims_file = Path(options["claims"])
        details_file = Path(options["details"])
        mode = options["mode"]

        if not claims_file.exists() or not details_file.exists():
            self.stderr.write(self.style.ERROR("File(s) not found"))
            return

        if mode == "overwrite":
            ClaimDetail.objects.all().delete()
            Claim.objects.all().delete()
            self.stdout.write(self.style.WARNING("All existing claims and details deleted (overwrite mode)."))

        # Helper to load JSON or CSV
        def load_data(file_path):
            if file_path.suffix.lower() == ".json":
                with open(file_path, "r") as f:
                    return json.load(f)
            elif file_path.suffix.lower() == ".csv":
                with open(file_path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            else:
                raise Exception(f"Unsupported file type: {file_path.suffix}")

        claims_data = load_data(claims_file)
        for entry in claims_data:
            claim, created = Claim.objects.update_or_create(
                id=entry["id"],
                defaults={
                    "patient_name": entry["patient_name"],
                    "billed_amount": entry["billed_amount"],
                    "paid_amount": entry["paid_amount"],
                    "status": entry["status"],
                    "insurer_name": entry["insurer_name"],
                    "discharge_date": entry["discharge_date"],
                },
            )
            msg = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{msg} claim {claim.id}"))

        details_data = load_data(details_file)
        for entry in details_data:
            try:
                claim = Claim.objects.get(id=entry["claim_id"])
            except Claim.DoesNotExist:
                self.stderr.write(
                    self.style.WARNING(f"Skipping detail {entry.get('id', 'unknown')} - claim missing")
                )
                continue

            ClaimDetail.objects.update_or_create(
                claim=claim,
                defaults={
                    "denial_reason": entry["denial_reason"],
                    "cpt_codes": entry["cpt_codes"],
                },
            )
            self.stdout.write(self.style.SUCCESS(f"Linked details for claim {claim.id}"))

        self.stdout.write(self.style.SUCCESS("Data import complete."))
