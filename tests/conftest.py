import os
import string
from contextlib import contextmanager

import pytest
from django.utils.crypto import get_random_string

from django_gcloud_storage import DjangoGCloudStorage

DEFAULT_CREDENTIALS_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "test-credentials.json"
)


def pytest_addoption(parser):
    parser.addoption("--gcs-credentials-file",
                     action="store",
                     default=DEFAULT_CREDENTIALS_PATH,
                     help="Defaults to PROJECT_DIR/test-credentials.json")
    parser.addoption("--gcs-project-name", action="store")


@contextmanager
def storage_object_for_tests(request, bucket_name=None):
    if bucket_name is None:
        # create a random test bucket name
        bucket_name = "test_bucket_" + get_random_string(6, string.ascii_lowercase)

    storage = DjangoGCloudStorage(
        project=request.config.getoption("--gcs-project-name"),
        bucket=bucket_name,
        credentials_file_path=request.config.getoption("--gcs-credentials-file")
    )

    # Make sure the bucket exists
    storage.client.create_bucket(bucket_name)

    yield storage

    # Manually delete all remaining blobs due to a unicode issue in google.cloud
    from django_gcloud_storage import prepare_name
    for blob in storage.bucket.list_blobs():
        storage.bucket.delete_blob(prepare_name(blob.name))

    storage.bucket.delete(force=True)


@pytest.yield_fixture(scope="session")
def gcs_settings(request):
    # create a random test bucket name
    bucket_name = "test_bucket_" + get_random_string(6, string.ascii_lowercase)

    with storage_object_for_tests(request, bucket_name=bucket_name):
        from django.test import override_settings
        with override_settings(
            GCS_PROJECT=request.config.getoption("--gcs-project-name"),
            GCS_CREDENTIALS_FILE_PATH=request.config.getoption("--gcs-credentials-file"),
            GCS_BUCKET=bucket_name
        ):
            yield True


@pytest.yield_fixture(scope="class")
def storage_object(request):
    with storage_object_for_tests(request) as storage:
        yield storage
