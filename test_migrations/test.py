#!/usr/bin/env python
from __future__ import print_function

import os
import re
import sys
from subprocess import STDOUT, CalledProcessError, check_output


def main():
    '''
    This script runs a migration procedure from django-modeltranslation to
    django-moeltrans.

    `pre_migrate_tests` run before the migration to django-modeltrans
    `post_migrate_tests` run after the migration to django-modeltrans
    '''

    # clean up the test projects directory
    cmd('git clean migrate_test/ -f')
    cmd('git checkout -- migrate_test/')

    cmd('pip install -r requirements.txt')

    # empty db
    cmd("echo 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' | ./manage.py dbshell")

    manage('migrate')
    manage('loaddata data.json')

    run_test('pre_migrate_tests')

    # do the actual migration.

    # 1. install django-modeltrans and add to installed apps.
    cmd('pip install -U ..')
    cmd('''sed -i "s/# 'modeltrans'/'modeltrans'/g" migrate_test/settings.py''')

    # 2. add registrations to translation.py
    add_modeltrans_registration()

    # 3. make the migrations to add django-modeltrans json fields
    manage('makemigrations app')
    manage('migrate app')
    manage('i18n_makemigrations app')
    manage('migrate app')

    # 4. remove django-modeltranslation
    cmd('''sed -i "s/'modeltranslation',//g" migrate_test/settings.py''')
    remove_original_modeltranslation_registrations()

    # 5. migrate once more to remove django-modeltranslation's fields
    manage('makemigrations app')
    manage('migrate app')

    # 6. run the post-migration tests
    run_test('post_migrate_tests')


os.chdir(os.path.dirname(os.path.abspath(__file__)))


def cmd(c):
    print('\033[92m Running command: \033[0m', c)
    try:
        return check_output(c, shell=True, stderr=STDOUT)
    except CalledProcessError as e:
        print('\033[31m Process errored: \033[0m, code: {}'.format(e.returncode))
        print(e.output)
        sys.exit(1)


def manage(c):
    print(cmd('./manage.py {}'.format(c)))


def run_test(test_module):
    assert not test_module.endswith('.py')

    manage('test --keepdb {}'.format(test_module))


def indent(s, amount=4):
    return '\n'.join([(' ' * 4) + line if len(line) > 0 else '' for line in s.splitlines()])


TRANSLATIONS_PY = 'migrate_test/app/translation.py'

# template to generate the new translation.py.
MODELTRANS_TEMPLATE = '''

# start
{old}
# end


def modeltrans_migration_registration():
{imports}

    # start
    translator.set_create_virtual_fields(False)
    # end


{classes}

{registrations}


modeltrans_migration_registration()
'''


def add_modeltrans_registration():
    IMPORTS = r"(^from [a-zA-Z\.]+ import [a-zA-Z,_ ]+$|import [a-zA-Z_]+|\n+)+"
    TRANSLATION_OPTIONS_RE = r"(^class [A-Z]+[a-zA-Z]+\(TranslationOptions\):\n[\s\w=\(\)',]+\n)+$"
    TRANSLATION_REGISTRATION = r"(^translator\.register\([A-Za-z ,]+\)(\n)*)+"

    with open(TRANSLATIONS_PY, 'r') as f:
        contents = f.read()

        imports = re.search(IMPORTS, contents, flags=re.MULTILINE).group(0)
        classes = re.search(TRANSLATION_OPTIONS_RE, contents, flags=re.MULTILINE).group(0)
        registrations = re.search(TRANSLATION_REGISTRATION, contents, flags=re.MULTILINE).group(0)

    with open(TRANSLATIONS_PY, 'w') as f:
        f.write(MODELTRANS_TEMPLATE.format(
            old='\n'.join([imports, classes, registrations]),

            imports=indent(imports.strip().replace('modeltranslation', 'modeltrans')),
            classes=indent(classes.strip()),
            registrations=indent(registrations.strip())
        ))


def remove_original_modeltranslation_registrations():
    COMMENT_RE = r'(# start(.|\n)*?# end)'
    with open(TRANSLATIONS_PY, 'r') as f:
        contents = f.read()
        contents = re.sub(COMMENT_RE, '', contents, flags=re.MULTILINE)

    with open(TRANSLATIONS_PY, 'w') as f:
        f.write(contents)


if __name__ == '__main__':
    main()
