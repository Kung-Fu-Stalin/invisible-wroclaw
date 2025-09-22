import zipfile
from pathlib import Path

from utils import settings
from utils.logger import get_logger
from utils.errors import NotAFileException


logger = get_logger(__name__)


class ImagesManager:

    def __init__(self, path: str | Path):
        logger.info(f"Creating images controller instance for {path}")
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def is_file_exists(self, file_name: str | Path):
        path = Path(self.path, file_name)
        logger.info(f"Checking file by path: {path}")
        if path.is_dir():
            logger.error(f"{path} is a dir!")
            raise NotAFileException(path)
        return path.exists()

    def extract_archive(self, archive_path: str | Path):
        logger.info(f"Starting extraction from {archive_path}")
        if not self.is_file_exists(archive_path):
            raise FileExistsError(f"Archive by path: {archive_path} is not found")

        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('/'):
                    continue
                target_path = Path(self.path, Path(member).name)
                counter = 1
                stem, suffix = target_path.stem, target_path.suffix
                while target_path.exists():
                    target_path = Path(self.path, f"{stem}_{counter}{suffix}")
                    counter += 1
                with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                    target.write(source.read())

        logger.info(
            f"Extraction has been successful and available here: {self.path}"
        )
        Path(archive_path).unlink()

    def is_dir_empty(self):
        logger.warning("Checking files in directory")
        is_empty = not any(self.path.iterdir())
        logger.warning(f"Current status: {is_empty}")
        return is_empty

    def clear_dir(self):
        logger.warning(f"Clearing dir: {self.path}")
        for item in self.path.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
        logger.warning("!!!Directory has been purged!!!")

    def get_files_paths(self):
        files = [
            str(item.resolve()) for item in self.path.iterdir() if item.is_file()
        ]
        return sorted(
            files,
            key=lambda f: (
                0, int(f.split('/')[-1].split('.')[0])
            ) if f.split('/')[-1].split('.')[0].isdigit() else (1, f.lower())
        )

    def read_image_file(self, file_path: str | Path, mode='rb'):
        if not Path(file_path).is_file():
            raise ValueError(f"Incorrect file_path: {file_path}")
        if not Path(file_path).exists():
            raise ValueError(f"File: {file_path} is not exist")
        image = open(file_path, mode=mode)
        return image


IMGManager = ImagesManager(settings.IMAGES_DIR)
