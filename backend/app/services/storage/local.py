from pathlib import Path

from app.services.storage.base import Storage


class LocalStorage(Storage):

    def __init__(self, root: str = "../storage"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, object_key: str) -> Path:
        path = (self.root / object_key).resolve()

        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Invalid storage object key.") from exc

        return path

    def save(
        self,
        object_key: str,
        data: bytes,
    ) -> str:
        path = self._safe_path(object_key)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_bytes(data)

        return object_key

    def get_path(
        self,
        object_key: str,
    ) -> Path:
        return self._safe_path(object_key)