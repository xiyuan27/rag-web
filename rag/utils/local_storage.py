import os
import logging
from rag.utils import singleton
from rag import settings

@singleton
class LocalFileStorage:
    def __init__(self):
        self.base_path = settings.LOCAL_STORAGE_PATH
        os.makedirs(self.base_path, exist_ok=True)

    def _path(self, bucket, fnm):
        bucket_dir = os.path.join(self.base_path, bucket)
        os.makedirs(bucket_dir, exist_ok=True)
        return os.path.join(bucket_dir, fnm)

    def put(self, bucket, fnm, binary):
        path = self._path(bucket, fnm)
        with open(path, 'wb') as f:
            f.write(binary)
        return True

    def rm(self, bucket, fnm):
        try:
            os.remove(self._path(bucket, fnm))
        except FileNotFoundError:
            logging.warning("File not found: %s/%s", bucket, fnm)

    def get(self, bucket, fnm):
        with open(self._path(bucket, fnm), 'rb') as f:
            return f.read()

    def obj_exist(self, bucket, fnm):
        return os.path.exists(self._path(bucket, fnm))

    def health(self):
        try:
            test_path = self._path("health", "check")
            with open(test_path, "wb") as f:
                f.write(b"ok")
            os.remove(test_path)
            return True
        except Exception as e:
            logging.exception("Local storage health check failed: %s", e)
            return False
