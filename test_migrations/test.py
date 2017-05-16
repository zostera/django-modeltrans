import os
from subprocess import call

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def cmd(c):
    return call(c.split())


# setup the Django project:
cmd('pip -r requirements.txt')
cmd('./manage.py migrate')
cmd('./manage.py loaddata data.json')

# run the pre-migrate tests
cmd('./manage.py test pre_migrate_tests')


# do the migration.


# add django-modeltrans to installed apps.
cmd("sed -i 's/# \'modeltrans\'/\'modeltrans\'/g migrate_test/settings.py")


# remove django-modeltranslation
cmd("sed -i 's/\'modeltranslation\',//g migrate_test/settings.py")

# run the post-migrate tests
