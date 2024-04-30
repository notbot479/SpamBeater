from PIL.Image import Image as PilImage
from io import BytesIO
from PIL import Image
import numpy as np


def normalize_image(image: bytes | np.ndarray, target_size=(224, 224)) -> np.ndarray:
    if isinstance(image, bytes):
        img = Image.open(BytesIO(image))
    else:
        img = Image.fromarray(image)
    img = _crop_center_square(img=img)
    img = img.resize(target_size)
    image_array = np.array(img)
    image_array = image_array.astype(np.float32) / 255.0
    return image_array


def _crop_center_square(img: PilImage) -> PilImage:
    width, height = img.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    right = (width + size) // 2
    bottom = (height + size) // 2
    box = (left, top, right, bottom)
    return img.crop(box=box)
