import re
import unicodedata

_PUNCT = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-"})

def normalize(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"(?<=\w)-\s*\r?\n\s*(?=\w)", "", s)
    return re.sub(r"\s+", " ", s.translate(_PUNCT)).strip()

def normalize_with_map(s):
    raw = unicodedata.normalize("NFKC", s or "")
    out, indexes = [], []
    i = 0
    while i < len(raw):
        if raw[i] == "-" and i + 1 < len(raw) and raw[i+1] == "\n" and out and out[-1].isalnum():
            j = i + 2
            while j < len(raw) and raw[j].isspace(): j += 1
            if j < len(raw) and raw[j].isalnum(): i = j; continue
        c = raw[i].translate(_PUNCT)
        if c.isspace():
            if out and out[-1] != " ": out.append(" "); indexes.append(i)
        else: out.append(c); indexes.append(i)
        i += 1
    while out and out[-1] == " ": out.pop(); indexes.pop()
    return "".join(out), indexes
