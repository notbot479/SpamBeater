from dataclasses import dataclass
from enum import Enum


class FileClass(Enum):
    PHOTO = 1
    VIDEO = 2

@dataclass
class MediaFile:
    fclass: FileClass
    fid: str
