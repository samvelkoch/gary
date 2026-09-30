"""Цитаты из аккаунта заказчика (@matautu, 2011–2015) → поиск в корпусе → corpus/tweets/matches.json

Правила:
  * посты, разбитые на части стрелками «->» / «<-», склеиваются в одну цитату;
  * из текста убираются хэштеги, ссылки, кавычки, многоточия; «ё» → «е»; слова в нижнем регистре;
  * совпадение — доля трёхсловных цепочек цитаты, найденных в одном абзаце корпуса (русские тексты: own, self, twin);
    ≥ 0,5 — цитата найдена; для цитат короче 6 слов — только полное совпадение цепочек (1,0);
  * цитата, помеченная хэштегом другого автора (#шантарам, #фаулз, #акунин…), в поиск не идёт, но считается.
"""
import json, pickle, re
from collections import defaultdict, Counter
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE.parent / "corpus" / "tweets" / "matautu_tweets.json"
OUT = HERE.parent / "corpus" / "tweets" / "matches.json"
OTHER = re.compile(r"#(шантарам|shantaram|фаулз|волхв|акунин|беллона|гроссман|бенгстон|генрихманн|шекспир)", re.I)
W = re.compile(r"[а-яёa-z]+")


def norm_words(t):
    t = re.sub(r"https?://\S+|twitpic\.com/\S+|#\S+|@\S+", " ", t)
    return [w.replace("ё", "е") for w in W.findall(t.lower())]


def join_parts(T):
    """Склейка частей: пост, кончающийся на «->», продолжается следующим, начинающимся с «<-»."""
    out, cur = [], None
    for t, tid, tx in T:
        s = tx.strip()
        starts = s.lstrip('"“. ').startswith("<-") or s.startswith("..<-") or s.startswith(".. <-")
        if cur and starts:
            cur["text"] += " " + s; cur["ids"].append(tid)
        else:
            if cur: out.append(cur)
            cur = {"t": t, "ids": [tid], "text": s}
        if not s.rstrip('"” .…').endswith("->"):
            out.append(cur); cur = None
    if cur: out.append(cur)
    return out


def main():
    T = [x for x in json.load(open(SRC)) if x[0] < "2016"]
    Q = join_parts(T)
    docs = pickle.load(open(HERE / "corpus.pkl", "rb"))
    paras = []
    for d in docs:
        if d["lang"] != "ru" or d["role"] not in ("own", "self", "twin"):
            continue
        for i, p in enumerate(d["paras"]):
            paras.append((d["work"], d["role"], d["tr"], i, p["t"]))
    idx = defaultdict(set)
    for k, (_, _, _, _, t) in enumerate(paras):
        w = norm_words(t)
        for j in range(len(w) - 2):
            idx[" ".join(w[j:j + 3])].add(k)
    res = []
    for q in Q:
        other = bool(OTHER.search(q["text"]))
        w = norm_words(q["text"])
        sh = [" ".join(w[j:j + 3]) for j in range(len(w) - 2)]
        best, share = None, 0.0
        if sh and not other:
            c = Counter(k for s in set(sh) for k in idx.get(s, ()))
            if c:
                k, n = c.most_common(1)[0]
                best, share = k, n / len(set(sh))
        need = 1.0 if len(w) < 6 else 0.5
        m = best is not None and share >= need
        r = {"t": q["t"], "ids": q["ids"], "text": q["text"], "words": len(w), "other_author": other, "share": round(share, 2), "found": m}
        if m:
            work, role, tr, i, t = paras[best]
            r.update(work=work, role=role, tr=tr, para=i, para_text=t[:600])
        res.append(r)
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    tot = len(res); oth = sum(r["other_author"] for r in res); fnd = sum(r["found"] for r in res)
    print(f"постов до 2016: {len(T)}; цитат после склейки: {tot}; помечены другим автором: {oth}; найдены в корпусе: {fnd}")
    print("по книгам:", Counter(r["work"] for r in res if r["found"]).most_common())
    print("по ролям:", Counter(r["role"] for r in res if r["found"]))
    nf = [r for r in res if not r["found"] and not r["other_author"] and r["words"] >= 6]
    print(f"не найдены (не другой автор, ≥ 6 слов): {len(nf)}")
    for r in nf[:40]:
        print(f"   {r['share']:.2f} {r['text'][:130]}")


if __name__ == "__main__":
    main()
