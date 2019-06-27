# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import os
import re
from tempfile import SpooledTemporaryFile
import mimetypes

import django
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_text, smart_str
from google.cloud import _helpers as gcloud_helpers
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud.storage.bucket import Bucket

__version__ = '0.4.0'

DJANGO_17 = django.get_version().startswith('1.7.')

try:
    # For Python 3.0 and later
    from urllib import parse as urlparse
except ImportError:
    # Fall back to Python 2's urllib2
    import urlparse


def safe_join(base, path):
    base = force_text(base).replace("\\", "/").lstrip("/").rstrip("/") + "/"
    path = force_text(path).replace("\\", "/").lstrip("/")

    # Ugh... there must be a better way that I can't think of right now
    if base == "/":
        base = ""

    resolved_url = urlparse.urljoin(base, path)

    resolved_url = re.sub("//+", "/", resolved_url)

    if not resolved_url.startswith(base):
        raise SuspiciousFileOperation(
            'The joined path ({}) is located outside of the base path '
            'component ({})'.format(resolved_url, base))

    return resolved_url


def prepare_name(name):
    return smart_str(name, encoding='utf-8')


def remove_prefix(target, prefix):
    if target.startswith(prefix):
        return target[len(prefix):]
    return target


class GCloudFile(File):
    """
    Django file object that wraps a SpooledTemporaryFile and remembers changes on
    write to reupload the file to GCS on close()
    """

    def __init__(self, blob, maxsize=1000):
        """
        :type blob: google.cloud.storage.blob.Blob
        """
        self._dirty = False
        self._tmpfile = SpooledTemporaryFile(
            max_size=maxsize,
            prefix="django_gcloud_storage_"
        )

        self._blob = blob

        super(GCloudFile, self).__init__(self._tmpfile)

    def _update_blob(self):
        # Specify explicit size to avoid problems with not yet spooled temporary files
        # Djangos File.size property already knows how to handle cases like this

        if DJANGO_17 and self._tmpfile.name is None:  # Django bug #22307
            size = self._tmpfile.tell()
        else:
            size = self.size

        self._blob.upload_from_file(self._tmpfile, size=size, rewind=True)

    def write(self, content):
        self._dirty = True
        super(GCloudFile, self).write(content)

    def close(self):
        if self._dirty:
            self._update_blob()
            self._dirty = False

        super(GCloudFile, self).close()


# noinspection PyAbstractClass
@deconstructible
class DjangoGCloudStorage(Storage):

    def __init__(self, project=None, bucket=None, credentials_file_path=None, use_unsigned_urls=None):
        self._client = None
        self._bucket = None

        if bucket is not None:
            self.bucket_name = bucket
        else:
            self.bucket_name = settings.GCS_BUCKET

        if credentials_file_path is not None:
            self.credentials_file_path = credentials_file_path
        else:
            self.credentials_file_path = settings.GCS_CREDENTIALS_FILE_PATH

        assert os.path.exists(self.credentials_file_path), "Credentials file not found"

        if project is not None:
            self.project_name = project
        else:
            self.project_name = settings.GCS_PROJECT

        if use_unsigned_urls is not None:
            self.use_unsigned_urls = use_unsigned_urls
        else:
            self.use_unsigned_urls = getattr(settings, "GCS_USE_UNSIGNED_URLS", False)

        self.bucket_subdir = ''  # TODO should be a parameter
        self.default_content_type = 'application/octet-stream'

    @property
    def client(self):
        """
        :rtype: storage.Client
        """
        if not self._client:
            self._client = storage.Client.from_service_account_json(
                self.credentials_file_path,
                project=self.project_name
            )
        return self._client

    @property
    def bucket(self):
        """
        :rtype: Bucket
        """
        if not self._bucket:
            self._bucket = self.client.get_bucket(self.bucket_name)
        return self._bucket

    def _save(self, name, content):
        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        # Required for InMemoryUploadedFile objects, as they have no fileno
        total_bytes = None if not hasattr(content, 'size') else content.size

        # Set correct mimetype or fallback to default
        _type, _ = mimetypes.guess_type(name)
        content_type = getattr(content, 'content_type', None)
        content_type = content_type or _type or self.default_content_type

        blob = self.bucket.blob(name)
        blob.upload_from_file(content, size=total_bytes, content_type=content_type)

        return name

    def _open(self, name, mode):
        # TODO implement mode?

        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        blob = self.bucket.get_blob(name)
        if blob is None:
            # Create new
            blob = self.bucket.blob(name)
            tmpfile = GCloudFile(blob)
        else:
            tmpfile = GCloudFile(blob)
            blob.download_to_file(tmpfile)
        tmpfile.seek(0)

        return tmpfile

    def created_time(self, name):
        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        blob = self.bucket.get_blob(name)

        # google.cloud doesn't provide a public method for this
        value = blob._properties.get("timeCreated", None)
        if value is not None:
            naive = datetime.datetime.strptime(value, gcloud_helpers._RFC3339_MICROS)
            return naive.replace(tzinfo=gcloud_helpers.UTC)

    def delete(self, name):
        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        try:
            self.bucket.delete_blob(name)
        except NotFound:
            pass

    def exists(self, name):
        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        return self.bucket.get_blob(name) is not None

    def size(self, name):
        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        blob = self.bucket.get_blob(name)

        return blob.size if blob is not None else None

    def modified_time(self, name):
        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        blob = self.bucket.get_blob(name)

        return blob.updated if blob is not None else None

    def get_modified_time(self, name):
        # In Django>=1.10, modified_time is deprecated, and modified_time will be removed in Django 2.0.
        return self.modified_time(name)

    def listdir(self, path):
        path = safe_join(self.bucket_subdir, path)
        path = prepare_name(path)

        iterator = self.bucket.list_blobs(
            prefix=path,
            delimiter="/"
        )

        items = [remove_prefix(blob.name, path) for blob in list(iterator)]
        # prefixes is only set after first iterating the results!
        dirs = [remove_prefix(prefix, path).rstrip("/") for prefix in list(iterator.prefixes)]

        items.sort()
        dirs.sort()

        return dirs, items

    def url(self, name):
        name = safe_join(self.bucket_subdir, name)
        name = prepare_name(name)

        if self.use_unsigned_urls:
          return "https://storage.googleapis.com/{}/{}".format(self.bucket.name, name)

        return self.bucket.get_blob(name).generate_signed_url(expiration=datetime.datetime.now() + datetime.timedelta(hours=1))
