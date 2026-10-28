import pytest
from PIL import Image

from utils import TelegramImageResizer

ORIENTATION = 0x0112
ROTATED_90_CLOCKWISE = 6
MIRRORED_AND_ROTATED = 5


def size_of(path):
    with Image.open(path) as image:
        return image.size


def test_large_photo_is_scaled_down_to_telegram_limit(tmp_path):
    photo = tmp_path / "big.jpg"
    Image.new("RGB", (2560, 1440), "green").save(photo)

    TelegramImageResizer(tmp_path).process_all()

    assert size_of(photo) == (1280, 720)


@pytest.mark.parametrize("size", [(640, 480), (1280, 720)])
def test_photo_within_telegram_limits_is_left_untouched(tmp_path, size):
    photo = tmp_path / "small.jpg"
    Image.new("RGB", size, "green").save(photo)
    original = photo.read_bytes()

    TelegramImageResizer(tmp_path).process_all()

    assert photo.read_bytes() == original


def test_heavy_photo_is_recompressed_under_the_size_limit(tmp_path):
    photo = tmp_path / "noisy.jpg"
    Image.effect_noise((1000, 1000), 100).convert("RGB").save(photo, quality=100)
    limit = photo.stat().st_size // 2

    TelegramImageResizer(tmp_path, max_filesize=limit).process_all()

    assert limit * 0.8 < photo.stat().st_size <= limit  # no more loss than needed
    assert size_of(photo) == (1000, 1000)


def test_sideways_photo_is_stored_upright(tmp_path):
    photo = tmp_path / "portrait.jpg"
    exif = Image.Exif()
    exif[ORIENTATION] = ROTATED_90_CLOCKWISE
    Image.new("RGB", (2000, 1000), "green").save(photo, exif=exif)

    TelegramImageResizer(tmp_path).process_all()

    assert size_of(photo) == (640, 1280)


def test_files_that_are_not_photos_are_ignored(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("not a photo")

    TelegramImageResizer(tmp_path).process_all()

    assert notes.read_text() == "not a photo"


def test_mirrored_sideways_photo_is_stored_upright(tmp_path):
    photo = tmp_path / "selfie.jpg"
    exif = Image.Exif()
    exif[ORIENTATION] = MIRRORED_AND_ROTATED
    Image.new("RGB", (2000, 1000), "green").save(photo, exif=exif)

    TelegramImageResizer(tmp_path).process_all()

    assert size_of(photo) == (640, 1280)


def test_broken_photo_does_not_stop_the_others(tmp_path):
    (tmp_path / "broken.jpg").write_bytes(b"not really a jpeg")
    photo = tmp_path / "big.jpg"
    Image.new("RGB", (2560, 1440), "green").save(photo)

    TelegramImageResizer(tmp_path).process_all()

    assert (tmp_path / "broken.jpg").read_bytes() == b"not really a jpeg"
    assert size_of(photo) == (1280, 720)
