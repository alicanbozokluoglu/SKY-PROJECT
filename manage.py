#!/usr/bin/env python
# this line tells the system to use python to run this file

"""Django's command-line utility for administrative tasks."""
# this file is used to run commands like starting the server, migrations, etc.

import os
# this lets python work with system settings (like environment variables)

import sys
# this lets python read inputs from the command line (like arguments you type)


def main():
    """Run administrative tasks."""
    # this function runs when you use commands like:
    # python manage.py runserver

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    # this tells django where to find the settings file
    # "config.settings" is the file that contains project settings

    try:
        from django.core.management import execute_from_command_line
        # this imports django's tool that runs commands like runserver, migrate, etc.

    except ImportError as exc:
        # this happens if django is not installed or not found

        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        # this shows an error message to help fix the problem

    execute_from_command_line(sys.argv)
    # this line actually runs the command you typed in terminal
    # for example:
    # python manage.py runserver
    # python manage.py migrate


if __name__ == '__main__':
    # this checks if this file is being run directly

    main()
    # this starts the main function and runs the django command

"""This file is the main control file for Django.
When I type commands like runserver or migrate, this file runs them.
It connects Django to the settings file and then executes the command I typed."""