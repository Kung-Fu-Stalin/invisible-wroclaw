import sys
import time
from urllib.parse import urlparse
from pathlib import Path, PurePosixPath

import requests
from tqdm import tqdm

from utils.logger import get_logger


logger = get_logger(__name__)


class GDrive:

    def __init__(self, google_storage_url: str):
        self.google_storage_url = google_storage_url

        self._test_accessibility()

        self.google_drive_id = PurePosixPath(
            urlparse(self.google_storage_url).path
        ).name
        self.incognito_user_id = "AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE"
        self.google_job_domain = "https://takeout-pa-qw.clients6.google.com"
        self.headers = {
            "referer": "https://drive.google.com/",
            "user-agent": ""
        }
        self.session = self._create_session()

    @staticmethod
    def _create_session():
        logger.info("[✅] Session has been created")
        with requests.Session() as session:
            return session

    def _initiate_archiving(self):
        logger.info("[⚠️]Triggering archiving process...")
        archive_prefix = "wroclaw-photo"
        response = self.session.request(
            method="POST",
            url=f"{self.google_job_domain}/v1/exports",
            params={
                "key": self.incognito_user_id
            },
            headers=self.headers,
            json={
                "archivePrefix": archive_prefix,
                "items": [
                    {
                        "id": self.google_drive_id
                    }
                ]
            }
        )
        response.raise_for_status()
        logger.info("[✅] Archiving process has been initiated")
        return response.json()

    def _get_archiving_status(self, job_id: str):
        response = self.session.request(
            method="GET",
            url=f"{self.google_job_domain}/v1/exports/{job_id}",
            params={
                "key": self.incognito_user_id
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def _test_accessibility(self):
        logger.info("[⚠️] Checking Google Drive directory availability...")
        response = requests.get(self.google_storage_url)
        if response.status_code == 200:
            logger.info(f"[✅] Directory: {self.google_storage_url} is available for download.")
            return True
        else:
            logger.error(f"[❗] WARNING. Directory: {self.google_storage_url} is not available")
            raise ConnectionAbortedError

    def _download_file(self, url: str, output_path: str | Path,
                        chunk_size: int = 1024 * 1024):
        logger.info("[⚠️] Starting download...")

        with self.session.request(method="GET", url=url,
                                  stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))

            if Path(output_path).is_dir():
                filename = "file-archive.zip"
                output_path = Path(output_path, filename)

            with output_path.open("wb") as file, tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=output_path.name,
                    initial=0,
                    ascii=True,
                    file=sys.stdout,
                    ncols=80,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}"
            ) as progress:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        progress.update(len(chunk))

            logger.info(
                f"[✅] Download finished! File is available here: {output_path}"
            )
            return output_path

    def download_archive(self, download_path: str | Path):
        r_json = self._initiate_archiving()
        job_id = r_json["exportJob"]["id"]

        is_ready = False

        while not is_ready:
            r_json = self._get_archiving_status(job_id)
            current_status = r_json["exportJob"]["status"]
            is_ready = current_status == "SUCCEEDED"
            logger.info(f"[⚠️] Is archive ready for download: {current_status}")
            time.sleep(5)

        r_json = self._get_archiving_status(job_id)
        download_link = r_json["exportJob"]["archives"][0]["storagePath"]
        archive_path = self._download_file(
            url=download_link, output_path=download_path
        )
        return archive_path
