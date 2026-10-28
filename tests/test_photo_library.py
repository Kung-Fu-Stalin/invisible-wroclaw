import zipfile
from pathlib import Path

from conftest import jpeg_bytes

from utils import IMGManager
from utils.images_manager import ImagesManager


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


def test_archive_is_flattened_and_photos_with_same_name_are_all_kept(tmp_path):
    archive = tmp_path / "photos.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("day-1/", "")
        zip_file.writestr("day-1/1.jpg", jpeg_bytes(color="red"))
        zip_file.writestr("day-2/1.jpg", jpeg_bytes(color="blue"))
        zip_file.writestr("day-3/1.jpg", jpeg_bytes(color="white"))

    IMGManager.extract_archive(archive)

    assert sorted(item.name for item in IMGManager.path.iterdir()) == [
        "1.jpg",
        "1_1.jpg",
        "1_2.jpg",
    ]
    assert not archive.exists()


def test_library_folder_is_created_with_its_parents(tmp_path):
    folder = tmp_path / "data" / "photos"

    ImagesManager(folder)

    assert folder.is_dir()


def test_leftovers_of_an_interrupted_refresh_are_removed_on_start(tmp_path):
    leftover = tmp_path / ".staging-interrupted"
    leftover.mkdir()
    (leftover / "1.jpg").write_bytes(jpeg_bytes())
    (tmp_path / "2.jpg").write_bytes(jpeg_bytes())

    ImagesManager(tmp_path)

    assert [item.name for item in tmp_path.iterdir()] == ["2.jpg"]
