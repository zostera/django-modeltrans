#!/usr/bin/env python
import re
import shlex
import subprocess
import sys

from setuptools import find_packages, setup

# get version without importing
with open("modeltrans/__init__.py", "rb") as f:
    VERSION = str(re.search('__version__ = "(.+?)"', f.read().decode("utf-8")).group(1))


def run(command):
    """Run command, aborting the release if it fails."""
    subprocess.check_call(shlex.split(command))


def run_python(command):
    """Run command with the current interpreter, aborting the release if it fails."""
    run("{} {}".format(shlex.quote(sys.executable), command))


if sys.argv[-1] == "publish":
    run_python("-m pip install --upgrade build twine")
    run_python("-m build")
    run_python(
        "-m twine upload"
        " dist/django_modeltrans-{version}.tar.gz"
        " dist/django_modeltrans-{version}-py3-none-any.whl".format(version=VERSION)
    )
    message = "\nreleased [{version}](https://pypi.python.org/pypi/django-modeltrans/{version})"
    print(message.format(version=VERSION))
    sys.exit()

if sys.argv[-1] == "tag":
    run("git tag -a v{version} -m 'tagging v{version}'".format(version=VERSION))
    run("git push --tags")
    run("git push origin master")
    sys.exit()


setup(
    name="django-modeltrans",
    version=VERSION,
    description="Model translations in a jsonb field",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Jan Pieter Waagmeester",
    author_email="jieter@zostera.nl",
    license="Simplified BSD",
    url="https://github.com/zostera/django-modeltrans/",
    packages=find_packages(exclude=["tests.*", "tests", "example.*", "example"]),
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=["Django>=5.2"],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6.0",
        "Framework :: Django :: 6.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
    ],
)
