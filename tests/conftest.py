import os

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
