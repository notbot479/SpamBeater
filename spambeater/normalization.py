

def normalize_text(text:str) -> str:
    text = text.replace('\n',' ')
    text = text.lower()
    return text
