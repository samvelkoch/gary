"""Данные для интерактивов (по образцу «Бродского» и «Чехова на просвет»): палитра периодов, карта словаря,
сеть «Круг Гари» (реальные люди и герои, названные в нескольких книгах) с карточками, темы с карточками.
Алгоритмы t-SNE, rsvd, k-средних и раскладка «островами» — из samvelkoch/brodsky (style.py, world.py) через «Чехова».
Вход: corpus.pkl, stats.json. Выход: explore.json. Запуск: python explore.py [--qa]
"""
import json, pickle, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
QA = "--qa" in sys.argv
docs = pickle.load(open(HERE / "corpus.pkl", "rb"))
S = json.load(open(HERE / "stats.json", encoding="utf-8"))
PER = [("1937–1949", 1937, 1949), ("1952–1962", 1952, 1962), ("1963–1969", 1963, 1969), ("1970–1980", 1970, 1981)]
per_of = lambda y: next((i for i, (_, a, b) in enumerate(PER) if y and a <= y <= b), -1)
RU = [d for d in docs if d["lang"] == "ru" and d["role"] == "own"]
AT = S["atlas"]
AIX = {a["id"]: a["i"] for a in AT if a["lang"] == "ru" and a["role"] == "own"}
LEX = S["lex"]
OUT = {"periods": [p[0] for p in PER]}

# ------------------------------------------------------------------ алгоритмы (из «Бродского» через «Чехова»)
def kmeans(X, k, n_init=30, iters=300, seed=42):
    rng = np.random.default_rng(seed); best = None
    for _ in range(n_init):
        cen = [X[rng.integers(len(X))]]
        for _ in range(1, k):
            d = np.min(((X[:, None] - np.array(cen)[None]) ** 2).sum(-1), 1)
            cen.append(X[rng.choice(len(X), p=d / d.sum())])
        cen = np.array(cen)
        for _ in range(iters):
            lab = ((X[:, None] - cen[None]) ** 2).sum(-1).argmin(1)
            new = np.array([X[lab == c].mean(0) if (lab == c).any() else cen[c] for c in range(k)])
            if np.allclose(new, cen):
                break
            cen = new
        inertia = ((X - cen[lab]) ** 2).sum()
        if best is None or inertia < best[0]:
            best = (inertia, lab, cen)
    return best[1], best[2]


def rsvd(M, k, it=5, seed=0):
    rng = np.random.default_rng(seed)
    Q = np.linalg.qr(M @ rng.standard_normal((M.shape[1], k + 10)))[0]
    for _ in range(it):
        Q = np.linalg.qr(M @ (M.T @ Q))[0]
    U, Sv, _ = np.linalg.svd(Q.T @ M, full_matrices=False)
    return (Q @ U)[:, :k], Sv[:k]


def tsne(X, perplexity=15, iters=1200, seed=42):
    rng = np.random.default_rng(seed); n = len(X)
    Dd = ((X[:, None] - X[None]) ** 2).sum(-1); P = np.zeros((n, n)); target = np.log(perplexity)
    for i in range(n):
        lo, hi, beta = 1e-20, 1e20, 1.0; di = np.delete(Dd[i], i)
        for _ in range(60):
            pi = np.exp(-di * beta); sp = pi.sum() + 1e-12
            H = np.log(sp) + beta * (di * pi).sum() / sp
            if abs(H - target) < 1e-5:
                break
            if H > target:
                lo = beta; beta = beta * 2 if hi == 1e20 else (beta + hi) / 2
            else:
                hi = beta; beta = (beta + lo) / 2
        P[i, np.arange(n) != i] = pi / sp
    P = (P + P.T) / (2 * n); P = np.maximum(P, 1e-12)
    Y = rng.standard_normal((n, 2)) * 1e-4; vel, gains = np.zeros_like(Y), np.ones_like(Y)
    for t in range(iters):
        ex = 12.0 if t < 250 else 1.0
        num = 1 / (1 + ((Y[:, None] - Y[None]) ** 2).sum(-1)); np.fill_diagonal(num, 0)
        Q = np.maximum(num / num.sum(), 1e-12)
        G = 4 * (((ex * P - Q) * num)[:, :, None] * (Y[:, None] - Y[None])).sum(1)
        mom = 0.5 if t < 250 else 0.8
        gains = (gains + 0.2) * ((G > 0) != (vel > 0)) + gains * 0.8 * ((G > 0) == (vel > 0))
        gains = np.maximum(gains, 0.01); vel = mom * vel - 200 * gains * G
        Y = Y + vel; Y -= Y.mean(0)
    return Y


def island_layout(cl, tx):
    ids = sorted(set(cl.tolist()) - {-1}, key=lambda c: -int((cl == c).sum()))
    size = {c: int((cl == c).sum()) for c in ids}
    rad = {c: 0.11 * np.sqrt(size[c]) + 0.05 for c in ids}
    tot = sum(2 * rad[c] for c in ids); a = 0.3; cen = {}
    R = max(0.62, tot / (2 * np.pi) * 1.08)
    for c in ids:
        wd = 2 * rad[c] / tot * 2 * np.pi
        cen[c] = R * np.array([np.cos(a + wd / 2), np.sin(a + wd / 2)]); a += wd
    P = np.zeros((len(cl), 2)); golden = 2.39996
    for c in ids:
        mem = sorted((i for i in range(len(cl)) if cl[i] == c), key=lambda i: -tx[i])
        sc = rad[c] / np.sqrt(len(mem) + 0.5)
        for r, i in enumerate(mem):
            P[i] = cen[c] + sc * np.sqrt(r + 0.5) * np.array([np.cos(r * golden), np.sin(r * golden)])
    free = [i for i in range(len(cl)) if cl[i] == -1]
    for r, i in enumerate(free):
        P[i] = 0.28 * np.sqrt((r + 0.5) / max(1, len(free))) * np.array([np.cos(r * golden), np.sin(r * golden)])
    return P / (np.abs(P).max() * 1.04)


def snip(t, a, b, n=230):
    s = max(0, (a + b) // 2 - n // 2); e = min(len(t), s + n)
    return ("…" if s > 0 else "") + t[s:e].strip() + ("…" if e < len(t) else "")


# ------------------------------------------------------------------ 1. палитра периодов (русские переводы)
COLHEX = {"белый": "#f4f1ea", "чёрный": "#1d1a17", "черный": "#1d1a17", "красный": "#c43a2c", "синий": "#2c4f9e", "голубой": "#79aee0",
          "зелёный": "#3f8a3c", "зеленый": "#3f8a3c", "жёлтый": "#e3c23a", "желтый": "#e3c23a", "серый": "#8c8a86", "розовый": "#e8a0b4",
          "лиловый": "#9a6bb3", "коричневый": "#7a4e2c", "бурый": "#6d4a2e", "рыжий": "#c96a2b", "золотой": "#c9a227",
          "серебряный": "#c0c3c7", "багровый": "#8e1f1f", "алый": "#e2362e", "фиолетовый": "#6b3fa0", "оранжевый": "#ef8a2b",
          "малиновый": "#b0194f", "сиреневый": "#c3a2d8", "седой": "#d9d6d0", "пёстрый": "#a58a5d", "пестрый": "#a58a5d",
          "бледный": "#e9e1cf", "смуглый": "#a67750", "пурпурный": "#7d1e5a", "лазурный": "#3f8fd2", "бирюзовый": "#2fa3a0",
          "янтарный": "#d99a22", "кремовый": "#efe3c2", "бежевый": "#d8c3a0", "изумрудный": "#1f8a5a", "голубоватый": "#8ab8e0"}
YO = {"черный": "чёрный", "зеленый": "зелёный", "желтый": "жёлтый", "пестрый": "пёстрый"}
pal = []
for p in range(len(PER)):
    c = Counter()
    for d in RU:
        if per_of(d["year"]) != p:
            continue
        for l, t in zip(d["lemmas"], d["tokens"]):
            if l in COLHEX and t[:1].islower():  # «Белый», «Роза» и т. п. с заглавной — имена
                c[YO.get(l, l)] += 1
    pal.append({"p": PER[p][0], "c": sorted([[w, COLHEX[w], n] for w, n in c.items()], key=lambda r: -r[2])})
OUT["palette"] = pal

# ------------------------------------------------------------------ 2. карта словаря (русские переводы)
KEEP = {"NOUN", "ADJF", "ADJS", "VERB", "INFN", "PRTF", "PRTS", "GRND"}
STOPW = set("""быть мочь который мой твой наш ваш свой этот тот весь такой какой самый сам один другой каждый всякий никакой
некоторый иной чей любой должный их её его есть бывать стать иметь сказать""".split())
seqs = []
for d in RU:
    cur = []; last = -1
    for l, pos, nm, pi, t in zip(d["lemmas"], d["pos"], d["is_name"], d["para_of_tok"], d["tokens"]):
        if pi != last and cur:
            seqs.append(cur); cur = []
        last = pi
        if pos in KEEP and not nm and l not in STOPW and len(l) > 1 and t[:1].islower():
            cur.append(l)
    if cur:
        seqs.append(cur)
freq = Counter(w for s in seqs for w in s)
vocab = [w for w, c in freq.most_common() if c >= 10][:6000]
vi = {w: i for i, w in enumerate(vocab)}
Cm = np.zeros((len(vocab), len(vocab)), np.float32)
for s in seqs:
    ids = [vi[w] for w in s if w in vi]
    for x, i in enumerate(ids):
        for j in ids[max(0, x - 5):x]:
            Cm[i, j] += 1; Cm[j, i] += 1
ctx = Cm.sum(0) ** 0.75
pmi = np.log(np.maximum(Cm * ctx.sum() / (Cm.sum(1, keepdims=True) * ctx[None, :] + 1e-9), 1e-9))
ppmi = np.maximum(pmi, 0).astype(np.float32)
U, Sv = rsvd(ppmi, 100)
Wv = U * np.sqrt(Sv); Wv /= np.linalg.norm(Wv, axis=1, keepdims=True) + 1e-9
content = [w for w in vocab if w in LEX]
top_words = content[:260]
neighbors = {}
for w in content[:1500]:
    sims = Wv @ Wv[vi[w]]
    neighbors[w] = [vocab[j] for j in np.argsort(-sims)[1:30] if vocab[j] in LEX and vocab[j] != w][:6]
Vt = np.array([Wv[vi[w]] for w in top_words])
emb = tsne(Vt)
wl, _ = kmeans(Vt, 8, n_init=15)
OUT["wmap"] = [{"w": YO.get(w, w), "k": w, "x": round(float(x), 3), "y": round(float(y), 3), "c": int(c), "n": int(freq[w])}
               for w, (x, y), c in zip(top_words, emb, wl)]
OUT["wgroups"] = [[m["w"] for m in sorted([m for m in OUT["wmap"] if m["c"] == c], key=lambda m: -m["n"])[:4]] for c in range(8)]
OUT["neighbors"] = neighbors

# ------------------------------------------------------------------ 3. «Круг Гари»: люди, названные в нескольких книгах
# имя — лемма с пометой Name/Surn (pymorphy) или вне словаря, с заглавной, не в начале реплики;
# имя перед фамилией не считается отдельным человеком; исключения — те же, что в пантеоне (compute.py)
NOT_PERSON = {"господь", "бог", "мадам", "месье", "мадемуазель", "мисс", "мистер", "сэр", "синьор", "доктор", "роза", "франс",
              "жан", "карл", "жанна", "мария", "марсель", "морис", "пьер", "жак", "поль", "джон", "джек", "джеймс", "мишель",
              "анри", "виктор", "луи", "пьеро", "чарли", "билл", "джо", "том", "анна", "ганс", "фауст",
              "робер", "голуаз",  # Голуаз — марка сигарет
              # отдельные личные имена — персонажи разных книг
              "леон", "марк", "себастьян", "андре", "франсуа", "роже", "альбер", "антуан", "фернан", "гастон", "густав", "томас",
              "гарри", "педро", "джим", "жанно", "павел", "петр", "жозеф", "жозефа", "жюль", "жюля", "карла", "давид",
              # места, названия, вещи
              "нотр-дам", "сен-дени", "булонский", "булонском", "пигаль", "монмартр", "бордигера", "итон", "ларусс", "геральд",
              "лсд", "виктория"}
ALIAS = {"голля": "голль", "баха": "бах", "гамлета": "гамлет", "рембрандта": "рембрандт", "ронсара": "ронсар", "босха": "босх",
         "павлова": "павлов", "монтеня": "монтень", "гог": "ван гог"}
SHOW = {"голль": "де Голль", "арк": "Жанна д'Арк", "бах": "Бах", "гамлет": "Гамлет", "рембрандт": "Рембрандт", "ронсар": "Ронсар",
        "босх": "Босх", "павлов": "Павлов", "монтень": "Монтень", "ван гог": "Ван Гог"}
ROMAN = re.compile(r"^[IVXLC]+$")
import pymorphy3
_m = pymorphy3.MorphAnalyzer()
def junk(t):
    """Частицы и междометия через дефис («Да-да», «Я-то») и римские цифры — не имена."""
    if ROMAN.match(t) or re.search(r"[A-Za-z]", t):
        return True
    if "-" in t:
        parts = [x for x in t.lower().split("-") if x]
        return all(_m.word_is_known(x) for x in parts) or len(parts[-1]) <= 2
    return False
spell = Counter()
paras = {}          # имя -> {(doc_idx, para_idx)}
for di, d in enumerate(RU):
    toks = d["tokens"]
    for i, t in enumerate(toks):
        if not t[:1].isupper() or len(t) < 3 or d["is_geo"][i] or not (d["is_name"][i] or not d["known"][i]) or junk(t):
            continue
        if d["paras"][d["para_of_tok"][i]]["k"] == "head":
            continue
        if i + 1 < len(toks) and toks[i + 1][:1].isupper() and d["is_name"][i + 1] and d["para_of_tok"][i + 1] == d["para_of_tok"][i]:
            continue
        l = ALIAS.get(d["lemmas"][i], d["lemmas"][i])
        if l in NOT_PERSON:
            continue
        paras.setdefault(l, set()).add((di, d["para_of_tok"][i]))
        spell[(l, t)] += 1
# склейка и исключения по показываемому имени (леммы незнакомых слов непредсказуемы)
_show_raw = {}
for l in paras:
    c = [(n, t) for (ll, t), n in spell.items() if ll == l]
    same = [(n, t) for n, t in c if t.lower().replace("ё", "е") == l.replace("ё", "е")]
    _show_raw[l] = max(same or c)[1]
NOT_D = {"петр", "пётр", "чак", "карлос", "майк", "адам", "альфонс", "люсьен", "ален", "эмиль", "джимми", "марселе", "марсель",
         "шартрский", "сен-жермен", "бельвиль", "булонском", "нотр-дам", "иоанн", "шарль", "бернар", "грета", "фонтенбло", "нил", "лодзи", "юбер"}
ALIAS_D = {"монтеня": "Монтень", "чингисхана": "Чингисхан", "гамлета": "Гамлет", "рембрандта": "Рембрандт", "ронсара": "Ронсар",
           "босха": "Босх", "павлова": "Павлов", "баха": "Бах", "голля": "де Голль", "гог": "Ван Гог",
           "гельдерлина": "Гельдерлин", "жуан": "Дон Жуан"}
merged = defaultdict(set); disp = {}
for l, ps in paras.items():
    raw = SHOW.get(l, _show_raw[l]); key = raw.lower().replace("ё", "е")
    if key in NOT_D or l in NOT_PERSON:
        continue
    name = ALIAS_D.get(key, raw); k2 = name.lower().replace("ё", "е")
    merged[k2] |= ps; disp[k2] = name
paras = dict(merged)
books_of = {l: {di for di, _ in ps} for l, ps in paras.items()}
def show(l):
    return disp[l]
pool = sorted([l for l in paras if len(books_of[l]) >= 3], key=lambda l: (-len(books_of[l]), -len(paras[l])))[:120]
N = len(pool)
Wm = np.zeros((N, N)); blk = defaultdict(set)
for i, l in enumerate(pool):
    for key in paras[l]:
        blk[key].add(i)
for mem in blk.values():
    m = sorted(mem)
    for a in range(len(m)):
        for c in range(a + 1, len(m)):
            Wm[m[a], m[c]] += 1; Wm[m[c], m[a]] += 1
deg = Wm.sum(1) + 1e-9
Sn = Wm / np.sqrt(np.outer(deg, deg))
vals, vecs = np.linalg.eigh(Sn)
K = 7
X = vecs[:, -K:]; X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
lab, _ = kmeans(X, K, n_init=20)
sizes = Counter(lab.tolist())
top_cl = [c for c, _ in sizes.most_common() if sizes[c] >= 3][:7]
cl = np.array([top_cl.index(c) if c in top_cl else -1 for c in lab])
tx = np.array([len(books_of[l]) for l in pool], float)
pos = island_layout(cl, tx)


def contexts(l, n=3):
    keys = sorted(paras[l], key=lambda k: (RU[k[0]]["year"] or 0, k[1]))
    step = max(1, len(keys) // n); out = []
    nm = show(l); stem = re.escape(nm.split()[-1][:max(3, len(nm.split()[-1]) - 2)])
    for di, pi in keys[::step][:n]:
        t = RU[di]["paras"][pi]["t"]; m = re.search(stem, t)
        out.append({"s": snip(t, m.start(), m.end()) if m else t[:230], "b": AIX[RU[di]["id"]]})
    return out


nodes = []
for i, l in enumerate(pool):
    bs = books_of[l]
    per = [sum(1 for di in bs if per_of(RU[di]["year"]) == p) for p in range(len(PER))]
    nb = [(int(j), int(Wm[i, j])) for j in np.argsort(-Wm[i])[:6] if Wm[i, j] > 0]
    bc = Counter(di for di, _ in paras[l])
    nodes.append({"name": show(l), "k": l, "n": len(bs), "np": len(paras[l]), "per": per, "cl": int(cl[i]),
                  "x": round(float(pos[i, 0]), 4), "y": round(float(pos[i, 1]), 4), "nb": [[j, w] for j, w in nb],
                  "books": [[AIX[RU[di]["id"]], k] for di, k in bc.most_common(10)], "ctx": contexts(l)})
keep = {(i, j) for i in range(N) for j in range(i + 1, N) if Wm[i, j] >= 2}
for i in range(N):
    if Wm[i].max() >= 1:
        j = int(np.argmax(Wm[i])); keep.add((min(i, j), max(i, j)))
edges = [[i, j, int(Wm[i, j])] for i, j in sorted(keep)]
clusters = []
for c in range(len(top_cl)):
    mem = sorted((i for i in range(N) if cl[i] == c), key=lambda i: -tx[i])
    clusters.append({"names": [nodes[i]["name"] for i in mem[:3]], "n": len(mem)})
OUT["net"] = {"nodes": nodes, "edges": edges, "clusters": clusters, "min_books": 3}

# ------------------------------------------------------------------ 4. темы: книги, где тема громче всего
F = S["fields"]
from compute import FIELDS  # те же списки слов, что в stats.json
loud = {}
for f, ws in FIELDS.items():
    ws = set(ws); rows = []
    for d in RU:
        n = len(d["tokens"])
        if n < 10000:
            continue
        k = sum(1 for l in d["lemmas"] if l in ws)
        rows.append((AIX[d["id"]], round(1000 * k / n, 2)))
    loud[f] = sorted(rows, key=lambda r: -r[1])[:5]
OUT["theme_loud"] = loud

json.dump(OUT, open(HERE / "explore.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("explore.json", round((HERE / "explore.json").stat().st_size / 1024), "KB")
if QA:
    print("палитра:", [(r["p"], [c[0] for c in r["c"][:6]], sum(c[2] for c in r["c"])) for r in pal])
    print("группы карты:", OUT["wgroups"])
    print("соседи:", {k: neighbors.get(k) for k in ["слон", "мать", "смерть", "женщина", "война", "клоун"]})
    print("сеть:", N, "рёбер", len(edges), "круги:", clusters)
    print("узлы:", [(n["name"], n["n"]) for n in nodes[:40]])
