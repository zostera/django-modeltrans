#!/usr/bin/env python
from __future__ import print_function
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "migrate_test.settings")
    from django.core.management import execute_from_command_line

    from django.conf import settings
    print('\033[92m INSTALLED_APPS: \033[0m', ', '.join(settings.INSTALLED_APPS))

    # try:
    #     print('JIETER', settings.JIETER)
    # except:
    #     print('no JIETER available')

    execute_from_command_line(sys.argv)
