# coding=utf-8
from __future__ import unicode_literals

import datetime
import os
import string
import urllib2
from tempfile import TemporaryFile

import gcloud.exceptions
import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.utils.crypto import get_random_string

from django_gcloud_storage import safe_join, DjangoGCloudStorage, remove_prefix

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))


# noinspection PyClassHasNoInit,PyMethodMayBeStatic
class TestSafeJoin:
    def test_should_join_urls(self):
        assert safe_join("test", "index.html") == "/test/index.html"

    def test_should_not_break_on_slash_on_base(self):
        assert safe_join("test/", "index.html") == "/test/index.html"
        assert safe_join("test///", "index.html") == "/test/index.html"

    def test_should_enforce_starting_slash_on_base(self):
        assert safe_join("/test", "index.html") == "/test/index.html"
        assert safe_join("////test", "index.html") == "/test/index.html"

    def test_should_resolve_dots_to_absolute_path(self):
        assert safe_join("test", "/test/../index.html") == "/test/index.html"

    def test_should_resolve_multiple_slashes(self):
        assert safe_join("test", "/test//abc////index.html") == "/test/test/abc/index.html"
        assert safe_join("test///", "///test//abc////index.html") == "/test/test/abc/index.html"

    def test_should_not_allow_escaping_base_path(self):
        with pytest.raises(SuspiciousFileOperation):
            safe_join("test", "../index.html")
            safe_join("test", "/../index.html")

    def test_should_work_with_bytes(self):
        assert safe_join(b"test", "index.html") == "/test/index.html"
        assert safe_join("test", b"index.html") == "/test/index.html"
        assert safe_join(b"test", b"index.html") == "/test/index.html"

    def test_should_work_with_unicode_characters(self):
        assert safe_join("test", "brathähnchen.html") == "/test/brathähnchen.html"


def test_remove_prefix_function():
    assert remove_prefix("/a/b/c/", "/a/") == "b/c/"
    assert remove_prefix("/a/b/c/", "/b/") == "/a/b/c/"


# noinspection PyClassHasNoInit,PyMethodMayBeStatic
class TestGCloudStorageClass:
    TEST_FILE_NAME = "test_file_" + get_random_string(6)
    TEST_FILE_NAME_UNICODE = "test_file_陰陽_" + get_random_string(6)
    TEST_FILE_CONTENT = "Brathähnchen".encode("utf8")

    @classmethod
    def setup_class(cls):
        # create a random test bucket name
        cls.bucket_name = "test_bucket_" + get_random_string(6, string.ascii_lowercase)

        cls.storage = DjangoGCloudStorage(
            project="django-gcloud-storage",
            bucket=cls.bucket_name,
            credentials_file_path=os.path.join(TESTS_DIR, "..", "django-gcloud-storage-f834e02e2c6d.json")
        )

        # Make sure the bucket exists
        cls.storage.client.create_bucket(cls.bucket_name)

    @classmethod
    def teardown_class(cls):
        cls.storage.bucket.delete(force=True)

    def setup_method(self, method):
        # Make sure there are no test files due to a previous test run
        self.storage.bucket.delete_blobs(self.storage.bucket.list_blobs())

    def upload_test_file(self, name, content):
        with TemporaryFile() as testfile:
            testfile.write(content)
            testfile.seek(0)
            self.storage.save(name, testfile)

    def test_should_create_a_valid_client_object(self):
        with pytest.raises(gcloud.exceptions.NotFound):
            self.storage.client.get_bucket("some_random_bucket_name_that_doesnt_exist")

    def test_should_create_a_valid_bucket_object(self):
        assert self.storage.bucket.exists()

    def test_should_be_able_to_save_and_open_files(self, tmpdir):
        self.upload_test_file(self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        f = self.storage.open(self.TEST_FILE_NAME)
        assert f.read() == self.TEST_FILE_CONTENT

    def test_temporary_files_should_be_removed_after_close(self, tmpdir):
        assert 0

    def test_should_return_created_time(self):
        self.upload_test_file(self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        assert isinstance(self.storage.created_time(self.TEST_FILE_NAME), datetime.datetime)

    def test_should_return_modified_time(self):
        self.upload_test_file(self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        assert isinstance(self.storage.modified_time(self.TEST_FILE_NAME), datetime.datetime)

    def test_should_be_able_to_delete_files(self):
        self.upload_test_file(self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)
        self.storage.delete(self.TEST_FILE_NAME)

        # Should not raise an exception by gcloud
        assert self.storage.delete("missing_file") is None

    def test_exists_method(self):
        assert not self.storage.exists(self.TEST_FILE_NAME)

        self.upload_test_file(self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        assert self.storage.exists(self.TEST_FILE_NAME)

    def test_should_return_correct_file_size(self):
        self.upload_test_file(self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)
        assert self.storage.size(self.TEST_FILE_NAME) == len(self.TEST_FILE_CONTENT)

    def test_should_return_publicy_downloadable_url(self):
        self.upload_test_file(self.TEST_FILE_NAME, self.TEST_FILE_CONTENT)

        assert urllib2.urlopen(self.storage.url(self.TEST_FILE_NAME)).read() == self.TEST_FILE_CONTENT

    def test_should_work_with_utf8(self):
        self.upload_test_file(self.TEST_FILE_NAME_UNICODE.encode("utf8"), self.TEST_FILE_CONTENT)

        self.storage.exists(self.TEST_FILE_NAME_UNICODE.encode("utf8"))

        # Don't explode when trying to find a available name for existing files...
        self.upload_test_file(self.TEST_FILE_NAME_UNICODE.encode("utf8"), self.TEST_FILE_CONTENT)

    def test_should_be_able_to_list_dirs_and_files(self):
        subdir_file_pattern = "/subdir/%s.%d"

        for i in range(1, 11):
            self.upload_test_file(subdir_file_pattern % (self.TEST_FILE_NAME, i), "")

        self.upload_test_file("/subdir/a/" + self.TEST_FILE_NAME, "")
        self.upload_test_file("/subdir/b/" + self.TEST_FILE_NAME, "")

        # Make sure paths prefixed with a slash are normalized
        assert self.storage.listdir("") == self.storage.listdir("/")
        assert self.storage.listdir("subdir") == self.storage.listdir("/subdir")

        root_list_dir = self.storage.listdir("")
        assert len(root_list_dir[0]) == 1 and len(root_list_dir[1]) == 0
        assert root_list_dir[0] == ["subdir"]

        subdir_list_dir = self.storage.listdir("subdir/")
        assert len(subdir_list_dir[0]) == 2 and len(subdir_list_dir[1]) == 10
        assert subdir_list_dir[0] == ["a", "b"]
        assert subdir_list_dir[1][0] == "%s.%d" % (self.TEST_FILE_NAME, 1)

    def test_should_not_overwrite_files_on_save(self):
        self.upload_test_file(self.TEST_FILE_NAME, "")
        self.upload_test_file(self.TEST_FILE_NAME, "")

        assert len(self.storage.listdir("")[1]) == 2

    def test_changed_files_should_be_reuploaded(self):
        self.upload_test_file(self.TEST_FILE_NAME, "")
        first_modified_time = self.storage.modified_time(self.TEST_FILE_NAME)
        local_tmpfile = self.storage.open(self.TEST_FILE_NAME)

        assert local_tmpfile.read() == ""
        local_tmpfile.seek(0)

        local_tmpfile.write(self.TEST_FILE_CONTENT)
        local_tmpfile.close()

        assert self.storage.open(self.TEST_FILE_NAME).read() == self.TEST_FILE_CONTENT
        assert self.storage.modified_time(self.TEST_FILE_NAME) != first_modified_time
