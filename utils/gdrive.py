import sys
import time
from urllib.parse import urlparse
from pathlib import Path, PurePosixPath

import requests
from tqdm import tqdm

from utils.logger import get_logger


logger = get_logger(__name__)

# Public key of the Google Drive web client, enough to export a shared folder.
INCOGNITO_USER_KEY = "AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE"
EXPORTS_API = "https://takeout-pa-qw.clients6.google.com/v1/exports"
ARCHIVE_PREFIX = "wroclaw-photo"
ARCHIVE_NAME = "file-archive.zip"
REQUEST_TIMEOUT = 60  # seconds without an answer before a request fails


class ExportFailed(RuntimeError):
    pass


class GDrive:

    def __init__(
        self,
        google_storage_url: str,
        session: requests.Session | None = None,
        poll_interval: float = 5,
        export_timeout: float = 30 * 60,
    ):
        self.google_storage_url = google_storage_url
        self.google_drive_id = PurePosixPath(
            urlparse(self.google_storage_url).path
        ).name
        self.headers = {"referer": "https://drive.google.com/", "user-agent": ""}
        self.session = session or requests.Session()
        self.poll_interval = poll_interval
        self.export_timeout = export_timeout

    def _initiate_archiving(self):
        logger.info("[⚠️]Triggering archiving process...")
        response = self.session.request(
            method="POST",
            url=EXPORTS_API,
            params={"key": INCOGNITO_USER_KEY},
            headers=self.headers,
            json={
                "archivePrefix": ARCHIVE_PREFIX,
                "items": [{"id": self.google_drive_id}],
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        logger.info("[✅] Archiving process has been initiated")
        return response.json()

    def _get_archiving_status(self, job_id: str):
        response = self.session.request(
            method="GET",
            url=f"{EXPORTS_API}/{job_id}",
            params={"key": INCOGNITO_USER_KEY},
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def _test_accessibility(self):
        logger.info("[⚠️] Checking Google Drive directory availability...")
        response = self.session.get(self.google_storage_url, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            logger.error(
                f"[❗] WARNING. Directory: {self.google_storage_url} is not available"
            )
            raise ConnectionAbortedError(self.google_storage_url)
        logger.info(
            f"[✅] Directory: {self.google_storage_url} is available for download."
        )

    def _download_file(
        self, url: str, output_path: str | Path, chunk_size: int = 1024 * 1024
    ):
        logger.info("[⚠️] Starting download...")

        with self.session.request(
            method="GET", url=url, stream=True, timeout=REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))

            output_path = Path(output_path)
            if output_path.is_dir():
                output_path = Path(output_path, ARCHIVE_NAME)

            with (
                output_path.open("wb") as file,
                tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=output_path.name,
                    initial=0,
                    ascii=True,
                    file=sys.stdout,
                    ncols=80,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
                ) as progress,
            ):
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        progress.update(len(chunk))

            logger.info(
                f"[✅] Download finished! File is available here: {output_path}"
            )
            return output_path

    def download_archive(self, download_path: str | Path):
        self._test_accessibility()
        job_id = self._initiate_archiving()["exportJob"]["id"]
        export_job = self._wait_for_archive(job_id)
        download_link = export_job["archives"][0]["storagePath"]
        return self._download_file(url=download_link, output_path=download_path)

    def _wait_for_archive(self, job_id: str) -> dict:
        deadline = time.monotonic() + self.export_timeout
        while True:
            export_job = self._get_archiving_status(job_id)["exportJob"]
            status = export_job["status"]
            logger.info(f"[⚠️] Is archive ready for download: {status}")
            if status == "SUCCEEDED":
                return export_job
            if status == "FAILED":
                raise ExportFailed(f"Google Drive failed to archive job {job_id}")
            if time.monotonic() > deadline:
                raise TimeoutError(f"Archive {job_id} not ready in time")
            time.sleep(self.poll_interval)
