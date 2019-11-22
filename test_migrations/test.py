#!/usr/bin/env python

import os
import sys
from subprocess import STDOUT, CalledProcessError, check_output

MODELS_PY = "migrate_test/app/models.py"


def main():
    """
    This script runs a migration procedure from django-modeltranslation to
    django-moeltrans.

    `pre_migrate_tests` run before the migration to django-modeltrans
    `post_migrate_tests` run after the migration to django-modeltrans
    """

    # change directory to the test_migrations folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Current working directory:", os.getcwd())

    # clean up the test projects directory
    cmd("git clean migrate_test/ -f")
    cmd("git checkout -- migrate_test/")

    cmd("pip install -r requirements.txt")

    # start with an empty db
    cmd("dropdb modeltrans-migration --if-exists")

    if "TRAVIS" in os.environ:
        cmd("createdb modeltrans-migration -U postgres")
    else:
        cmd("createdb modeltrans-migration")

    # populate database and do some pre-migration verifications
    manage("migrate")
    manage("loaddata data.json")
    run_test("pre_migrate_tests")

    # do the actual migration modeltranslation -> modeltrans.

    # 1. install django-modeltrans and add to installed apps.
    cmd("pip install -U ..")
    replace_in_file("migrate_test/settings.py", '# "modeltrans"', '"modeltrans"')

    # 2. Uncomment modeltrans i18n-field in models.py
    replace_in_file(MODELS_PY, "# from", "from")
    replace_in_file(MODELS_PY, "# i18n", "i18n")
    replace_in_file(MODELS_PY, "# indexes", "indexes")

    # 3. make the migrations to add django-modeltrans json fields
    manage("makemigrations app")
    manage("migrate app")

    # 4. Create the data migration
    manage("i18n_makemigrations app")
    manage("migrate app")

    # 5. remove django-modeltranslation
    replace_in_file("migrate_test/settings.py", '"modeltranslation",')
    cmd("rm -r migrate_test/app/translation.py")
    replace_in_file(MODELS_PY, ", virtual_fields=False")

    # 6. migrate once more to remove django-modeltranslation's fields
    manage("makemigrations app")
    manage("migrate app")

    # 6. run the post-migration tests
    run_test("post_migrate_tests")


def replace_in_file(file, search, dest=""):
    with open(file, "r") as f:
        contents = f.read()

    with open(file, "w") as f:
        f.write(contents.replace(search, dest))


def cmd(c):
    print("\033[92m Running command: \033[0m", c)

    try:
        result = check_output(c, shell=True, stderr=STDOUT)
        if len(result) > 0:
            print(result.decode().replace("\\n", "\n"))
        return result
    except CalledProcessError as e:
        print("\033[31m Process errored: \033[0m, code: {}".format(e.returncode))
        print(e.output.decode().replace("\\n", "\n"))
        sys.exit(1)


def manage(c):
    cmd("coverage run -a --rcfile=../.coveragerc ./manage.py {}".format(c))


def run_test(test_module):
    assert not test_module.endswith(".py")

    manage("test --keepdb {}".format(test_module))


if __name__ == "__main__":
    main()
