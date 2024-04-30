from PIL.Image import Image as PilImage
from io import BytesIO
from PIL import Image
import numpy as np


def normalize_image(image_bytes:bytes, target_size=(224, 224)) -> np.ndarray:
    image = Image.open(BytesIO(image_bytes))
    image = _crop_center_square(image=image)
    image = image.resize(target_size)
    image_array = np.array(image)
    image_array = image_array.astype(np.float32) / 255.0
    return image_array


def _crop_center_square(image: PilImage) -> PilImage:
    width, height = image.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    right = (width + size) // 2
    bottom = (height + size) // 2
    box = (left, top, right, bottom)
    return image.crop(box=box)
