# coding=utf-8
from __future__ import unicode_literals

import datetime
import ssl
from tempfile import TemporaryFile

import google.cloud.exceptions
import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.utils import six
from django.utils.crypto import get_random_string

from django_gcloud_storage import safe_join, remove_prefix, GCloudFile


def urlopen(*args, **kwargs):
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib2 import urlopen

    try:
        # Ignore SSL errors (won't work on Py3.3 but can be ignored there)
        kwargs["context"] = ssl._create_unverified_context()
    except AttributeError:  # Py3.3
        pass

    return urlopen(*args, **kwargs)


@pytest.fixture
def storage(storage_object):
    # Make sure there are no test files due to a previous test run
    from django_gcloud_storage import prepare_name
    for blob in storage_object.bucket.list_blobs():
        storage_object.bucket.delete_blob(prepare_name(blob.name))

    return storage_object


# noinspection PyClassHasNoInit,PyMethodMayBeStatic
class TestSafeJoin:
    def test_should_join_urls(self):
        assert safe_join("test", "index.html") == "test/index.html"

    def test_should_not_break_on_slash_on_base(self):
        assert safe_join("test/", "index.html") == "test/index.html"
        assert safe_join("test///", "index.html") == "test/index.html"

    def test_should_enforce_no_starting_slash_on_base(self):
        assert safe_join("/test", "index.html") == "test/index.html"
        assert safe_join("////test", "index.html") == "test/index.html"

    def test_should_resolve_dots_to_absolute_path(self):
        assert safe_join("test", "/test/../index.html") == "test/index.html"

    def test_should_resolve_multiple_slashes(self):
        assert safe_join("test", "/test//abc////index.html") == "test/test/abc/index.html"
        assert safe_join("test///", "///test//abc////index.html") == "test/test/abc/index.html"

    def test_should_not_allow_escaping_base_path(self):
        with pytest.raises(SuspiciousFileOperation):
            safe_join("test", "../index.html")
        with pytest.raises(SuspiciousFileOperation):
            safe_join("test", "/../index.html")

    def test_should_work_with_bytes(self):
        assert safe_join(b"test", "index.html") == "test/index.html"
        assert safe_join("test", b"index.html") == "test/index.html"
        assert safe_join(b"test", b"index.html") == "test/index.html"

    def test_should_work_with_unicode_characters(self):
        assert safe_join("test", "brathähnchen.html") == "test/brathähnchen.html"

    def test_should_normalize_system_dependant_slashes(self):
        assert safe_join("test", "windows\\slashes") == "test/windows/slashes"
        assert safe_join("test", "windows\\/slashes") == "test/windows/slashes"
        assert safe_join("windows\\", "slashes") == "windows/slashes"


def test_remove_prefix_function():
    assert remove_prefix("/a/b/c/", "/a/") == "b/c/"
    assert remove_prefix("/a/b/c/", "/b/") == "/a/b/c/"


# noinspection PyMethodMayBeStatic,PyTypeChecker
class TestGCloudFile:
    TEST_CONTENT = "Brathähnchen".encode("utf8")

    def test_should_be_able_to_read_and_write(self, monkeypatch):
        monkeypatch.setattr(GCloudFile, "_update_blob", lambda: None)

        f = GCloudFile(None)
        f.open("w")
        assert f.read() == (b"" if six.PY3 else "")
        f.write(self.TEST_CONTENT)
        f.seek(0)
        assert f.read() == self.TEST_CONTENT

    def test_small_temporary_files_should_not_be_rolled_over_to_disk(self, monkeypatch):
        monkeypatch.setattr(GCloudFile, "_update_blob", lambda: None)

        f = GCloudFile(None, maxsize=1000)
        f.write("a".encode("utf8") * 1000)

        assert not f._tmpfile._rolled

    def test_large_temporary_files_should_be_rolled_over_to_disk(self, monkeypatch):
        monkeypatch.setattr(GCloudFile, "_update_blob", lambda: None)

        f = GCloudFile(None, maxsize=1000)
        f.write("a".encode("utf8") * 1001)

        assert f._tmpfile._rolled

    def test_modified_files_should_be_marked_as_dirty(self, monkeypatch):
        monkeypatch.setattr(GCloudFile, "_update_blob", lambda: None)

        f = GCloudFile(None)
        f.write(self.TEST_CONTENT)

        assert f._dirty


# noinspection PyClassHasNoInit,PyMethodMayBeStatic
class TestGCloudStorageClass:
    TEST_FILE_NAME = "test_file_" + get_random_string(6)
    TEST_FILE_NAME_UNICODE = "test_file_陰陽_" + get_random_string(6)
    TEST_FILE_CONTENT = "Brathähnchen".encode("utf8")

    def upload_test_file(self, storage, name, content):
        if six.PY3 and isinstance(content, str):
            content = content.encode("utf8")

        with TemporaryFile() as testfile:
            testfile.write(content)
            testfile.seek(0)
            storage.save(name, testfile)

    def test_should_create_blob_at_correct_path(self, storage):
        with TemporaryFile() as testfile:
            testfile.write(self.TEST_FILE_CONTENT)
            testfile.seek(0)
            storage_path = storage.save(self.TEST_FILE_NAME, testfile)
        assert storage_path == self.TEST_FILE_NAME

    def test_should_create_a_valid_client_object(self, storage):
        with pytest.raises(google.cloud.exceptions.NotFound):
            storage.client.get_bucket("some_random_bucket_name_that_doesnt_exist")

    def test_should_create_a_valid_bucket_object(self, storage):
        assert storage.bucket.exists()

    def test_should_be_able_to_save_and_open_files(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        f = storage.open(self.TEST_FILE_NAME)
        assert f.read() == self.TEST_FILE_CONTENT

    def test_should_return_created_time(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        assert isinstance(storage.created_time(self.TEST_FILE_NAME), datetime.datetime)

    def test_should_return_modified_time(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        assert isinstance(storage.modified_time(self.TEST_FILE_NAME), datetime.datetime)
        assert isinstance(storage.get_modified_time(self.TEST_FILE_NAME), datetime.datetime)

    def test_should_be_able_to_delete_files(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)
        storage.delete(self.TEST_FILE_NAME)

        # Should not raise an exception by google.cloud
        assert storage.delete("missing_file") is None

    def test_exists_method(self, storage):
        assert not storage.exists(self.TEST_FILE_NAME)

        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        assert storage.exists(self.TEST_FILE_NAME)

    def test_should_return_correct_file_size(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)
        assert storage.size(self.TEST_FILE_NAME) == len(self.TEST_FILE_CONTENT)

    def test_should_return_publicly_downloadable_url(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)
        assert urlopen(storage.url(self.TEST_FILE_NAME)).read() == self.TEST_FILE_CONTENT

    def test_should_work_with_utf8(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME_UNICODE, self.TEST_FILE_CONTENT)

        storage.exists(self.TEST_FILE_NAME_UNICODE)

        # Don't explode when trying to find a available name for existing files...
        self.upload_test_file(storage, self.TEST_FILE_NAME_UNICODE, self.TEST_FILE_CONTENT)

    def test_should_be_able_to_list_dirs_and_files(self, storage):
        subdir_file_pattern = "/subdir/%s.%d"

        for i in range(1, 11):
            self.upload_test_file(storage, subdir_file_pattern % (self.TEST_FILE_NAME, i), "")

        self.upload_test_file(storage, "/subdir/a/" + self.TEST_FILE_NAME, "")
        self.upload_test_file(storage, "/subdir/b/" + self.TEST_FILE_NAME, "")

        # Make sure paths prefixed with a slash are normalized
        assert storage.listdir("") == storage.listdir("/")
        assert storage.listdir("subdir") == storage.listdir("/subdir")

        root_list_dir = storage.listdir("")
        assert len(root_list_dir[0]) == 1 and len(root_list_dir[1]) == 0
        assert root_list_dir[0] == ["subdir"]

        subdir_list_dir = storage.listdir("subdir/")
        assert len(subdir_list_dir[0]) == 2 and len(subdir_list_dir[1]) == 10
        assert subdir_list_dir[0] == ["a", "b"]
        assert subdir_list_dir[1][0] == "%s.%d" % (self.TEST_FILE_NAME, 1)

    def test_should_not_overwrite_files_on_save(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, "")
        self.upload_test_file(storage, self.TEST_FILE_NAME, "")

        assert len(storage.listdir("")[1]) == 2

    def test_changed_files_should_be_reuploaded(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, "")
        first_modified_time = storage.modified_time(self.TEST_FILE_NAME)
        local_tmpfile = storage.open(self.TEST_FILE_NAME)

        assert local_tmpfile.read() == "".encode("ascii")
        local_tmpfile.seek(0)

        local_tmpfile.write(self.TEST_FILE_CONTENT)
        local_tmpfile.close()

        assert storage.open(self.TEST_FILE_NAME).read() == self.TEST_FILE_CONTENT
        assert storage.modified_time(self.TEST_FILE_NAME) != first_modified_time

    def test_open_should_be_able_to_create_new_file(self, storage):
        content = self.TEST_FILE_CONTENT
        if six.PY3 and isinstance(content, str):
            content = content.encode("utf8")

        with storage.open(self.TEST_FILE_NAME, mode="wb") as f:
            f.write(content)

        assert storage.exists(self.TEST_FILE_NAME)

    def test_use_unsigned_urls_option(self, storage):
        self.upload_test_file(storage, self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)
        storage.use_unsigned_urls = True
        url = storage.url(self.TEST_FILE_NAME)
        storage.use_unsigned_urls = False
        for i in ["Signature=", "GoogleAccessId=", "Expires="]:
            assert i not in url
