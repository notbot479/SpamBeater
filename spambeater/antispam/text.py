from sklearn.ensemble import GradientBoostingClassifier
from gensim.models import Word2Vec

import pandas as pd
import numpy as np
import joblib
import os

from normalization.text import normalize_text
from .predict_model import PredictModelBase


class TextPredictModel(PredictModelBase):
    _model = GradientBoostingClassifier(
        n_estimators=85,
        max_depth=5,
    )
    _vector_size = 100

    def __init__(self, model_dir: str | None = None) -> None:
        self._model_dir = self._get_model_dir(model_dir)
        self._model_path = os.path.join(self._model_dir, "model.joblib")
        self._vectorizer_path = os.path.join(self._model_dir, "vectorizer.joblib")
        # init save/load paths and try load old model
        self.model = self._model
        self.vectorize_model = None
        self.load()

    def predict_spam(self, text: str) -> bool:
        try:
            text = normalize_text(text)
            vector = np.array(
                [
                    self._vectorize_text(text),
                ]
            )
            p = self.model.predict(vector)  # 0 - spam; 1 - ham
            return not (bool(p))
        except:
            return False

    def predict_spam_proba(self, text: str) -> float:
        try:
            text = normalize_text(text)
            vector = np.array(
                [
                    self._vectorize_text(text),
                ]
            )
            p = self.model.predict_proba(vector)[0][0]
            return round(p, 3)
        except Exception as e:
            print(e)
            return 0.0

    def _vectorize_data(self, data) -> np.ndarray:
        return np.array([self._vectorize_text(i) for i in data])

    @property
    def zero_vector(self) -> np.ndarray:
        return np.zeros(self._vector_size)

    def _vectorize_text(self, sentence: str):
        if not (self.vectorize_model):
            return self.zero_vector
        words = sentence.split()
        words_vecs = [
            self.vectorize_model.wv[w] for w in words if w in self.vectorize_model.wv
        ]
        if len(words_vecs) == 0:
            return self.zero_vector
        words_vecs = np.array(words_vecs)
        return words_vecs.mean(axis=0)

    def save(self) -> None:
        self._save_model()
        self._save_vectorizer()

    def _save_model(self) -> None:
        if not (self.model):
            return
        try:
            joblib.dump(self.model, self._model_path)
        except:
            pass

    def _save_vectorizer(self) -> None:
        if not (self.vectorize_model):
            return
        try:
            joblib.dump(self.vectorize_model, self._vectorizer_path)
        except:
            pass

    def load(self) -> None:
        self._load_model()
        self._load_vectorizer()

    def _load_model(self) -> None:
        try:
            self.model = joblib.load(self._model_path)
        except Exception as e:
            print(e)

    def _load_vectorizer(self) -> None:
        try:
            self.vectorize_model = joblib.load(self._vectorizer_path)
        except Exception as e:
            print(e)

    def train_vectorize_model(self, data) -> None:
        sentences = [sentence.split() for sentence in data]
        self.vectorize_model = Word2Vec(
            sentences=sentences,
            vector_size=self._vector_size,
            window=5,
            min_count=5,
            workers=4,
        )

    def get_normalized_df_by_category(
        self, df: pd.DataFrame, k: int = 1
    ) -> pd.DataFrame:
        ds = df.copy()
        s = ds[ds["category"] == "spam"]  # smallest category
        h = ds[ds["category"] == "ham"].sample(frac=1)[0 : len(s) * k]
        ds = pd.concat([h, s]).sample(frac=1)  # pyright: ignore
        return ds

    def train(
        self,
        df: pd.DataFrame,
        *,
        normalize_df_k: int = 0,  # 0 not normalize df
        save: bool = True,
    ) -> None:
        X, y = self._get_normalized_train_data(df)
        # train word2vec model on all data
        self.train_vectorize_model(X)
        # optimize df by category if needed
        if normalize_df_k:
            df = self.get_normalized_df_by_category(df, k=normalize_df_k)
            X, y = self._get_normalized_train_data(df)
        # vectorize messages and train model
        X = self._vectorize_data(X)
        self.model = self._model
        self.model.fit(X, y)
        if save:
            self.save()

    def _get_normalized_train_data(self, df: pd.DataFrame) -> tuple:
        ds = df.copy()
        # normalize data
        ds["message"] = ds["message"].apply(normalize_text)
        ds["category"] = ds["category"].replace({"spam": 0, "ham": 1})
        # remove invalid data
        ds = ds.drop_duplicates()
        ds = ds[ds["message"] != ""]
        # split data
        X, y = ds["message"], ds["category"].values  # pyright: ignore
        return (X, y)


def _test():
    antispam = TextPredictModel()
    print(antispam)


if __name__ == "__main__":
    _test()
