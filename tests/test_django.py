# coding=utf-8
from __future__ import unicode_literals

import contextlib
import os
import shutil
import tempfile

import pytest
from django.core.files import File
from django.utils.crypto import get_random_string

from test_app.app.models import ModelWithFileField

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from setuptools.py31compat import TemporaryDirectory


@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.usefixtures("gcs_settings")
class TestApp:
    TEST_FILE_NAME = "test_file_" + get_random_string(6)
    TEST_FILE_NAME_UNICODE = "test_file_陰陽_" + get_random_string(6)
    TEST_FILE_CONTENT = "Brathähnchen".encode("utf8")

    @pytest.mark.django_db
    def test_manual_upload(self):
        model_instance = ModelWithFileField()

        with tempfile.TemporaryFile() as testfile:
            testfile.write(self.TEST_FILE_CONTENT)
            testfile.seek(0)

            model_instance.file.save(
                    self.TEST_FILE_NAME,
                    File(testfile)
            )

        model_instance.save()

        model_instance = ModelWithFileField.objects.first()

        with model_instance.file as f:
            assert f.read() == self.TEST_FILE_CONTENT

    @pytest.mark.django_db
    def test_http_upload(self, client):
        """
        :type client: django.test.Client
        """

        with TemporaryDirectory() as tmpdir:
            for filename in [self.TEST_FILE_NAME, self.TEST_FILE_NAME_UNICODE]:
                with open(os.path.join(tmpdir, filename), 'w+b') as testfile:
                    testfile.write(self.TEST_FILE_CONTENT)
                    testfile.seek(0)

                    r = client.post('/upload', {'file': testfile})

                    assert 302 == r.status_code

        assert ModelWithFileField.objects.count() == 2

    @pytest.mark.django_db
    def test_file_access(self, client):
        """
        :type client: django.test.Client
        """
        model_instance = ModelWithFileField()

        with tempfile.TemporaryFile() as testfile:
            testfile.write(self.TEST_FILE_CONTENT)
            testfile.seek(0)

            model_instance.file.save(
                    self.TEST_FILE_NAME,
                    File(testfile)
            )

        model_instance.save()

        model_instance = ModelWithFileField.objects.all()[0]

        r = client.get('/file/%s' % model_instance.pk)

        assert 200 == r.status_code and \
            self.TEST_FILE_CONTENT == r.content
