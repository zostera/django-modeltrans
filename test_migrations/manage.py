#!/usr/bin/env python
from __future__ import print_function

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "migrate_test.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
