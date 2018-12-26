"""
Management utility to create operator on duty user.
"""
import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group, User
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS

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
            '--adminpassword',
            help='Specifies the password for the admin user.'
        )
        parser.add_argument(
            '--operatorpassword',
            help='Specifies the password for the admin user.'
        )
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is %s.'
                 % DEFAULT_DB_ALIAS,
        )

    def handle(self, *args, **options):
        admin_password = options['adminpassword']
        operator_duty_password = options['operatorpassword']
        database = options['database']

        # Create superuser
        self._create_superuser(admin_password)

        # Create operator on duty user
        self._create_operator_user(operator_duty_password, database)

        # Create operators group
        self._create_operators_group(database)

        # Create timer user
        self._create_timer_user(admin_password, database)

    def _create_superuser(self, password):
        while password is None or password.strip() is '':
            print('Creating admin user...')
            password = getpass.getpass()
            if password.strip() == '':
                self.stderr.write("Error: Blank passwords aren't allowed.")
                password = None
                continue

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                'admin', 'admin@fake-admin.com', password)
        else:
            self.stderr.write("Error: The admin user is already created")

    def _create_operator_user(self, password, database):
        user = None
        username = 'operator_on_duty'

        # Create user
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
                print('Creating operator on duty...')
                password = getpass.getpass()
                if password.strip() == '':
                    self.stderr.write("Error: Blank passwords aren't allowed.")
                    # Don't validate blank passwords.
                    continue
            user_data[PASSWORD_FIELD] = password

        if not User.objects.filter(username=username).exists():
            user = self.UserModel._default_manager.db_manager(
                database).create_user(**user_data)
            self._add_operator_on_duty_permissions(user)
        else:
            self.stderr.write(
                "Error: The user {} is already created".format(username)
            )
        return user

    def _create_timer_user(self, password, database):
        # Create user
        user = None
        user_data = {}
        user_data[self.UserModel.USERNAME_FIELD] = 'timer'
        user_data[PASSWORD_FIELD] = password

        if not User.objects.filter(username='timer').exists():
            user = self.UserModel._default_manager.db_manager(
                database).create_user(**user_data)

        return user

    def _create_operators_group(self, database):
        group, created = Group.objects.get_or_create(name=operators_group_name)
        permissions = Permission.objects.filter(codename__icontains='view_')
        for permission in permissions:
            group.permissions.add(permission)
        return group

    def _add_operator_on_duty_permissions(self, user):
        permissions = Permission.objects.filter(codename__icontains='view_')
        codenames = [permission.codename for permission in permissions]
        codenames += [
            'acknowledge_ticket',
            'add_shelveregistry',
            'unshelve_shelveregistry'
        ]
        for codename in codenames:
            user.user_permissions.add(
                Permission.objects.get(codename=codename)
            )
        return user
