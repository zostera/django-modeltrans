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

    # change directory to the test_migrations folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print('Current working directory:', os.getcwd())

    # clean up the test projects directory
    cmd('git clean migrate_test/ -f')
    cmd('git checkout -- migrate_test/')

    cmd('pip install -r requirements.txt')

    # start with an empty db
    cmd('dropdb modeltrans-migration --if-exists')

    if 'TRAVIS' in os.environ:
        cmd('createdb modeltrans-migration -U postgres')
    else:
        cmd('createdb modeltrans-migration')

    # populate database and do some pre-migration verifications
    manage('migrate')
    manage('loaddata data.json')
    run_test('pre_migrate_tests')

    # do the actual migration modeltranslation -> modeltrans.

    # 1. install django-modeltrans and add to installed apps.
    cmd('pip install -U ..')
    cmd('''sed -i "s/# 'modeltrans'/'modeltrans'/g" migrate_test/settings.py''')

    # 2. Uncomment modeltrans i18n-field in models.py
    cmd('sed -i "s/# from/from/g" {}'.format(MODELS_PY))
    cmd('sed -i "s/# i18n/i18n/g" {}'.format(MODELS_PY))

    # 3. make the migrations to add django-modeltrans json fields
    manage('makemigrations app')
    manage('migrate app')

    # 4. Create the data migration
    manage('i18n_makemigrations app')
    manage('migrate app')

    # 5. remove django-modeltranslation
    cmd('''sed -i "s/'modeltranslation',//g" migrate_test/settings.py''')
    cmd('rm -r migrate_test/app/translation.py')
    cmd('sed -i "s/, virtual_fields=False//g" {}'.format(MODELS_PY))

    # 6. migrate once more to remove django-modeltranslation's fields
    manage('makemigrations app')
    manage('migrate app')

    # 6. run the post-migration tests
    run_test('post_migrate_tests')


def cmd(c):
    print('\033[92m Running command: \033[0m', c)

    try:
        result = check_output(c, shell=True, stderr=STDOUT)
        if len(result) > 0:
            print(str(result).replace('\\n', '\n'))
        return result
    except CalledProcessError as e:
        print('\033[31m Process errored: \033[0m, code: {}'.format(e.returncode))
        print(str(e.output).replace('\\n', '\n'))
        sys.exit(1)


def manage(c):
    cmd('coverage run -a --rcfile=../.coveragerc ./manage.py {}'.format(c))


def run_test(test_module):
    assert not test_module.endswith('.py')

    manage('test --keepdb {}'.format(test_module))


if __name__ == '__main__':
    main()
