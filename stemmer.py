import langdetect
import Stemmer

algs = {
    'ru': Stemmer.Stemmer('russian'),
    'en': Stemmer.Stemmer('english'),
}

def words(text, minlen=3, maxlen=50):
    def filter_by_size(words):
        for word in words:
            if len(word) >= minlen and len(word) <= maxlen: yield word

    result = ''.join((c if c.isalnum() else ' ') for c in text).split()
    return [word for word in filter_by_size(result)]

def stem_text(message):
    lang = langdetect.detect(message)
    if lang not in algs:
        lang = 'en'

    return " ".join(algs[lang].stemWords(words(message)))
