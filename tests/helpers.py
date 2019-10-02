from tempfile import TemporaryFile

import sys

def upload_test_file(storage, name, content):
    if sys.hexversion >= 0x3000000 and isinstance(content, str):
        content = content.encode("utf8")

    with TemporaryFile() as testfile:
        testfile.write(content)
        testfile.seek(0)
        return storage.save(name, testfile)
