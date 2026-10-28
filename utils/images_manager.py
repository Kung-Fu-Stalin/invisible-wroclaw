import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path

from utils.config import settings
from utils.logger import get_logger


logger = get_logger(__name__)

STAGING_PREFIX = ".staging-"
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def library_order(photo: Path):
    """Numbered photos first, in number order, then the rest by name."""
    if photo.stem.isdigit():
        return 0, int(photo.stem), ""
    return 1, 0, photo.name.lower()


class ImagesManager:

    def __init__(self, path: str | Path):
        logger.info(f"Creating images controller instance for {path}")
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._remove_staging_leftovers()

    def extract_archive(self, archive_path: str | Path):
        logger.info(f"Starting extraction from {archive_path}")
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith("/"):
                    continue
                target_path = Path(self.path, Path(member).name)
                counter = 1
                stem, suffix = target_path.stem, target_path.suffix
                while target_path.exists():
                    target_path = Path(self.path, f"{stem}_{counter}{suffix}")
                    counter += 1
                with zip_ref.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())

        logger.info(f"Extraction has been successful and available here: {self.path}")
        Path(archive_path).unlink()

    def _remove_staging_leftovers(self):
        for leftover in self.path.glob(f"{STAGING_PREFIX}*"):
            logger.warning(f"Removing leftovers of an interrupted update: {leftover}")
            shutil.rmtree(leftover, ignore_errors=True)

    @contextmanager
    def staging(self):
        """A private library to build the next photo set in; removed afterwards."""
        folder = Path(tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=self.path))
        try:
            yield ImagesManager(folder)
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def replace_photos_with(self, other: "ImagesManager"):
        for photo in self.get_files_paths():
            Path(photo).unlink()
        for photo in other.get_files_paths():
            Path(photo).replace(Path(self.path, Path(photo).name))
        logger.warning(f"Photo library has been replaced: {self.path}")

    def get_files_paths(self) -> list[str]:
        photos = [
            item
            for item in self.path.iterdir()
            if item.is_file() and item.suffix.lower() in PHOTO_EXTENSIONS
        ]
        return [str(photo.resolve()) for photo in sorted(photos, key=library_order)]


IMGManager = ImagesManager(settings.IMAGES_DIR)
