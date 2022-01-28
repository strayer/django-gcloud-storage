.. :changelog:

History
-------

0.5.0 (2021-01-28)
~~~~~~~~~~~~~~~~~~

* Added support for Django 4.0, 3.2 and 2.2
* Added support for Python 3.8, 3.9 and 3.10
* Added support for PyPy 3.7 and 3.8
* Dropped suport for now unsupported Python and Django versions:
    * Python 2.7, 3.4, 3.5 and 3.6
    * Django 1.11, 2.1 and 3.0

0.4.0 (2019-06-27)
~~~~~~~~~~~~~~~~~~

* Autodetect and set object Content-Type on upload
* Added test support for Django 2.2
* Dropped test support for Django 2.0

0.3.1 (2018-08-08)
~~~~~~~~~~~~~~~~~~

* Updated test support versions for Django 1.11 - 2.1
* Added test support for Python 3.7
* Added test support for Pypy 3
* Dropped support for Python 3.3
* Dropped support for Django 1.11 or older
* Tests are much quicker and do less API requests
* Switched to google-cloud-storage library

0.2.1 (2017-06-23)
~~~~~~~~~~~~~~~~~~

* Use google-cloud package instead of gcloud (package was renamed by Google)
* Added test support for Django 1.10 and 1.11
* Deprecated Django 1.7 (should still work, no support guaranteed)
* Added test support for Python 3.6
* Added setting for unsigned URLs support
* Added get_modified_time() for Django 1.11+ support
* storage.open() will now create new blobs if no existing blob has been found

0.1.0 (2016-02-01)
~~~~~~~~~~~~~~~~~~

* First release on PyPI.
* Development of this release was kindly sponsored by `Craft AG <http://craft.de>`_.
