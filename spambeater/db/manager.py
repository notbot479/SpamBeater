from typing import Literal, Union
import aiofiles
import csv
import os


Category = Union[Literal['spam'],Literal['ham']]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SaveManager:
    _text_db_path = os.path.join(BASE_DIR, 'db.csv')
    _spam_dir = os.path.join(BASE_DIR, 'spam')
    _ham_dir = os.path.join(BASE_DIR, 'ham')

    @classmethod
    async def save_text(cls,text:str, category: Category) -> None:
        data = (category, text)
        async with aiofiles.open(cls._text_db_path, 'a', newline='') as file:
            writer = csv.writer(file)
            await writer.writerow(data)
    
    @classmethod
    async def save_media(
        cls, 
        file_bytes: bytes, 
        filename: str, 
        category: Category,
    ) -> None:
        path = cls._get_save_media_path(filename=filename, category=category)
        async with aiofiles.open(path, 'wb') as file: 
            await file.write(file_bytes)


    @classmethod
    def _get_save_media_path(cls, filename:str, category: Category) -> str:
        dir_path = cls._spam_dir if category == 'spam' else cls._ham_dir
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, filename)
        return path
