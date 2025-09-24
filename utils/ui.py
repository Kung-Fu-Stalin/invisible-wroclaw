import json
from pathlib import Path

from utils.config import settings


class UIStrings:
    def __init__(self, filepath: Path | str):
        self.filepath = filepath
        self.data = self._open_file()
        self._set_attributes()

    def _open_file(self):
        with open(self.filepath, "r", encoding="utf-8") as file:
            return json.load(file)

    def _set_attributes(self):
        for key, value in self.data.items():
            setattr(self, key, value)


UI = UIStrings(settings.UI)
