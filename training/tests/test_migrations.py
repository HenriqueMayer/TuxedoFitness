from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MigrationStateTests(TransactionTestCase):
    def test_database_is_at_every_migration_leaf(self):
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())

        self.assertEqual(pending, [])
