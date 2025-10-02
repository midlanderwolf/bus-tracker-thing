from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from tracker.models import VehiclePosition, TrackingSession


class Command(BaseCommand):
    help = 'Clean up old tracking data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete data older than N days'
        )
        parser.add_argument(
            '--vehicle',
            type=str,
            help='Delete data for specific vehicle'
        )
        parser.add_argument(
            '--operator',
            type=str,
            help='Delete data for specific operator'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        days = options['days']
        vehicle_ref = options.get('vehicle')
        operator_ref = options.get('operator')
        dry_run = options['dry_run']
        force = options['force']

        cutoff = timezone.now() - timezone.timedelta(days=days)

        # Build queries
        positions_query = VehiclePosition.objects.filter(recorded_at_time__lt=cutoff)
        sessions_query = TrackingSession.objects.filter(start_time__lt=cutoff)

        if vehicle_ref:
            positions_query = positions_query.filter(vehicle_ref=vehicle_ref)
            sessions_query = sessions_query.filter(vehicle_ref=vehicle_ref)

        if operator_ref:
            positions_query = positions_query.filter(operator_ref=operator_ref)

        # Count records
        position_count = positions_query.count()
        session_count = sessions_query.count()

        # Display summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Found {position_count} vehicle positions and {session_count} tracking sessions "
                f"older than {days} days"
            )
        )

        if vehicle_ref:
            self.stdout.write(f"Filtered by vehicle: {vehicle_ref}")
        if operator_ref:
            self.stdout.write(f"Filtered by operator: {operator_ref}")

        if position_count == 0 and session_count == 0:
            self.stdout.write(self.style.WARNING("No data to clean up."))
            return

        # Confirmation
        if not force and not dry_run:
            confirm = input(
                f"This will permanently delete {position_count} positions and {session_count} sessions. "
                "Type 'yes' to continue: "
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING("Operation cancelled."))
                return

        # Execute deletion
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No data was deleted"))
        else:
            try:
                positions_deleted, _ = positions_query.delete()
                sessions_deleted, _ = sessions_query.delete()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully deleted {positions_deleted} vehicle positions "
                        f"and {sessions_deleted} tracking sessions"
                    )
                )
            except Exception as e:
                raise CommandError(f"Error during deletion: {e}")