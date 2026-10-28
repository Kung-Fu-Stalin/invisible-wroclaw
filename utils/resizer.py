import io
import os
from pathlib import Path

from PIL import Image, ImageOps

from utils.logger import get_logger
from utils.images_manager import PHOTO_EXTENSIONS


logger = get_logger(__name__)

JPEG_QUALITIES = range(95, 29, -5)  # tried from best until the file is small enough


class TelegramImageResizer:
    def __init__(self, input_dir, max_dim=1280, max_filesize=10 * 1024**2):
        self.input_dir = Path(input_dir)
        self.max_dim = max_dim
        self.max_filesize = max_filesize

    def _resize_keep_aspect(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        max_side = max(w, h)
        if max_side <= self.max_dim:
            return img
        scale = self.max_dim / float(max_side)
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        return img.resize((new_w, new_h), Image.LANCZOS)

    def _save_with_size_limit(self, img: Image.Image, out_path: Path) -> int:
        rgb = img.convert("RGB")
        for quality in JPEG_QUALITIES:
            buffer = io.BytesIO()
            rgb.save(
                buffer, format="JPEG", quality=quality, optimize=True, progressive=True
            )
            if buffer.tell() <= self.max_filesize:
                break
        out_path.write_bytes(buffer.getvalue())
        return buffer.tell()

    def process_file(self, path: Path):
        try:
            orig_size = path.stat().st_size
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)
                w, h = img.size

                if max(w, h) <= self.max_dim and orig_size <= self.max_filesize:
                    logger.info(f"Skip: {path.name} ({w}x{h}, {orig_size/1024:.1f} KB)")
                    return

                resized = self._resize_keep_aspect(img)
                final_size = self._save_with_size_limit(resized, path)
                logger.info(
                    f"Processed: {path.name} | {w}x{h}->{resized.size[0]}x{resized.size[1]} | {final_size/1024:.1f} KB"
                )

        except Exception:
            logger.exception(f"Failed to prepare {path} for Telegram")

    def process_all(self):
        if not self.input_dir.exists():
            logger.info(f"No such dir: {self.input_dir}")
            return
        for root, _, files in os.walk(self.input_dir):
            for f in files:
                p = Path(root) / f
                if p.suffix.lower() in PHOTO_EXTENSIONS:
                    self.process_file(p)
