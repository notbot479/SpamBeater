from dataclasses import dataclass
from enum import Enum


@dataclass
class Spam:
    status: bool
    cls: str | None = None

    def __bool__(self) -> bool:
        return bool(self.status)


class FileClass(Enum):
    PHOTO = 1
    VIDEO = 2


@dataclass
class MediaFile:
    fclass: FileClass
    fid: str
    ext: str
