"""
Management utility to create operator on duty user.
"""
import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group, User
from django.core.management.base import BaseCommand
from django.contrib.auth.password_validation import validate_password
from django.db import DEFAULT_DB_ALIAS
from django.core import exceptions

PASSWORD_FIELD = 'password'
username = 'operator_on_duty'
operators_group_name = 'operators'


class Command(BaseCommand):
    help = 'Creates the operator on duty user and the operators group'
    requires_migrations_checks = True
    stealth_options = ('stdin',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(
            self.UserModel.USERNAME_FIELD)

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            help='Specifies the password for the operator on duty user.'
        )
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is %s.'
                 % DEFAULT_DB_ALIAS,
        )

    def handle(self, *args, **options):
        password = options['password']
        database = options['database']

        # Create opertator on duty user
        user_data = {}
        user_data[self.UserModel.USERNAME_FIELD] = username
        user_data[PASSWORD_FIELD] = None

        fake_user_data = {}
        fake_user_data[self.UserModel.USERNAME_FIELD] = (
            self.username_field.remote_field.model(username)
            if self.username_field.remote_field else username
        )
        while user_data[PASSWORD_FIELD] is None:
            if password is None:
                password = getpass.getpass()
                if password.strip() == '':
                    self.stderr.write("Error: Blank passwords aren't allowed.")
                    # Don't validate blank passwords.
                    continue
            try:
                validate_password(password, self.UserModel(**fake_user_data))
            except exceptions.ValidationError as err:
                self.stderr.write('\n'.join(err.messages))
                response = input(
                    'Bypass password validation and create user anyway? [y/N]:'
                )
                if response.lower() != 'y':
                    continue
            user_data[PASSWORD_FIELD] = password

        if not User.objects.filter(username=username).exists():
            user = self.UserModel._default_manager.db_manager(
                database).create_user(**user_data)
            self._add_operator_on_duty_permissions(user)
        else:
            self.stderr.write("Error: The operator on duty is already created")

        # Create operators group
        self._create_operators_group(database)

    def _create_operators_group(self, database):
        return Group.objects.get_or_create(name=operators_group_name)

    def _add_operator_on_duty_permissions(self, user):
        permissions = [
            'acknowledge_ticket',
            'add_shelveregistry',
            'unshelve_shelveregistry'
        ]
        for permission in permissions:
            user.user_permissions.add(
                Permission.objects.get(codename=permission)
            )
        return user
