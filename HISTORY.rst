.. :changelog:

History
-------

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
