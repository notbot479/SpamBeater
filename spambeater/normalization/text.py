from nltk.corpus import stopwords
from nltk import word_tokenize
import nltk

import string
import re
import os


if not (os.path.exists(nltk.data.path[0])):
    nltk.download("stopwords")
    nltk.download("punkt")
else:
    print("Skip install nltk files")


def normalize_text(text: str) -> str:
    text = basic_text_normolization(text)
    text = basic_words_replacement(text)
    text = merge_splitted_words(text)
    text = remove_bad_patterns_from_text(text)
    text = remove_punctuation_from_text(text)
    text = replace_substitution_to_russian(text)
    text = remove_stopwords_from_text(text)
    # funcs below must runs in the end
    text = delete_another_trash_symbols(text)
    text = remove_large_spaces_from_text(text)
    return text


# =========================================================

link_pattern = re.compile(r"[-A-Za-z0-9@:]+\.[-_A-Za-z0-9@:/#&%?=+.]+")
mention_pattern = re.compile(r"\B@[A-Z-a-z0-9_]+")
one_letter_only_pattern = re.compile(r"\b\w\b")
digitsonly_pattern = re.compile(r"[0-9]+")
emoji_pattern = re.compile(
    "["
    "\U0001f1e0-\U0001f1ff"  # flags (iOS)
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f700-\U0001f77f"  # alchemical symbols
    "\U0001f780-\U0001f7ff"  # Geometric Shapes Extended
    "\U0001f800-\U0001f8ff"  # Supplemental Arrows-C
    "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
    "\U0001fa00-\U0001fa6f"  # Chess Symbols
    "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027b0"  # Dingbat Symbols
    "\U000024c2-\U0001f251"  # Enclosed characters
    "]+",
    flags=re.UNICODE,
)

bad_patterns = [
    link_pattern,
    mention_pattern,
    emoji_pattern,
    digitsonly_pattern,
    one_letter_only_pattern,
]


def merge_splitted_words(text: str) -> str:
    pattern = r"(\b\w\b(\s\b\w\b){3,})"
    words = [i[0] for i in re.findall(pattern, text)]
    merged_words = [i.replace(" ", "") for i in words]
    # replace splitted words to merged
    for old, new in zip(words, merged_words):
        text = text.replace(old, new)
    return text


# =========================================================


def basic_words_replacement(text: str) -> str:
    text = private_message_replacement(text)
    return text


def private_message_replacement(text: str):
    pattern = r"л[\.\s]+[cс][\.]+"
    r = re.sub(pattern, "лс", text)
    return r


# =========================================================


def basic_text_normolization(text: str) -> str:
    text = text.lower().replace("\n", " ")
    text = text.replace("ё", "е")  # reduce wordspace
    return text


def remove_bad_patterns_from_text(text: str) -> str:
    for bad_pattern in bad_patterns:
        text = bad_pattern.sub("", text)
    return text


def remove_punctuation_from_text(text: str) -> str:
    extra = [
        "‼",
        "…",
        "—",
        "“",
        "•",
        "˚",
        "»",
        "«",
        "⋆",
        "⇘",
        "⇙",
        "°",
        "⇗",
        "⇖",
        "”",
        "˛",
        "⇩",
        "·",
        "⍟",
        "˖",
        "⊹",
        "+",
        "-",
        "₽",
        "⁉",
        "˒",
        "༆",
        "⁺",
        "₊",
    ]
    exclude = string.punctuation + "".join(set(extra))
    translator = str.maketrans(exclude, " " * len(exclude))
    return text.translate(translator)


def remove_large_spaces_from_text(text: str) -> str:
    pattern = re.compile(r"\s+")
    return pattern.sub(" ", text).strip()


def delete_another_trash_symbols(text: str) -> str:
    kaz = r"\u04D8\u04D9\u04B0\u04B1\u0406\u0456\u04A2\u04A3\u0492\u0493\u04AE\u04AF\u049A\u049B\u04E8\u04E9\u04BA\u04BB"
    rus = r"Ёёа-яА-Я"
    eng = r"A-Za-z"
    extra = r"\d\s"
    pattern = re.compile(rf"[^{rus}{eng}{kaz}{extra}]+")
    return pattern.sub(" ", text).strip()


# =========================================================


def generate_letters_range(start_char: str, stop_char: str) -> str:
    start = ord(str(start_char)[0])
    stop = ord(str(stop_char)[0]) + 1
    return "".join([chr(i) for i in range(start, stop)])


russian_letters = "ёЁ" + "".join(
    [generate_letters_range(*r) for r in [("а", "я"), ("А", "Я"), ("0", "9")]]
)
english_letters = "".join(
    [generate_letters_range(*r) for r in [("a", "z"), ("A", "Z"), ("0", "9")]]
)
substitutions = {
    "а": ["a", "4", "ᥲ", "ᴀ"],
    "б": ["b", "6", "δ", "‍", "ƃ"],
    "в": ["ʙ", "ᏼ"],
    "г": ["g", "ᴦ"],
    "д": ["d"],
    "е": ["e", "ᥱ", "ё", "ᴇ", "ε"],
    "з": ["3", "ᤋ", "ɜ", "ɜ"],
    "и": ["u", "ᥙ", "i", "ᥔ"],
    "к": ["k", "κ", "ᴋ"],
    "л": ["l", "᧘", "ᴧ"],
    "м": ["m", "ʍ"],
    "н": ["h", "n"],
    "о": ["o", "0", "᧐", "ᴏ"],
    "п": ["ᥰ", "ᴨ", "π"],
    "р": ["p", "ρ", "r", "ᴩ"],
    "с": ["c", "ᥴ", "᧐", "ᴄ"],
    "т": ["t", "ᴛ"],
    "у": ["y"],
    "ш": ["ɯ"],
    "ф": ["ɸ"],
    "х": ["x", "᥊"],
    "э": ["϶"],
}


def word_of_language(word: str, all_lang_letters: str) -> bool:
    return all([i in all_lang_letters for i in word])


def replace_substitution_to_russian(text: str) -> str:
    result = []
    words = str(text).split(" ")

    for word in words:
        possible_russian_word = False
        new_word = ""
        # skip russian and english words
        is_rus_word = word_of_language(word, russian_letters)
        is_eng_word = word_of_language(word, english_letters)
        if is_rus_word or is_eng_word:
            result.append(word)
            continue
        for char in word:
            # try to find any possible substituted word
            if char in russian_letters and not (possible_russian_word):
                possible_russian_word = True
            # try find any substitution in word
            replacement = [k for k, v in substitutions.items() if char in v]
            char = str(replacement[0] if replacement else char)
            new_word += char
        needed_in_replacement = possible_russian_word or not (is_eng_word)
        word = new_word if needed_in_replacement else word
        result.append(word)
    return " ".join(result)


# =========================================================

stopwords_langs = ["english", "russian"]
greets = [
    "всем",
    "привет",
    "добрый",
    "день",
    "здравствуйте",
    "здравствуй",
    "приветствую",
    "доброго",
    "времени",
    "суток",
]
trash_words = [
    "http",
    "https",
    "это",
    "нe",
]
extra_stopwords = trash_words + greets


def remove_stopwords_from_text(text: str) -> str:
    new_list, stopwrds = [], extra_stopwords.copy()
    words = word_tokenize(text)
    for lang in stopwords_langs:
        stopwrds.extend(stopwords.words(lang))
    for word in words:
        if word not in set(stopwrds):
            new_list.append(word)
    return " ".join(new_list)


# =========================================================


def _test() -> None:
    text = """
    @mention Hello my friend. 
    How are you? Please, check my new video on youtube 
    https://youtube.com/funnyvideo, also you can watch 
    this video in t.me/some, check my phone +8(800)555-35-35

    Можешь написать мне в л.с.
    """
    print(normalize_text(text))


if __name__ == "__main__":
    _test()
