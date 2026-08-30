import spacy
from functools import lru_cache


@lru_cache(maxsize=1)
def get_sentencizer():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp


@lru_cache(maxsize=1)
def get_analyzer():
    return spacy.load("en_core_web_sm")