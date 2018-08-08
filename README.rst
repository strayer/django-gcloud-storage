=============================
django-gcloud-storage
=============================

.. image:: https://img.shields.io/pypi/v/django-gcloud-storage.svg
    :target: https://pypi.python.org/pypi/django-gcloud-storage
.. image:: https://img.shields.io/pypi/l/django-gcloud-storage.svg
    :target: https://pypi.python.org/pypi/django-gcloud-storage
.. image:: https://img.shields.io/pypi/pyversions/django-gcloud-storage.svg
    :target: https://pypi.python.org/pypi/django-gcloud-storage
.. image:: https://img.shields.io/pypi/format/django-gcloud-storage.svg
    :target: https://pypi.python.org/pypi/django-gcloud-storage

Django storage module implementation for Google Cloud Storage using the
google-cloud-storage_ python module by Google.

.. _google-cloud-storage: https://pypi.org/project/google-cloud-storage/

Notice: alpha release
---------------------

Please keep in mind that this version is not yet used in any production application
(as far as I know of) and thus is an alpha release, even though fully tested!
Any kind of feedback is greatly appreciated.

Installation
------------

Install django-gcloud-storage::

    pip install django-gcloud-storage

Create a GCS service account JSON keyfile and a bucket for your application.
Check the documentation of google-cloud-python and Google Cloud Platform for
more details:

https://googlecloudplatform.github.io/google-cloud-python/latest/core/auth.html#setting-up-a-service-account

https://cloud.google.com/storage/docs/authentication#generating-a-private-key

Update your Django settings and use it like any other Django storage module::

    DEFAULT_FILE_STORAGE = 'django_gcloud_storage.DjangoGCloudStorage'

    GCS_PROJECT = "django-gcloud-storage"
    GCS_BUCKET = "django-gcloud-storage-bucket"
    GCS_CREDENTIALS_FILE_PATH = "/path/to/gcs-credentials.json"

Features
--------

* Fully tested on Python 2.7, 3.4 - 3.7, PyPy 2.7-6.0.0 and PyPy 3.5-6.0.0 with
  Django 1.11 and 2.0 - 2.1
* Files are locally downloaded as SpooledTemporaryFile objects to avoid memory
  abuse
* Changed files will automatically be reuploaded to GCS when closed

Caveats
-------

* Files must be fully downloaded to be accessed and fully uploaded when changed
* Everytime a file is opened via the storage module, it will be downloaded again
* (development) Most tests need access to Google Cloud Storage

Unsigned URLS
-------------

The module generates signed urls by default. This requires calls to storage API
which might take some time if you need to return several objects at a time. You
can generate unsigned urls using the following setting::

  GCS_USE_UNSIGNED_URLS = True

Keep in mind you might need to set the default object permission to public for
the unsigned urls to work.

Contributing
------------

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/strayer/django-gcloud-storage/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

django-gcloud-storage could always use more documentation, whether as part of the
official django-gcloud-storage docs, in docstrings, or even on the web in blog posts,
articles, and such.

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. The pull request should work for all supported Python and Django versions
   (see above). Make sure that the tests pass.

Running Tests
-------------

Warning: Most of the tests require a GCS project and will do API requests that
may end up costing you money!

You can run the test suite either in a virtualenv with py.test or with tox - both
require a valid service account JSON keyfile called `test-credentials.json` in
the project root. The GCS project name will be provided via a command argument.

The tests will create and (hopefully) remove buckets on their own. To be safe,
check if there are any leftover buckets in your GCS project after running the
tests!

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install -r requirements-test.txt
    (myenv) $ pip install -e .
    (myenv) $ py.test --gcs-project-name="project-name"

    or

    $ tox -- --gcs-project-name="project-name"

Credits
-------

Inspired by:

* `django-storages`_

.. _`django-storages`: https://pypi.python.org/pypi/django-storages

Tools (partly) used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
