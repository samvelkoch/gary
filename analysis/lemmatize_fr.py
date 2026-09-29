"""Французские леммы и части речи для готовых списков слов (запускается из .venv-fr).
Вход: JSON [[слово, ...], ...]; выход: <вход>.out.json [[леммы], [части речи]] для каждого текста."""
import json, sys
from pathlib import Path
import spacy
from spacy.tokens import Doc

nlp = spacy.load("fr_core_news_sm", disable=["parser", "ner"])
src = Path(sys.argv[1]); texts = json.load(open(src))
out = []
for words in texts:
    lem, pos = [], []
    for i in range(0, len(words), 3000):  # порции: контекст для разметки, умеренная память
        chunk = words[i:i + 3000]
        doc = Doc(nlp.vocab, words=chunk, spaces=[not w.endswith(("'", "’")) for w in chunk])
        for name, proc in nlp.pipeline:
            doc = proc(doc)
        lem += [t.lemma_.lower() for t in doc]; pos += [t.pos_ for t in doc]
    out.append([lem, pos])
json.dump(out, open(src.with_suffix(".out.json"), "w"), ensure_ascii=False)
print("fr texts", len(out), "tokens", sum(len(l) for l, _ in out))
