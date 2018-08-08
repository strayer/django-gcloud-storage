# coding=utf-8
from __future__ import unicode_literals

import datetime
import ssl
from tempfile import TemporaryFile

import google.cloud.exceptions
import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.utils import six

from django_gcloud_storage import safe_join, remove_prefix, GCloudFile

from conftest import TEST_FILE_CONTENT, TEST_FILE_PATH
from helpers import upload_test_file

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
    def test_should_create_blob_at_correct_path(self, storage, test_file):
        assert test_file == TEST_FILE_PATH

    def test_should_create_a_valid_client_object(self, storage):
        with pytest.raises(google.cloud.exceptions.NotFound):
            storage.client.get_bucket("some_random_bucket_name_that_doesnt_exist")

    def test_should_create_a_valid_bucket_object(self, storage):
        assert storage.bucket.exists()

    def test_should_be_able_to_save_and_open_files(self, storage, test_file):
        f = storage.open(test_file)
        assert f.read() == TEST_FILE_CONTENT

    def test_should_return_created_time(self, storage, test_file):
        assert isinstance(storage.created_time(test_file), datetime.datetime)

    def test_should_return_modified_time(self, storage, test_file):
        assert isinstance(storage.modified_time(test_file), datetime.datetime)
        assert isinstance(storage.get_modified_time(test_file), datetime.datetime)

    def test_should_be_able_to_delete_files(self, storage):
        file_name = "test_delete_file"
        upload_test_file(storage, file_name, "")
        storage.delete(file_name)

        # Should not raise an exception by google.cloud
        assert storage.delete("missing_file") is None

    def test_exists_method(self, storage, test_file):
        assert not storage.exists("missing_file")
        assert storage.exists(test_file)

    def test_should_return_correct_file_size(self, storage, test_file):
        assert storage.size(test_file) == len(TEST_FILE_CONTENT)

    def test_should_return_publicly_downloadable_url(self, storage, test_file):
        assert urlopen(storage.url(test_file)).read() == TEST_FILE_CONTENT

    def test_should_work_with_utf8(self, storage):
        file_name = "test_utf8_file_陰陽"
        upload_test_file(storage, file_name, "")

        storage.exists(file_name)

        # Don't explode when trying to find a available name for existing files...
        upload_test_file(storage, file_name, "")

    def test_should_be_able_to_list_dirs_and_files(self, storage):
        file_name = "test_listdir_file"
        subdir_file_pattern = "/subdir/%s.%d"

        for i in range(1, 11):
            upload_test_file(storage, subdir_file_pattern % (file_name, i), "")

        upload_test_file(storage, "/subdir/a/" + file_name, "")
        upload_test_file(storage, "/subdir/b/" + file_name, "")

        # Make sure paths prefixed with a slash are normalized
        assert storage.listdir("") == storage.listdir("/")
        assert storage.listdir("subdir") == storage.listdir("/subdir")

        subdir_list_dir = storage.listdir("subdir/")
        assert len(subdir_list_dir[0]) == 2 and len(subdir_list_dir[1]) == 10
        assert subdir_list_dir[0] == ["a", "b"]
        assert subdir_list_dir[1][0] == "%s.%d" % (file_name, 1)

    def test_should_not_overwrite_files_on_save(self, storage, test_file):
        duplicate_file = upload_test_file(storage, test_file, "")
        assert duplicate_file != test_file

    def test_changed_files_should_be_reuploaded(self, storage):
        file_name = "test_changed_file_reuploaded"
        file_content = "gcloud".encode("ascii")

        upload_test_file(storage, file_name, "")
        first_modified_time = storage.modified_time(file_name)
        local_tmpfile = storage.open(file_name)

        assert local_tmpfile.read() == "".encode("ascii")
        local_tmpfile.seek(0)

        local_tmpfile.write(file_content)
        local_tmpfile.close()

        assert storage.open(file_name).read() == file_content
        assert storage.modified_time(file_name) != first_modified_time

    def test_open_should_be_able_to_create_new_file(self, storage):
        file_name = "test_open_creates_file"
        file_content = "".encode("ascii")

        with storage.open(file_name, mode="wb") as f:
            f.write(file_content)

        assert storage.exists(file_name)

    def test_use_unsigned_urls_option(self, storage, test_file):
        storage.use_unsigned_urls = True
        url = storage.url(test_file)
        storage.use_unsigned_urls = False
        for i in ["Signature=", "GoogleAccessId=", "Expires="]:
            assert i not in url
