#!/usr/bin/env python
from __future__ import print_function

import os
import sys
from subprocess import STDOUT, CalledProcessError, check_output

MODELS_PY = 'migrate_test/app/models.py'


def main():
    '''
    This script runs a migration procedure from django-modeltranslation to
    django-moeltrans.

    `pre_migrate_tests` run before the migration to django-modeltrans
    `post_migrate_tests` run after the migration to django-modeltrans
    '''

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # clean up the test projects directory
    cmd('git clean migrate_test/ -f')
    cmd('git checkout -- migrate_test/')

    cmd('pip install -r requirements.txt')

    # start with an empty db
    cmd("echo 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' | ./manage.py dbshell")

    manage('migrate')
    manage('loaddata data.json')

    run_test('pre_migrate_tests')

    # do the actual migration.

    # 1. install django-modeltrans and add to installed apps.
    cmd('pip install -U ..')
    cmd('''sed -i "s/# 'modeltrans'/'modeltrans'/g" migrate_test/settings.py''')

    # 2. Uncomment modeltrans i18n-field in models.py
    cmd('sed -i "s/# from/from/g" {}'.format(MODELS_PY))
    cmd('sed -i "s/# i18n/i18n/g" {}'.format(MODELS_PY))

    # 3. make the migrations to add django-modeltrans json fields
    manage('makemigrations app')
    manage('migrate app')
    manage('i18n_makemigrations app', prefix='coverage run')
    manage('migrate app')

    # 4. remove django-modeltranslation
    cmd('''sed -i "s/'modeltranslation',//g" migrate_test/settings.py''')
    cmd('rm -r migrate_test/app/translation.py')
    cmd('sed -i "s/, virtual_fields=False//g" {}'.format(MODELS_PY))

    # 5. migrate once more to remove django-modeltranslation's fields
    manage('makemigrations app')
    manage('migrate app')

    # 6. run the post-migration tests
    run_test('post_migrate_tests')


def cmd(c):
    print('\033[92m Running command: \033[0m', c)
    try:
        return check_output(c, shell=True, stderr=STDOUT)
    except CalledProcessError as e:
        print('\033[31m Process errored: \033[0m, code: {}'.format(e.returncode))
        print(e.output)
        sys.exit(1)


def manage(c, prefix=''):
    print(cmd('{} ./manage.py {}'.format(prefix, c)))


def run_test(test_module):
    assert not test_module.endswith('.py')

    manage('test --keepdb {}'.format(test_module), prefix='coverage run')


if __name__ == '__main__':
    main()
