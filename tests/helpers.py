from tempfile import TemporaryFile

from django.utils import six

def upload_test_file(storage, name, content):
    if six.PY3 and isinstance(content, str):
        content = content.encode("utf8")

    with TemporaryFile() as testfile:
        testfile.write(content)
        testfile.seek(0)
        return storage.save(name, testfile)
