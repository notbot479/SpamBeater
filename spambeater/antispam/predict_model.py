from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score,
    roc_auc_score,
)
from abc import ABC
import pandas as pd
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class PredictModelBase(ABC):
    _base_dir = BASE_DIR
    _metrics = {
        'accuracy': accuracy_score, 
        'precision': precision_score, 
        'recall': recall_score,
        'f1': f1_score,
        'roc': roc_auc_score,
    }

    def __init__(self, model_dir: str | None) -> None:
        self._model_dir = self._get_model_dir(model_dir)
        self.model = None
        self.vectorize_model = None
        self.metrics = {}

    def predict_spam(self, text:str) -> bool: # pyright: ignore
        raise NotImplementedError
    
    def predict_spam_proba(self, text:str) -> float: # pyright: ignore
        raise NotImplementedError

    def save(self) -> None: # pyright: ignore
        raise NotImplementedError

    def load(self) -> None: # pyright: ignore
        raise NotImplementedError

    def train(self, data:pd.DataFrame) -> None: #pyright: ignore 
        raise NotImplementedError

    def _get_train_metrics(self, X_test, y_test) -> dict:
        if not(self.model): return {}
        y_pred = self.model.predict(X_test)
        d = (y_test,y_pred)
        return {k:round(m(*d),3) for k,m in self._metrics.items()}

    def _get_model_dir(self, model_dir: str | None) -> str:
        d = os.path.join(self._base_dir,self.__class__.__name__)
        d = model_dir if model_dir else d
        if not os.path.exists(d): os.makedirs(d)
        return d
