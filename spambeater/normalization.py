from io import BytesIO
from PIL import Image
import numpy as np


def normalize_image(image_bytes:bytes, target_size=(224, 224)) -> np.ndarray:
    image = Image.open(BytesIO(image_bytes))
    image = image.resize(target_size)
    image_array = np.array(image)
    image_array = image_array.astype(np.float32) / 255.0
    return image_array
