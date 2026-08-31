from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.services import prune_private_snapshots, prune_sync_runs


class Command(BaseCommand):
    help = 'Apply retention rules to private snapshots and synchronization logs.'

    def handle(self, *args, **options):
        owner = get_user_model().objects.order_by('pk').first()
        retention_days = 7
        if owner is not None:
            preference = getattr(owner, 'fitness_preferences', None)
            if preference is not None:
                retention_days = preference.snapshot_retention_days
        snapshots = prune_private_snapshots(retention_days)
        runs = prune_sync_runs()
        self.stdout.write(
            self.style.SUCCESS(
                f'Retention complete: snapshots={snapshots}, sync_runs={runs}.'
            )
        )
