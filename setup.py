#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    with open(filename) as f:
        version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')

version = get_version('django_gcloud_storage', '__init__.py')

with open('README.rst') as f:
    readme = f.read()
with open('HISTORY.rst') as f:
    history = f.read().replace('.. :changelog:', '')

setup(
    name='django-gcloud-storage',
    version=version,
    description="""Django storage module implementation for Google Cloud Storage""",
    long_description=readme + '\n\n' + history,
    author='Sven Grunewaldt',
    author_email='strayer@olle-orks.org',
    url='https://github.com/strayer/django-gcloud-storage',
    packages=[
        'django_gcloud_storage',
    ],
    include_package_data=True,
    install_requires=[
        "google-cloud-storage>=1.10.0",
        "django>=1.11"
    ],
    license="BSD",
    zip_safe=False,
    keywords='django-gcloud-storage gcloud google-cloud gcs',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
