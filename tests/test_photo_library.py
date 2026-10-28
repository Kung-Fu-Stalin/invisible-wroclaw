import zipfile
from pathlib import Path

from conftest import jpeg_bytes

from utils import IMGManager


def names(paths):
    return [Path(path).name for path in paths]


def test_photos_are_ordered_by_number_then_by_name(photos):
    photos("10.jpg", "b.png", "2.JPG", "A.jpeg", "1.jpg")
    Path(IMGManager.path, "notes.txt").write_text("not a photo")

    assert names(IMGManager.get_files_paths()) == [
        "1.jpg",
        "2.JPG",
        "10.jpg",
        "A.jpeg",
        "b.png",
    ]


def test_archive_is_flattened_and_same_names_are_both_kept(tmp_path):
    archive = tmp_path / "photos.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("day-1/", "")
        zip_file.writestr("day-1/1.jpg", jpeg_bytes(color="red"))
        zip_file.writestr("day-2/1.jpg", jpeg_bytes(color="blue"))

    IMGManager.extract_archive(archive)

    assert names(IMGManager.get_files_paths()) == ["1.jpg", "1_1.jpg"]
    assert not archive.exists()
