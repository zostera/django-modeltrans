#!/usr/bin/env python
from __future__ import print_function

import os
import re
from subprocess import STDOUT, check_output

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def cmd(c):
    print('\033[92m Running command: \033[0m', c)
    return check_output(c, shell=True, stderr=STDOUT)


def manage(c):
    print(cmd('./manage.py {}'.format(c)))


def run_test(test_module):
    assert not test_module.endswith('.py')

    manage('test --keepdb {}'.format(test_module))


def indent(s, amount=4):
    return '\n'.join([(' ' * 4) + line if len(line) > 0 else '' for line in s.splitlines()])


MODELTRANS_TEMPLATE = '''

# - #
{old}
# | #


def modeltrans_migration_registration():
{imports}

    # - #
    translator.set_create_virtual_fields(False)
    # | #


{classes}

{registrations}


modeltrans_migration_registration()
'''

# setup the Django project with a clean db:
cmd('pip install -r requirements.txt')
cmd("echo 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' | ./manage.py dbshell")

# manage('flush --noinput')
# manage('migrate app zero')
manage('migrate')
manage('loaddata data.json')

run_test('pre_migrate_tests')

# do the actual migration.

# 1. install django-modeltrans and add to installed apps.
cmd('pip install --upgrade ..')
cmd('''sed -i "s/# 'modeltrans'/'modeltrans'/g" migrate_test/settings.py''')


# 2. add registrations to translation.py
IMPORTS = r"(^from [a-zA-Z\.]+ import [a-zA-Z,_ ]+$|import [a-zA-Z_]+|\n+)+"
TRANSLATION_OPTIONS_RE = r"(^class [A-Z]+[a-zA-Z]+\(TranslationOptions\):\n[\s\w=\(\)',]+\n)+$"
TRANSLATION_REGISTRATION = r"(^translator\.register\([A-Za-z ,]+\)(\n)*)+"

with open('migrate_test/app/translation.py', 'r+w') as f:
    contents = f.read()

    imports = re.search(IMPORTS, contents, flags=re.MULTILINE).group(0)
    classes = re.search(TRANSLATION_OPTIONS_RE, contents, flags=re.MULTILINE).group(0)
    registrations = re.search(TRANSLATION_REGISTRATION, contents, flags=re.MULTILINE).group(0)

    f.seek(0)
    f.write(MODELTRANS_TEMPLATE.format(
        old='\n'.join([imports, classes, registrations]),

        imports=indent(imports.strip().replace('modeltranslation', 'modeltrans')),
        classes=indent(classes.strip()),
        registrations=indent(registrations.strip())
    ))

# 3. make the migrations to add django-modeltrans json fields
manage('makemigrations app')
manage('migrate app')
manage('i18n_makemigrations app')
manage('migrate app')

# 4. remove django-modeltranslation
cmd('''sed -i "s/'modeltranslation',//g" migrate_test/settings.py''')
cmd('''sed -i "s/(# - #(.|\n)*# \| #)//gm" migrate_test/app/translation.py''')

# 5. migrate once more to remove django-modeltranslation's fields
manage('makemigrations app')
manage('migrate app')


# 6. run the post-migration tests
run_test('post_migrate_tests')
#
# # cleanup changed sourcecode files.
