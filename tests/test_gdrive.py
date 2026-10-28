import pytest

from utils import GDrive
from utils.gdrive import ExportFailed

FOLDER = "https://drive.google.com/drive/folders/folder-1"
ARCHIVE_URL = "https://storage.example/archive.zip"


class FakeResponse:
    def __init__(self, status_code=200, json=None, content=b""):
        self.status_code = status_code
        self._json = json
        self.content = content
        self.headers = {"Content-Length": str(len(content))}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ConnectionError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start : start + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeTakeout:
    """Google Drive's archive export API, as seen through requests.Session."""

    def __init__(self, statuses, folder_status=200, archive=b"zip bytes"):
        self.statuses = list(statuses)
        self.folder_status = folder_status
        self.archive = archive

    def get(self, url, **_):
        return FakeResponse(status_code=self.folder_status)

    def request(self, method, url, **_):
        if method == "POST":
            return FakeResponse(json={"exportJob": {"id": "job-1"}})
        if url.endswith("/job-1"):
            status = (
                self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
            )
            archives = [{"storagePath": ARCHIVE_URL}] if status == "SUCCEEDED" else []
            return FakeResponse(
                json={"exportJob": {"status": status, "archives": archives}}
            )
        if url == ARCHIVE_URL:
            return FakeResponse(content=self.archive)
        raise AssertionError(f"unexpected request {method} {url}")


def drive(takeout, **options):
    return GDrive(FOLDER, session=takeout, poll_interval=0, **options)


def test_archive_is_downloaded_once_export_succeeds(tmp_path):
    takeout = FakeTakeout(["QUEUED", "IN_PROGRESS", "SUCCEEDED"], archive=b"photos")

    archive = drive(takeout).download_archive(tmp_path)

    assert archive.read_bytes() == b"photos"
    assert archive.parent == tmp_path


def test_folder_that_is_not_shared_is_reported(tmp_path):
    takeout = FakeTakeout(["SUCCEEDED"], folder_status=403)

    with pytest.raises(ConnectionAbortedError):
        drive(takeout).download_archive(tmp_path)


def test_failed_export_is_reported_instead_of_waiting_forever(tmp_path):
    takeout = FakeTakeout(["IN_PROGRESS", "FAILED"])

    with pytest.raises(ExportFailed):
        drive(takeout).download_archive(tmp_path)


def test_export_that_never_finishes_gives_up(tmp_path):
    takeout = FakeTakeout(["IN_PROGRESS"])

    with pytest.raises(TimeoutError):
        drive(takeout, export_timeout=0.05).download_archive(tmp_path)
