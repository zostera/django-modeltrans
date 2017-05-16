#!/usr/bin/env python
from __future__ import print_function

import os
import re
from subprocess import check_output

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def cmd(c):
    print('\033[92m Running command: \033[0m', c)
    return check_output(c.split())


def manage(c):
    print(cmd('./manage.py {}'.format(c)))


def run_test(test_module):
    assert not test_module.endswith('.py')

    manage('test --keepdb {}'.format(test_module))


def indent(s, amount=4):
    return '\n'.join([(' ' * 4) + line for line in s.splitlines()])


MODELTRANS_TEMPLATE = '''

#-#
{old}
#-#

def modeltrans_migration_registration():
    from modeltrans import TranslationOptions, translator

    #-#
    translator.set_create_virtual_fiels(False)
    #-#
{classes}

{registrations}


modeltrans_migration_registration()
'''

# setup the Django project:
cmd('pip install -r requirements.txt')
manage('flush --noinput')
manage('migrate')
manage('loaddata data.json')

run_test('pre_migrate_tests')

# do the actual migration.

# 1. install django-modeltrans and add to installed apps.
cmd('pip install ..')
cmd("sed -i 's/# \'modeltrans\'/\'modeltrans\'/g migrate_test/settings.py")


# 2. add registrations to translation.py
IMPORTS = r"(^from [a-zA-Z\.]+ import [a-zA-Z,_ ]+$|import [a-zA-Z_]+)+"
TRANSLATION_OPTIONS_RE = r"(^class [A-Z]+[a-zA-Z]+\(TranslationOptions\):\n[\s\w=\(\)',]+\n)+$"
TRANSLATION_REGISTRATION = r"(^translator\.register\([A-Za-z ,]+\))+$"

with open('migrate_test/app/translation.py', 'rw') as f:
    contents = f.read()

    imports = re.find(IMPORTS, contents, flats=re.MULTILINE)
    classes = re.find(TRANSLATION_OPTIONS_RE, contents, flags=re.MULTILINE)
    registrations = re.find(TRANSLATION_REGISTRATION, contents, flags=re.MULTILINE)

    f.write(MODELTRANS_TEMPLATE.format(
        old='\n'.join([imports, classes, registrations]),
        classes=indent('\n'.join(classes)),
        registrations=indent(registrations)
    ))

# 3. make the migrations to add django-modeltrans json fields
manage('makemigrations app')
manage('migrate app')
manage('i18n_makemigrations app > migrate_test/app/migrations/0004_i18n_data_migration.py')
manage('migrate app')

# remove django-modeltranslation
cmd("sed -i 's/\'modeltranslation\',//g migrate_test/settings.py")
cmd("sed -i 's/#-#.*#-#//g migrate_test/app/translation.py")

run_test('post_migrate_tests')
#
# # cleanup changed sourcecode files.
