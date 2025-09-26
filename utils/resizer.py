#!/usr/bin/env python3

import io
import os
from pathlib import Path

from PIL import Image, ExifTags

from utils.logger import get_logger


logger = get_logger(__name__)


class TelegramImageResizer:
    def __init__(self, input_dir, max_dim=1280, max_filesize=10 * 1024**2):
        self.input_dir = Path(input_dir)
        self.max_dim = max_dim
        self.max_filesize = max_filesize
        self.image_exts = {".jpg", ".jpeg", ".png"}

    @staticmethod
    def _get_exif_orientation(img):
        try:
            exif = img._getexif()
            if not exif:
                return None
            for k, v in ExifTags.TAGS.items():
                if v == "Orientation":
                    return exif.get(k)
        except Exception:
            return None
        return None

    def _correct_orientation(self, img):
        try:
            orientation = self._get_exif_orientation(img)
            if orientation == 3:
                return img.rotate(180, expand=True)
            if orientation == 6:
                return img.rotate(270, expand=True)
            if orientation == 8:
                return img.rotate(90, expand=True)
        except Exception:
            pass
        return img

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
        q = 95
        size = 0
        while q >= 30:
            buf = io.BytesIO()
            img.convert("RGB").save(
                buf, format="JPEG", quality=q, optimize=True, progressive=True
            )
            size = buf.tell()
            if size <= self.max_filesize or q == 30:
                with open(out_path, "wb") as f:
                    f.write(buf.getvalue())
                return size
            q -= 5
        return size

    def process_file(self, path: Path):
        try:
            orig_size = path.stat().st_size
            with Image.open(path) as img:
                img = self._correct_orientation(img)
                w, h = img.size

                if max(w, h) <= self.max_dim and orig_size <= self.max_filesize:
                    logger.info(f"Skip: {path.name} ({w}x{h}, {orig_size/1024:.1f} KB)")
                    return

                resized = self._resize_keep_aspect(img)
                final_size = self._save_with_size_limit(resized, path)
                logger.info(
                    f"Processed: {path.name} | {w}x{h}->{resized.size[0]}x{resized.size[1]} | {final_size/1024:.1f} KB"
                )

        except Exception as e:
            logger.info(f"Failed: {path} ({e})")

    def process_all(self):
        if not self.input_dir.exists():
            logger.info(f"No such dir: {self.input_dir}")
            return
        for root, _, files in os.walk(self.input_dir):
            for f in files:
                p = Path(root) / f
                if p.suffix.lower() in self.image_exts:
                    self.process_file(p)


if __name__ == "__main__":
    resizer = TelegramImageResizer(
        input_dir="../imgs", max_dim=1280, max_filesize=10 * 1024**2
    )
    resizer.process_all()
