# coding: utf-8
"""
Basic configuration for iffSamples

This configuration is the pure base, representing defaults. These values may be altered or expanded in several ways:
- For tests, the configuration is modified in tests/conftest.py.
- For local, interactive testing and demonstrations, the configuration is modified in demo.py.
- environment variables starting with the prefix SAMPLEDB_ will further override any hardcoded configuration data.
"""

import typing
import sys
import sqlalchemy

from .utils import generate_secret_key, load_environment_configuration

REQUIRED_CONFIG_KEYS: typing.Set[str] = {
    'SQLALCHEMY_DATABASE_URI',
    'MAIL_SERVER',
    'MAIL_SENDER',
    'CONTACT_EMAIL',
}

LDAP_REQUIRED_CONFIG_KEYS: typing.Set[str] = {
    'LDAP_NAME',
    'LDAP_SERVER',
    'LDAP_USER_BASE_DN',
    'LDAP_UID_FILTER',
    'LDAP_NAME_ATTRIBUTE',
    'LDAP_MAIL_ATTRIBUTE',
    'LDAP_OBJECT_DEF',
}

JUPYTERHUB_REQUIRED_CONFIG_KEYS: typing.Set[str] = {
    'JUPYTERHUB_URL'
}


def use_environment_configuration(env_prefix):
    """
    Uses configuration data from environment variables with a given prefix by setting the config modules variables.
    """
    config = load_environment_configuration(env_prefix)
    for name, value in config.items():
        globals()[name] = value


def check_config(
        config: typing.Mapping[str, typing.Any]
) -> typing.Dict[str, typing.Any]:
    """
    Check whether all neccessary configuration values are set.

    Print a warning if missing values will lead to reduced functionality.
    Exit if missing values will prevent SampleDB from working correctly.

    :param config: the config mapping
    """
    defined_config_keys = {
        key
        for key, value in config.items()
        if value is not None
    }

    show_config_info = False
    can_run = True

    internal_config = {}

    missing_config_keys = REQUIRED_CONFIG_KEYS - defined_config_keys

    if missing_config_keys:
        print(
            'Missing required configuration values:\n -',
            '\n - '.join(missing_config_keys),
            '\n',
            file=sys.stderr
        )
        can_run = False
        show_config_info = True

    missing_config_keys = LDAP_REQUIRED_CONFIG_KEYS - defined_config_keys
    if missing_config_keys:
        print(
            'LDAP authentication will be disabled, because the following '
            'configuration values are missing:\n -',
            '\n - '.join(missing_config_keys),
            '\n',
            file=sys.stderr
        )
        show_config_info = True

    missing_config_keys = JUPYTERHUB_REQUIRED_CONFIG_KEYS - defined_config_keys
    if missing_config_keys:
        print(
            'JupyterHub integration will be disabled, because the following '
            'configuration values are missing:\n -',
            '\n - '.join(missing_config_keys),
            '\n',
            file=sys.stderr
        )
        show_config_info = True

    admin_password_set = 'ADMIN_PASSWORD' in defined_config_keys
    admin_username_set = 'ADMIN_USERNAME' in defined_config_keys
    admin_email_set = 'ADMIN_EMAIL' in defined_config_keys
    if admin_password_set or admin_username_set or admin_email_set:
        if not admin_password_set:
            if admin_username_set and admin_email_set:
                print(
                    'ADMIN_USERNAME and ADMIN_EMAIL are set, but '
                    'ADMIN_PASSWORD is missing. No admin user will be created.'
                    '\n',
                    file=sys.stderr
                )
            elif admin_username_set:
                print(
                    'ADMIN_USERNAME is set, but ADMIN_PASSWORD is missing. No '
                    'admin user will be created.'
                    '\n',
                    file=sys.stderr
                )
            elif admin_email_set:
                print(
                    'ADMIN_EMAIL is set, but ADMIN_PASSWORD is missing. No '
                    'admin user will be created.'
                    '\n',
                    file=sys.stderr
                )
        elif config['ADMIN_PASSWORD'] == '':
            print(
                'ADMIN_PASSWORD is an empty string. No admin user will be '
                'created.'
                '\n',
                file=sys.stderr
            )
        elif len(config['ADMIN_PASSWORD']) < 8:
            print(
                'ADMIN_PASSWORD is too short. No admin user will be created.'
                '\n',
                file=sys.stderr
            )
        elif can_run:
            engine = sqlalchemy.create_engine(config['SQLALCHEMY_DATABASE_URI'])
            user_table_exists = bool(engine.execute(
                "SELECT * "
                "FROM information_schema.columns "
                "WHERE table_name = 'users'"
            ).fetchall())
            if user_table_exists:
                users_exist = bool(engine.execute(
                    "SELECT * FROM users"
                ).fetchall())
            else:
                users_exist = False
            if users_exist:
                print(
                    'ADMIN_PASSWORD is set, but there already are users in '
                    'the database. No admin user will be created.'
                    '\n',
                    file=sys.stderr
                )
            else:
                admin_username = config.get('ADMIN_USERNAME', 'admin').lower()
                admin_email = config.get('ADMIN_EMAIL', config['CONTACT_EMAIL']).lower()
                print(
                    'A new admin user with the username "{}", the email '
                    'address "{}" and the given ADMIN_PASSWORD will be '
                    'created.'
                    '\n'.format(admin_username, admin_email),
                    file=sys.stderr
                )
                internal_config['ADMIN_INFO'] = (
                    admin_username, admin_email, config['ADMIN_PASSWORD']
                )
                if config['ADMIN_PASSWORD'] == 'password':
                    print(
                        '\033[33mYou are using the default ADMIN_PASSWORD from the '
                        'SampleDB documentation. Please sign in and change your '
                        'password before making this SampleDB instance available '
                        'to other users.'
                        '\033[0m\n',
                        file=sys.stderr
                    )

        show_config_info = True

    if show_config_info:
        print(
            'For more information on setting SampleDB configuration, see: '
            'https://scientific-it-systems.iffgit.fz-juelich.de/SampleDB/'
            'developer_guide/configuration.html',
            file=sys.stderr
        )

    if not can_run:
        exit(1)

    return internal_config


# prefix for all routes (used by run script)
SERVER_PATH = '/'

# whether to use CSRF protection
# see: https://flask-wtf.readthedocs.io/en/stable/config.html
CSRF_ENABLED = True

# secret key for Flask, wtforms and more
# see: http://flask.pocoo.org/docs/1.0/config/#SECRET_KEY
# automatically generated default, but should be replaced using environment variable SAMPLEDB_SECRET_KEY
SECRET_KEY = generate_secret_key(num_bits=256)

# whether or not SQLAlchemy should track modifications
# see: http://flask-sqlalchemy.pocoo.org/2.3/config/
# deprecated and should stay disabled, as we manually add modified objects
SQLALCHEMY_TRACK_MODIFICATIONS = False

# LDAP settings
LDAP_NAME = None
LDAP_SERVER = None
LDAP_USER_BASE_DN = None
LDAP_UID_FILTER = None
LDAP_NAME_ATTRIBUTE = None
LDAP_MAIL_ATTRIBUTE = None
LDAP_OBJECT_DEF = None
# LDAP credentials, may both be None if anonymous access is enabled
LDAP_USER_DN = None
LDAP_PASSWORD = None

# email settings
MAIL_SERVER = None
MAIL_SENDER = None
CONTACT_EMAIL = None

# branding and legal info
SERVICE_NAME = 'SampleDB'
SERVICE_DESCRIPTION = SERVICE_NAME + ' is the sample and measurement metadata database at PGI and JCNS.'
SERVICE_IMPRINT = None
SERVICE_PRIVACY_POLICY = None

# location for storing files
# in this directory, per-action subdirectories will be created, containing
# per-object subdirectories, containing the actual files
FILE_STORAGE_PATH = '/tmp/sampledb/'

# a map of file extensions and the MIME types they should be handled as
# this is used to determine which user uploaded files should be served as
# images (those with an image/ MIME type) in the object view and which support
# a preview.
# files with extensions not listed here only support being downloaded.
MIME_TYPES = {
    '.txt': 'text/plain',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.pdf': 'application/pdf'
}

# JupyterHub settings
JUPYTERHUB_URL = None

# CSRF token time limit
# users may take a long time to fill out a form during an experiment
WTF_CSRF_TIME_LIMIT = 12 * 60 * 60

# environment variables override these values
use_environment_configuration(env_prefix='SAMPLEDB_')
