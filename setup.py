#!/usr/bin/env python
import os
import re
import sys

from setuptools import find_packages, setup

# get version without importing
with open("modeltrans/__init__.py", "rb") as f:
    VERSION = str(re.search('__version__ = "(.+?)"', f.read().decode("utf-8")).group(1))

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist")
    os.system("twine upload dist/django-modeltrans-{}.tar.gz".format(VERSION))
    message = "\nreleased [{version}](https://pypi.python.org/pypi/django-modeltrans/{version})"
    print(message.format(version=VERSION))
    sys.exit()

if sys.argv[-1] == "tag":
    os.system("git tag -a v{} -m 'tagging v{}'".format(VERSION, VERSION))
    os.system("git push --tags && git push origin master")
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
    install_requires=["Django>=1.11.15"],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
    ],
)
