#!/usr/bin/env python3
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


def main():
    from training.tests.factories import create_account, create_template, create_workout

    account = create_account('e2e-owner')
    account.user.set_password('Synthetic-e2e-password-274')
    account.user.save(update_fields=['password'])
    template = create_template(
        account,
        title='Supino inclinado com barra e pausa controlada — título sintético longo',
    )
    create_workout(account, template)


if __name__ == '__main__':
    main()
