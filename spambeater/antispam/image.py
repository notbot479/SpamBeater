import numpy as np
import keras
import os

from .predict_model import PredictModelBase
from logger import logger


class ImagePredictModel(PredictModelBase):
    _class_names = ['ads', 'insects', 'meat', 'ham']
    _ham_class_name = 'ham'

    def _get_class_name(self, inx:int) -> str:
        try:
            name = self._class_names[inx]
            return name
        except:
            return self._ham_class_name

    def is_spam_class(self, name: str) -> bool:
        status = not(name == self._ham_class_name)
        return status

    def __init__(self, model_dir: str | None = None) -> None:
        self._model_dir = self._get_model_dir(model_dir)
        self._model_path = os.path.join(self._model_dir,'model.keras') 
        self.model = None
        self.load()

    def predict_spam(self, images: list[np.ndarray]) -> list[bool]:
        if not(self.model): return []
        X = np.array(images)
        y = self.model.predict(X, verbose=0) #pyright: ignore
        predict = np.argmax(y, axis=1)
        class_names = [self._get_class_name(int(i)) for i in predict]
        for n,p in zip(class_names, y): logger.debug(f'{n} {p}') 
        spam = [self.is_spam_class(i) for i in class_names]
        return spam
    
    def load(self) -> None: 
        try:
            path = self._model_path
            self.model = keras.models.load_model(path)
        except Exception as e:
            print(e)


def _test():
    antispam = ImagePredictModel()
    print(antispam)

if __name__ == '__main__':
    _test()
