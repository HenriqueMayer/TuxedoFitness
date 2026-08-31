import django.db.models.deletion
from django.db import migrations, models

import core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='syncrun',
            name='high_water_at',
            field=models.DateTimeField(blank=True, null=True, validators=[core.validators.validate_aware_datetime]),
        ),
        migrations.CreateModel(
            name='SyncLock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False)),
                ('acquired_at', models.DateTimeField(blank=True, null=True, validators=[core.validators.validate_aware_datetime])),
                ('hevy_account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='sync_lock', to='integrations.hevyaccount')),
            ],
        ),
    ]
