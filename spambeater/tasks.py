from celery import Celery

import imageio.v2 as iio
import numpy as np


app = Celery(
    'tasks', 
    broker='pyamqp://guest@localhost//',
    backend='redis://localhost',
)
app.conf.broker_connection_retry_on_startup = True
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['pickle']


def get_video_reader(video:bytes):
    return iio.get_reader(video, format='mp4') #pyright: ignore

@app.task
def get_frames_count(video:bytes) -> int:
    reader = get_video_reader(video=video)
    return sum([1 for _ in reader.iter_data()])

@app.task
def get_frames_from_video(video:bytes, stop:int,*,step:int=1) -> list[np.ndarray]:
    reader = get_video_reader(video=video)
    frames = [reader.get_data(min(i,stop)) for i in range(0,stop,step)]
    return frames #pyright: ignore
