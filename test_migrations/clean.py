#!/usr/bin/env python
from __future__ import print_function

import os
import sys
from subprocess import STDOUT, CalledProcessError, check_output


def cmd(c):
    print("\033[92m Running command: \033[0m", c)
    try:
        return check_output(c, shell=True, stderr=STDOUT)
    except CalledProcessError as e:
        print("\033[31m Process errored: \033[0m, code: {}".format(e.returncode))
        print(e.output)
        sys.exit(1)


os.chdir(os.path.dirname(os.path.abspath(__file__)))
cmd("git clean migrate_test/ -f")
cmd("git checkout -- migrate_test/")
