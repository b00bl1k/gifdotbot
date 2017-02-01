# -*- coding: utf-8 -*-

import Stemmer

algs = {
    'ru': Stemmer.Stemmer('russian'),
    'en': Stemmer.Stemmer('english'),
}

def is_russian(word):
    for c in word:
        if u"\u0410" <= c <= u"\u044f":
            return True
    return False

def stem_text(message, minlen=1, maxlen=50):
    result = ''.join((c if c.isalnum() else ' ') for c in message).split()
    text = []
    for word in result:
        if minlen <= len(word) <= maxlen:
            if is_russian(word):
                alg = algs['ru']
            else:
                alg = algs['en']

            text.append(alg.stemWord(word.lower()))

    return " ".join(text)
