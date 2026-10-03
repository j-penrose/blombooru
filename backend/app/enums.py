import enum
from typing import Any

class RatingEnum(str, enum.Enum):
    safe = "safe"
    questionable = "questionable"
    explicit = "explicit"

class TagCategoryEnum(str, enum.Enum):
    general = "general"
    artist = "artist"
    character = "character"
    copyright = "copyright"
    meta = "meta"

class FileTypeEnum(str, enum.Enum):
    image = "image"
    video = "video"
    gif = "gif"

class ApiKeyPermissionEnum(str, enum.Enum):
    read = "read"
    write = "write"
    admin = "admin"

def rating_to_str(rating: Any) -> str:
    if rating is None:
        return "safe"
    return rating.value if hasattr(rating, "value") else str(rating)
