import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import OwnerPreference


class Command(BaseCommand):
    help = 'Cria o único proprietário local do Tuxedo Fitness.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--email', default='')
        parser.add_argument('--no-input', action='store_true')

    def handle(self, *args, **options):
        user_model = get_user_model()
        if user_model.objects.exists():
            raise CommandError('A local owner already exists.')

        if options['no_input']:
            password = os.environ.get('TUXEDO_OWNER_PASSWORD', '')
        else:
            password = getpass.getpass('Senha: ')

        if not password:
            raise CommandError(
                'Informe a senha interativamente ou por TUXEDO_OWNER_PASSWORD.'
            )

        user = user_model(username=options['username'], email=options['email'])
        try:
            validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError(' '.join(error.messages)) from error
        user.set_password(password)
        user.save()
        OwnerPreference.objects.create(user=user)
        self.stdout.write(
            self.style.SUCCESS(f'Proprietário {user.username} criado.')
        )
