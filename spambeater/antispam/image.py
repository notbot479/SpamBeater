import tensorflow as tf
import keras

import pandas as pd
import numpy as np
import os

from .predict_model import PredictModelBase


class ImagePredictModel(PredictModelBase):
    _class_names = ['meat','notspam']
    _notspam_class_name = 'notspam'

    def _get_class_name(self, inx:int) -> str | None:
        try:
            name = self._class_names[inx]
            return name
        except:
            return None

    def is_spam_class(self, name: str) -> bool:
        status = not(name == self._notspam_class_name)
        return status

    def __init__(self, model_dir: str | None = None) -> None:
        self._model_dir = self._get_model_dir(model_dir)
        self._model_path = os.path.join(self._model_dir,'model.keras') 
        self.model = None
        self.load()

    def predict_spam(self, image: np.ndarray) -> bool:
        if not(self.model): return False
        X = tf.expand_dims(image, axis=0)
        y = self.model.predict(X, verbose=0)[0] #pyright: ignore
        inx = int(np.argmax(y))
        class_name = self._get_class_name(inx=inx)
        print(class_name, y)
        if not(class_name): return False
        spam = self.is_spam_class(name = class_name)
        return spam
    
    def predict_spam_proba(self, image: np.ndarray) -> float: 
        spam = self.predict_spam(image=image)
        return float(1 if spam else 0)

    def load(self) -> None: 
        try:
            path = self._model_path
            self.model = keras.models.load_model(path)
        except Exception as e:
            print(e)

    def save(self) -> None: # pyright: ignore
        raise NotImplementedError

    def train(self, data:pd.DataFrame) -> None: 
        raise NotImplementedError


def _test():
    antispam = ImagePredictModel()
    print(antispam)

if __name__ == '__main__':
    _test()