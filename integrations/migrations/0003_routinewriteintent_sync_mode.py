import uuid

import django.db.models.deletion
from django.db import migrations, models

import core.validators


class Migration(migrations.Migration):
    dependencies = [('integrations', '0002_synclock_syncrun_high_water_at')]

    operations = [
        migrations.AlterField(
            model_name='syncrun',
            name='mode',
            field=models.CharField(
                choices=[
                    ('full', 'Full'),
                    ('incremental', 'Incremental'),
                    ('plans', 'Plans'),
                    ('validate', 'Validate'),
                    ('routine_create', 'Routine create'),
                ],
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name='RoutineWriteIntent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('payload', models.JSONField()),
                ('payload_hash', models.CharField(max_length=64)),
                ('state', models.CharField(choices=[('previewed', 'Previewed'), ('submitting', 'Submitting'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('unknown', 'Unknown'), ('expired', 'Expired')], default='previewed', max_length=16)),
                ('expires_at', models.DateTimeField(validators=[core.validators.validate_aware_datetime])),
                ('submitted_at', models.DateTimeField(blank=True, null=True, validators=[core.validators.validate_aware_datetime])),
                ('finished_at', models.DateTimeField(blank=True, null=True, validators=[core.validators.validate_aware_datetime])),
                ('external_routine_id', models.CharField(blank=True, max_length=255)),
                ('error_code', models.CharField(blank=True, max_length=64)),
                ('sanitized_error', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('hevy_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routine_write_intents', to='integrations.hevyaccount')),
            ],
        ),
        migrations.AddIndex(
            model_name='routinewriteintent',
            index=models.Index(fields=['hevy_account', 'state', 'created_at'], name='routine_intent_state_idx'),
        ),
    ]
