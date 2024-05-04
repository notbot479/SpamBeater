from celery import Celery

import imageio.v2 as iio
import numpy as np

from antispam.image import ImagePredictModel
from bot_types import Spam


image_predict_model = ImagePredictModel()
app = Celery(
    'tasks', 
    broker='pyamqp://guest@localhost//',
    backend='redis://localhost',
)
app.conf.broker_connection_retry_on_startup = True
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['pickle']


@app.task
def predict_images_spam(images: list[np.ndarray]) -> list[Spam]:
    spam = image_predict_model.predict_spam(images=images)
    return spam

@app.task
def get_frames_count(video:bytes) -> int:
    reader = _get_video_reader(video=video)
    return sum([1 for _ in reader.iter_data()])

@app.task
def get_frames_from_video(video:bytes, stop:int,*,step:int=1) -> list[np.ndarray]:
    reader = _get_video_reader(video=video)
    frames = [reader.get_data(min(i,stop)) for i in range(0,stop,step)]
    return frames #pyright: ignore


def _get_video_reader(video:bytes):
    return iio.get_reader(video, format='mp4') #pyright: ignore
