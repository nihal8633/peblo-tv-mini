from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):

    @abstractmethod
    def save(
        self,
        object_key: str,
        data: bytes,
    ) -> str:
        pass

    @abstractmethod
    def get_path(
        self,
        object_key: str,
    ) -> Path:
        pass