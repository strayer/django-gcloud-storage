# coding=utf-8
from __future__ import unicode_literals

import os
import string

import pytest
from django.utils.crypto import get_random_string
from django.utils import six

from django_gcloud_storage import DjangoGCloudStorage
from google.cloud.storage import Bucket

from helpers import upload_test_file

DEFAULT_CREDENTIALS_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "test-credentials.json"
)
DEFAULT_BUCKET_LOCATION="europe-west3"
TEST_FILE_PATH = "general_test_file"
TEST_FILE_CONTENT = "Brathähnchen".encode("utf8")

def pytest_addoption(parser):
    parser.addoption("--gcs-credentials-file",
                     action="store",
                     default=DEFAULT_CREDENTIALS_PATH,
                     help="Defaults to PROJECT_DIR/test-credentials.json")
    parser.addoption("--gcs-project-name", action="store")
    parser.addoption("--gcs-bucket-location", action="store",
                     default=DEFAULT_BUCKET_LOCATION,
                     help="Defaults to " + DEFAULT_BUCKET_LOCATION)


@pytest.fixture(scope="module")
def storage(request):
    # create a random test bucket name
    bucket_name = "test_bucket_" + get_random_string(6, string.ascii_lowercase)

    storage = DjangoGCloudStorage(
        project=request.config.getoption("--gcs-project-name"),
        bucket=bucket_name,
        credentials_file_path=request.config.getoption("--gcs-credentials-file")
    )

    # Make sure the bucket exists
    bucket = Bucket(storage.client, bucket_name)
    bucket.location = request.config.getoption("--gcs-bucket-location")
    bucket.create()

    yield storage

    storage.bucket.delete_blobs(storage.bucket.list_blobs())

    storage.bucket.delete(force=True)

@pytest.fixture(scope="module")
def test_file(storage):
    path = upload_test_file(storage, TEST_FILE_PATH, TEST_FILE_CONTENT)
    yield path
    storage.delete(path)

@pytest.fixture(scope="module")
def gcs_settings(request, storage):
    bucket_name = storage.bucket.name

    from django.test import override_settings
    with override_settings(
        GCS_PROJECT=request.config.getoption("--gcs-project-name"),
        GCS_CREDENTIALS_FILE_PATH=request.config.getoption("--gcs-credentials-file"),
        GCS_BUCKET=bucket_name
    ):
        yield True
