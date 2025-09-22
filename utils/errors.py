class GoogleDriveDirectoryAccessException(Exception):
    def __init__(self, google_storage_url):
        super().__init__(f"No access to: {google_storage_url}!")


class NotAFileException(Exception):
    def __init__(self, path):
        super().__init__(f"Path {path} is not a file, it's a directory!")
