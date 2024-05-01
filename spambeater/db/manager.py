from typing import Literal, Union
import csv
import os


Category = Union[Literal['spam'],Literal['ham']]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SaveManager:
    _spam_dir = os.path.join(BASE_DIR, 'spam')
    _ham_dir = os.path.join(BASE_DIR, 'ham')
    _text_db_path = os.path.join(BASE_DIR, 'db.csv')

    @classmethod
    def save_text(cls,text:str, category: Category) -> None:
        data = (category, text)
        with open(cls._text_db_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    @classmethod
    def get_save_media_path(cls, filename:str, category: Category) -> str | None:
        dir_path = cls._spam_dir if category == 'spam' else cls._ham_dir
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, filename)
        return path
