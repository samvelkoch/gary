"""Статистика для отчёта «Ромен Гари на просвет» → analysis/stats.json

Подкорпуса (шкалы не смешиваются):
  ru  — русские переводы художественных текстов (own), по ним периоды, слова эпох, темы, словоискатель;
  fr  — французские оригиналы (own): предложение, словарь, сравнение с переводом;
  self — Гари о себе (интервью, эссе); oral — автосубтитры (только меры по словам).
Режим --qa: печать ключевых чисел и контекстов для проверки.
"""
import argparse, json, math, pickle, re
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
PERIODS = [("1937–1949", 1937, 1949), ("1952–1962", 1952, 1962), ("1963–1969", 1963, 1969), ("1970–1980", 1970, 1981)]
PER_NOTE = ["юность, война, первые романы", "дипломат, Гонкур за «Корни неба»", "Америка, Джин Сиберг, «Брат Океан»", "поздний Гари и Эмиль Ажар"]
SIGN_RU = {"Gary": "Гари", "Émile Ajar": "Ажар", "Shatan Bogat": "Шатан Богат", "Fosco Sinibaldi": "Фоско Синибальди"}
CONTENT_RU = {"NOUN", "VERB", "INFN", "ADJF", "ADJS", "ADVB", "PRTF", "PRTS", "GRND"}
CONTENT_FR = {"NOUN", "VERB", "ADJ", "ADV"}
# служебные слова, которые морфология относит к знаменательным частям речи
STOP_RU = set("""быть мочь который мой твой наш ваш свой этот тот весь такой какой самый сам один потому так там тут здесь
теперь уже ещё очень только даже тоже вот как где когда сейчас всегда никогда почему зачем тогда потом затем сразу вдруг
просто совсем ничто никто что кто себя свой каждый любой другой иной весьма столь стать иметь сказать есть бывать""".split())
STOP_FR = set("être avoir faire pouvoir aller dire vouloir falloir devoir tout même autre plus très bien aussi encore jamais toujours alors donc ainsi là ici".split())
WORD_RU = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*")

# смысловые поля (русский): леммы pymorphy; поля не пересекаются
FIELDS = {
    "Война": "война солдат армия немец фронт бой враг оружие пулемёт винтовка выстрел стрелять партизан офицер генерал танк бомба гестапо сопротивление лагерь",
    "Небо и полёт": "самолёт лётчик пилот эскадрилья полёт лететь аэродром бомбардировщик экипаж крыло парашют авиация взлёт штурман истребитель",
    "Мать и семья": "мать мама матушка отец сын дочь ребёнок семья брат сестра бабушка дядя тётя детство мальчик",
    "Женщина и любовь": "женщина любовь любить жена девушка поцелуй нежность красота возлюбленный любовница страсть ласка целовать обнять",
    "Смерть": "смерть умереть мёртвый труп могила кладбище убийство самоубийство похороны гроб покойник гибель погибнуть убить",
    "Смех и клоунада": "смех смеяться шутка клоун юмор смешной улыбка улыбаться насмешка ирония комедия цирк фокус паяц хохотать",
    "Звери": "слон собака животное зверь удав птица кошка лошадь обезьяна голубь лев пёс змея крыса зоопарк",
    "Бог и вера": "бог господь христос церковь молитва вера верить рай ад святой ангел дьявол грех чудо молиться",
    "Еврейство": "еврей еврейский гетто синагога раввин антисемит антисемитизм погром идиш жид талмуд иудей",
    "Человечность": "человечество человечность достоинство свобода надежда справедливость идеал братство цивилизация гуманизм благородство честь милосердие мечта",
    "Деньги": "деньги доллар франк миллион богатый заплатить платить цена банк купить продать нищета бедный долг богатство",
    "Власть и политика": "власть политика государство правительство президент революция режим диктатор коммунизм фашизм демократия партия министр посол дипломат",
    "Тело": "тело рука глаз лицо голова кожа живот кровь нос рот губа грудь нога зад плечо",
    "Искусство": "книга писатель роман писать литература поэт художник картина музыка искусство театр актёр кино фильм шедевр",
    "Природа": "небо звезда солнце море океан лес дерево гора ветер снег дождь земля река луна трава",
    "Страх и тревога": "страх бояться тревога ужас паника испугаться кошмар тоска отчаяние одиночество страдание боль",
}
FIELDS = {k: v.split() for k, v in FIELDS.items()}


def pct(a, q):
    return float(np.percentile(a, q)) if len(a) else None


def sent_len(s):
    return len(WORD_RU.findall(s)) if re.search(r"[А-Яа-яЁё]", s) else len(re.findall(r"[A-Za-zÀ-ÿŒœ]+", s))


def mattr(tokens, w=500):
    t = [x.lower() for x in tokens]
    if len(t) < w:
        return None
    vals = [len(set(t[i:i + w])) for i in range(0, len(t) - w + 1, w)]
    return float(np.mean(vals))


def log_odds(c1, c2, prior, a0=None, min_n=10, top=20, keep=None):
    """Monroe et al. 2008: log-odds с информативным априором Дирихле. Возвращает [(слово, z, n1, n2)]."""
    n1, n2 = sum(c1.values()), sum(c2.values())
    a = prior; a_sum = sum(a.values())
    sc = a_sum / (sum(prior.values()) or 1)
    out = []
    for w in set(c1) | set(c2):
        if keep and not keep(w):
            continue
        y1, y2 = c1.get(w, 0), c2.get(w, 0)
        if y1 < min_n:
            continue
        aw = a.get(w, 0.01)
        l1 = math.log((y1 + aw) / (n1 + a_sum - y1 - aw)); l2 = math.log((y2 + aw) / (n2 + a_sum - y2 - aw))
        var = 1 / (y1 + aw) + 1 / (y2 + aw)
        out.append((w, (l1 - l2) / math.sqrt(var), y1, y2))
    out.sort(key=lambda x: -x[1])
    return out[:top]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--qa", action="store_true"); A = ap.parse_args()
    docs = pickle.load(open(HERE / "corpus.pkl", "rb"))
    V = json.load(open(HERE / "voices.json"))
    import csv
    global MAN_COUNTS
    MAN_COUNTS = dict(Counter(r["role"] for r in csv.DictReader(open(HERE.parent / "texts" / "manifest.csv", encoding="utf-8"))))
    LOWER = {lg: {t for d in docs if d["lang"] == lg for t in d["tokens"] if t[:1].islower()} for lg in ("ru", "fr")}

    # имя: морфология, или слово ни разу не встречено со строчной, или лемма с заглавной в ≥ 70% употреблений (≥ 2 раз)
    capn = {lg: Counter() for lg in ("ru", "fr")}; alln = {lg: Counter() for lg in ("ru", "fr")}
    for d in docs:
        for t, l in zip(d["tokens"], d["lemmas"]):
            alln[d["lang"]][l] += 1
            if t[:1].isupper():
                capn[d["lang"]][l] += 1
    NAME_LEM = {lg: {l for l, n in alln[lg].items() if capn[lg][l] >= 2 and capn[lg][l] >= 0.7 * n} for lg in alln}
    # как имя пишется в тексте: самое частое написание с заглавной
    SPELL = defaultdict(Counter)
    for d in docs:
        for t, l in zip(d["tokens"], d["lemmas"]):
            if t[:1].isupper():
                SPELL[(d["lang"], l)][t] += 1
    def spell(lg, l):
        c = SPELL[(lg, l)]
        if not c:
            return l.capitalize()
        same = [(n, t) for t, n in c.items() if t.lower().replace("ё", "е") == l.replace("ё", "е")]
        return max(same)[1] if same else c.most_common(1)[0][0]

    def is_person_or_place(d, i):
        """Для списков имён: заглавная, не капсом; у русского — помета имени/фамилии/топонима или слово вне словаря."""
        t = d["tokens"][i]
        if not t[:1].isupper() or (len(t) > 1 and t.isupper() and len(t) > 4):
            return False
        if d["lang"] == "ru":
            return d["is_name"][i] or d["is_geo"][i] or not d["known"][i]
        return d["is_name"][i] or t.lower() not in LOWER["fr"]

    def is_name(d, i):
        t = d["tokens"][i]
        return d["is_name"][i] or (t[:1].isupper() and t.lower() not in LOWER[d["lang"]]) or d["lemmas"][i] in NAME_LEM[d["lang"]]

    ru = [d for d in docs if d["lang"] == "ru" and d["role"] == "own"]
    fr = [d for d in docs if d["lang"] == "fr" and d["role"] == "own"]
    self_ = [d for d in docs if d["role"] == "self"]
    atlas_docs = sorted(ru, key=lambda d: (d["year"] or 9999, d["work"])) + sorted(fr, key=lambda d: d["year"]) + \
        [d for d in self_ if d["work"] in ("La nuit sera calme", "Vie et mort d'Émile Ajar", "Le Sens de ma vie")]

    # ---------- общий фон для характерных слов: русские own ----------
    def content_lemmas(d):
        keep = CONTENT_RU if d["lang"] == "ru" else CONTENT_FR
        stop = STOP_RU if d["lang"] == "ru" else STOP_FR
        return [l for i, (l, p) in enumerate(zip(d["lemmas"], d["pos"])) if p in keep and not is_name(d, i) and len(l) > 1 and l not in stop]

    CL = {id(d): Counter(content_lemmas(d)) for d in ru + fr}
    RU_ALL = Counter(); [RU_ALL.update(CL[id(d)]) for d in ru]
    FR_ALL = Counter(); [FR_ALL.update(CL[id(d)]) for d in fr]

    # ---------- меры по книге ----------
    def book_metrics(d):
        body = [p for p in d["paras"] if p["k"] in ("narr", "dialog")]
        sl = [sent_len(s) for p in body for s in p["sents"] if sent_len(s) > 0]
        pw = [p["ntok"] for p in body if p["k"] == "narr"]
        w_body = sum(p["ntok"] for p in body) or 1
        w_dlg = sum(p["ntok"] for p in body if p["k"] == "dialog")
        text = "\n".join(p["t"] for p in body)
        n = len(d["tokens"]) or 1
        lem, pos = d["lemmas"], d["pos"]
        if d["lang"] == "ru":
            fp = sum(1 for l in lem if l in ("я", "мой"))
            nouns = sum(1 for p in pos if p == "NOUN"); verbs = sum(1 for p in pos if p in ("VERB", "INFN"))
            adjs = sum(1 for p in pos if p in ("ADJF", "ADJS"))
        else:
            fp = sum(1 for l, p in zip(lem, pos) if l in ("je", "me", "moi", "mon") and p in ("PRON", "DET"))
            nouns = sum(1 for p in pos if p == "NOUN"); verbs = sum(1 for p in pos if p == "VERB"); adjs = sum(1 for p in pos if p == "ADJ")
        dash_in = len(re.findall(r"\s[—–]\s", text))
        pm = {"!": text.count("!"), "?": text.count("?"), "…": text.count("…") + text.count("..."),
              ";": text.count(";"), ":": text.count(":"), "(": text.count("("), "— внутри фразы": dash_in}
        return {
            "words": n, "sents": len(sl), "paras": len(body),
            "sl_med": pct(sl, 50), "sl_q1": pct(sl, 25), "sl_q3": pct(sl, 75), "sl_mean": float(np.mean(sl)) if sl else None,
            "sl_long": round(100 * sum(1 for x in sl if x >= 40) / max(1, len(sl)), 2),
            "par_med": pct(pw, 50), "dlg": round(100 * w_dlg / w_body, 1),
            "mattr": mattr([t for t in d["tokens"]]),
            "fp": round(1000 * fp / n, 2), "nv": round(nouns / max(1, verbs), 3), "adj": round(100 * adjs / n, 2),
            "punct": {k: round(1000 * v / n, 2) for k, v in pm.items()},
        }

    # ---------- атлас ----------
    atlas = []
    for d in atlas_docs:
        m = book_metrics(d)
        # характерные слова: против остального подкорпуса своего языка
        if d["lang"] == "ru" and d["role"] == "own":
            rest = RU_ALL - CL[id(d)]
            char = log_odds(CL[id(d)], rest, RU_ALL, min_n=6, top=12)
        elif d["lang"] == "fr" and d["role"] == "own":
            rest = FR_ALL - CL[id(d)]
            char = log_odds(CL[id(d)], rest, FR_ALL, min_n=6, top=12)
        else:
            c = Counter(content_lemmas(d)); base = RU_ALL if d["lang"] == "ru" else FR_ALL
            char = log_odds(c, base, base, min_n=5, top=12)
        names = Counter()
        for i, t in enumerate(d["tokens"]):
            if len(t) > 2 and is_person_or_place(d, i) and d["paras"][d["para_of_tok"][i]]["k"] != "head":
                names[d["lemmas"][i] if d["lang"] == "ru" else t] += 1
        body = [p for p in d["paras"] if p["k"] in ("narr", "dialog")]
        first = next((s for p in body for s in p["sents"] if sent_len(s) >= 4), "")
        last = next((s for p in reversed(body) for s in reversed(p["sents"]) if sent_len(s) >= 3), "")
        # строение: длина каждого абзаца и тип; длинные книги сжимаются до 600 штрихов
        seq = [(p["ntok"], {"narr": 0, "dialog": 1, "head": 2}.get(p["k"], 0)) for p in d["paras"] if p["k"] in ("narr", "dialog", "head")]
        if len(seq) > 600:
            g = math.ceil(len(seq) / 600)
            seq = [(sum(x for x, _ in seq[i:i + g]) // g, Counter(k for _, k in seq[i:i + g]).most_common(1)[0][0]) for i in range(0, len(seq), g)]
        fields = {}
        if d["lang"] == "ru":
            lc = Counter(d["lemmas"])
            fields = {f: round(1000 * sum(lc[w] for w in ws) / max(1, len(d["tokens"])), 2) for f, ws in FIELDS.items()}
        atlas.append({
            "id": d["id"], "work": d["work"], "year": d["year"], "sign": d["sign"], "lang": d["lang"], "role": d["role"],
            "genre": d["genre"], "tr": d["tr"], **m,
            "char": [[w, round(z, 1), n1] for w, z, n1, _ in char],
            "names": [[spell(d["lang"], w) if d["lang"] == "ru" else w, n] for w, n in names.most_common(8)],
            "first": first[:320], "last": last[:320],
            "seq": [x for x, _ in seq], "seqk": "".join(str(k) for _, k in seq), "fields": fields,
        })
    for i, a in enumerate(atlas):
        a["i"] = i

    # ---------- периоды (русские переводы) ----------
    def per_of(y):
        if not y:
            return None
        for j, (_, a, b) in enumerate(PERIODS):
            if a <= y <= b:
                return j
    per_docs = defaultdict(list)
    for d in ru:
        p = per_of(d["year"])
        if p is not None:
            per_docs[p].append(d)
    per_tok = [sum(len(d["tokens"]) for d in per_docs[j]) for j in range(len(PERIODS))]
    PL = [Counter() for _ in PERIODS]
    for j in range(len(PERIODS)):
        for d in per_docs[j]:
            PL[j].update(CL[id(d)])
    eras = []
    for j in range(len(PERIODS)):
        rest = Counter(); [rest.update(PL[k]) for k in range(len(PERIODS)) if k != j]
        top = log_odds(PL[j], rest, RU_ALL, min_n=10, top=200)
        # слово должно встречаться хотя бы в двух книгах периода, иначе это слово одной книги
        top = [(w, z, n1, sum(1 for d in per_docs[j] if CL[id(d)].get(w, 0) > 0)) for w, z, n1, _ in top]
        top = [x for x in top if x[3] >= 2][:20]
        eras.append({"p": PERIODS[j][0], "note": PER_NOTE[j], "books": len(per_docs[j]), "tokens": per_tok[j],
                     "top": [[w, round(z, 1), n1, nb] for w, z, n1, nb in top]})

    # Гари против Ажара (русские переводы; темы, не голос)
    G = Counter(); Aj = Counter()
    for d in ru:
        (Aj if d["sign"] == "Émile Ajar" else G if d["sign"] == "Gary" else Counter()).update(CL[id(d)])
    ajar_words = log_odds(Aj, G, RU_ALL, min_n=12, top=25)
    gary_words = log_odds(G, Aj, RU_ALL, min_n=40, top=25)

    # ---------- частые слова ----------
    def top_pos(docs_, keepset, n=25):
        c = Counter(); tot = 0
        for d in docs_:
            tot += len(d["tokens"])
            for i, (l, p) in enumerate(zip(d["lemmas"], d["pos"])):
                if p in keepset and not is_name(d, i) and len(l) > 1:
                    c[l] += 1
        return [[w, n_, round(10000 * n_ / tot, 1)] for w, n_ in c.most_common(n)]
    STOPV_RU = {"быть", "мочь", "сказать", "стать", "иметь"}
    top_words = {
        "ru": {"nouns": top_pos(ru, {"NOUN"}), "verbs": [x for x in top_pos(ru, {"VERB", "INFN"}, 30) if x[0] not in STOPV_RU][:25],
               "adjs": top_pos(ru, {"ADJF", "ADJS"})},
        "fr": {"nouns": top_pos(fr, {"NOUN"}), "verbs": [x for x in top_pos(fr, {"VERB"}, 30) if x[0] not in ("être", "avoir", "faire", "pouvoir", "dire", "aller")][:25],
               "adjs": top_pos(fr, {"ADJ"})},
    }

    # ---------- смысловые поля ----------
    def field_rates(docs_):
        c = Counter(); tot = 0
        for d in docs_:
            c.update(d["lemmas"]); tot += len(d["tokens"])
        return {f: round(1000 * sum(c[w] for w in ws) / max(1, tot), 3) for f, ws in FIELDS.items()}, c
    fields_per = []
    for j in range(len(PERIODS)):
        r, _ = field_rates(per_docs[j]); fields_per.append(r)
    sign_groups = {"Гари": [d for d in ru if d["sign"] == "Gary"], "Ажар": [d for d in ru if d["sign"] == "Émile Ajar"],
                   "Шатан Богат": [d for d in ru if d["sign"] == "Shatan Bogat"]}
    fields_sign = {k: field_rates(v)[0] for k, v in sign_groups.items()}
    _, allc = field_rates(ru)
    fields_words = {f: [[w, allc[w]] for w in sorted(ws, key=lambda w: -allc[w])] for f, ws in FIELDS.items()}
    # в каждом поле — книга-лидер
    fields_lead = {}
    for f, ws in FIELDS.items():
        best = max((a for a in atlas if a["lang"] == "ru" and a["role"] == "own" and a["words"] >= 10000), key=lambda a: a["fields"].get(f, 0))
        fields_lead[f] = [best["i"], best["fields"][f]]

    # ---------- словоискатель (русский) ----------
    ru_atlas_ix = {a["id"]: a["i"] for a in atlas if a["lang"] == "ru" and a["role"] == "own"}
    lexc = defaultdict(lambda: [0] * len(PERIODS))
    lex_sign = defaultdict(Counter); lex_book = defaultdict(Counter); lex_total = Counter(); lex_ex = {}
    for d in ru:
        p = per_of(d["year"])
        for i, (l, pos) in enumerate(zip(d["lemmas"], d["pos"])):
            nm = is_name(d, i)
            if not (pos in CONTENT_RU or nm) or len(l) < 2:
                continue
            key = spell("ru", l) if nm else l
            lex_total[key] += 1
            if p is not None:
                lexc[key][p] += 1
            lex_sign[key][SIGN_RU[d["sign"]]] += 1
            lex_book[key][ru_atlas_ix[d["id"]]] += 1
    keys = [k for k, n in lex_total.items() if n >= 10]
    # примеры: первое предложение средней длины со словом (для слов ≥ 15 употреблений)
    need = {k for k in keys if lex_total[k] >= 40}
    for d in ru:
        if not need:
            break
        for p in d["paras"]:
            if p["k"] not in ("narr", "dialog"):
                continue
            for s in p["sents"]:
                L = sent_len(s)
                if not 7 <= L <= 30:
                    continue
                toks = WORD_RU.findall(s)
                for t in toks:
                    lw = t.lower()
                    lm = ru_parse_cache.get(lw)
                    if lm is None:
                        continue
                    k = spell("ru", lm) if (t[:1].isupper() and (lw not in LOWER["ru"] or lm in NAME_LEM["ru"])) else lm
                    if k in need and k not in lex_ex:
                        lex_ex[k] = [s[:170], ru_atlas_ix[d["id"]]]
                        need.discard(k)
    lex = {}
    for k in keys:
        lex[k] = [lex_total[k], lexc[k], [lex_sign[k].get(s, 0) for s in ("Гари", "Ажар", "Шатан Богат")],
                  [x for b, n in lex_book[k].most_common() for x in (b, n)], lex_ex.get(k)]
    sign_tokens = {s: sum(len(d["tokens"]) for d in v) for s, v in sign_groups.items()}

    # ---------- хронология ----------
    works = {}
    for a in atlas:
        if a["role"] != "own":
            continue
        w = works.setdefault(a["work"], {"work": a["work"], "year": a["year"], "sign": a["sign"], "ru": None, "fr": None, "genre": a["genre"]})
        w[a["lang"]] = a["i"]
    works = sorted(works.values(), key=lambda w: (w["year"] or 9999, w["work"]))

    # ---------- оригинал и перевод ----------
    pairs = []
    for fa in [a for a in atlas if a["lang"] == "fr" and a["role"] == "own"]:
        ra = next((a for a in atlas if a["lang"] == "ru" and a["work"] == fa["work"]), None)
        if ra:
            pairs.append({"work": fa["work"], "fr": fa["i"], "ru": ra["i"], "tr": ra["tr"],
                          "words": [fa["words"], ra["words"]], "sents": [fa["sents"], ra["sents"]],
                          "sl": [fa["sl_med"], ra["sl_med"]], "dlg": [fa["dlg"], ra["dlg"]],
                          "excl": [fa["punct"]["!"], ra["punct"]["!"]], "q": [fa["punct"]["?"], ra["punct"]["?"]],
                          "ell": [fa["punct"]["…"], ra["punct"]["…"]], "fp": [fa["fp"], ra["fp"]]})
    twin_docs = [d for d in docs if d["role"] == "twin"]
    twins = []
    for t in twin_docs:
        a = next(x for x in ru if x["work"] == t["work"])
        ma, mt = book_metrics(a), book_metrics(t)
        twins.append({"work": t["work"], "tr": [a["tr"] or "нет данных", t["tr"] or "нет данных"],
                      "words": [ma["words"], mt["words"]], "sl": [ma["sl_med"], mt["sl_med"]], "mattr": [ma["mattr"], mt["mattr"]],
                      "excl": [ma["punct"]["!"], mt["punct"]["!"]], "dlg": [ma["dlg"], mt["dlg"]],
                      "first": [next((s for p in a["paras"] if p["k"] != "head" for s in p["sents"]), "")[:200],
                                next((s for p in t["paras"] if p["k"] != "head" for s in p["sents"]), "")[:200]]})

    # ---------- рекорды (русские переводы и оригиналы) ----------
    longest = []
    for d in ru + fr:
        for p in d["paras"]:
            if p["k"] in ("narr", "dialog"):
                for s in p["sents"]:
                    longest.append((sent_len(s), s, d["work"], d["lang"]))
    longest.sort(key=lambda x: -x[0])
    rec_ru = next(x for x in longest if x[3] == "ru"); rec_fr = next(x for x in longest if x[3] == "fr")
    ru_at = [a for a in atlas if a["lang"] == "ru" and a["role"] == "own" and a["words"] >= 10000]
    fr_at = [a for a in atlas if a["lang"] == "fr" and a["role"] == "own"]
    rec = {
        "longest_ru": [rec_ru[0], rec_ru[1][:900], rec_ru[2]], "longest_fr": [rec_fr[0], rec_fr[1][:900], rec_fr[2]],
        "most_dialog": max(ru_at, key=lambda a: a["dlg"])["i"], "least_dialog": min(ru_at, key=lambda a: a["dlg"])["i"],
        "most_excl": max(ru_at, key=lambda a: a["punct"]["!"])["i"], "most_fp": max(ru_at, key=lambda a: a["fp"])["i"],
        "longest_sl": max(ru_at, key=lambda a: a["sl_med"])["i"], "shortest_sl": min(ru_at, key=lambda a: a["sl_med"])["i"],
        "richest": max(ru_at, key=lambda a: a["mattr"] or 0)["i"], "biggest": max(ru_at, key=lambda a: a["words"])["i"],
        "most_q": max(ru_at, key=lambda a: a["punct"]["?"])["i"],
    }

    # ---------- мифы: вердикт порогом (правила ниже заданы до расчёта) ----------
    myths = []
    fv = V["fr"]["variants"]; M200 = fv["narr"]["by_mfw"]["200"]
    va = fv["narr"]["v_ajar"]; va_np = fv["narr_nopron"]["v_ajar"]
    myths.append({"id": "ajar", "q": "Эмиль Ажар пишет другим голосом, чем Ромен Гари",
                  "v": {"differs": "yes", "within": "no", "border": "part", "unstable": "part"}[va] if va == va_np else "part",
                  "num": f"По-французски, по частым словам повествования: «Жизнь впереди» отстоит от двух романов Гари на {M200['ajar_gary']:.2f}, "
                         f"а два романа Гари друг от друга — на {M200['base'][0]:.2f}. Без местоимений: {fv['narr_nopron']['by_mfw']['200']['ajar_gary']:.2f} против "
                         f"{fv['narr_nopron']['by_mfw']['200']['base'][0]:.2f}. Держится при 100, 200 и 300 частых словах. Оговорка: Ажар — одна книга, Гари — две."})
    vs_ = fv["narr"]["v_sini"]
    myths.append({"id": "sini", "q": "Фоско Синибальди — ещё одна маска со своим голосом",
                  "v": {"differs": "yes", "within": "no", "border": "part", "unstable": "no"}[vs_],
                  "num": f"«Человек с голубкой» отстоит от романов Гари на {M200['sini_gary']:.2f} — это не дальше, чем романы Гари друг от друга ({M200['base'][0]:.2f}). "
                         f"По частым словам под этой маской Гари от самого себя не отличить."})
    pj = V["fr"]["projection"]["oral"]["to_book"]
    near_oral = min(pj, key=pj.get)
    myths.append({"id": "oral", "q": "В интервью Гари говорит языком «Обещания на рассвете»",
                  "v": "yes" if near_oral == "Promesse" and sorted(pj.values())[1] / pj["Promesse"] >= 1.05 else "part" if near_oral == "Promesse" else "no",
                  "num": f"Устная речь (радио 1975 и 1980, автосубтитры) ближе всего к «Обещанию»: {pj['Promesse']:.2f}; к «Корням неба» — {pj['Racines']:.2f}, "
                         f"к «Жизни впереди» — {pj['Vie']:.2f}. Частые слова устной речи — как у автобиографической прозы."})
    # мать в «Обещании»: доля слов «мать/мама/матушка» против медианы книг
    mom = lambda d: 1000 * sum(1 for l in d["lemmas"] if l in ("мать", "мама", "матушка")) / len(d["tokens"])
    pr = next(d for d in ru if d["work"] == "La Promesse de l'aube")
    med_mom = float(np.median([mom(d) for d in ru if len(d["tokens"]) >= 10000]))
    ratio = mom(pr) / med_mom
    myths.append({"id": "mother", "q": "«Обещание на рассвете» — книга о матери",
                  "v": "yes" if ratio >= 3 else "part" if ratio >= 1.5 else "no",
                  "num": f"Слова «мать», «мама», «матушка»: {mom(pr):.1f} на 1000 слов в «Обещании» против {med_mom:.1f} в типичной книге Гари — в {ratio:.0f} раз чаще."})
    war = [fields_per[j]["Война"] for j in range(len(PERIODS))]
    myths.append({"id": "war", "q": "Гари — прежде всего писатель войны",
                  "v": "part" if max(war) >= 1.5 * min(war) and war.index(max(war)) == 0 else ("yes" if min(war) >= 3 else "no"),
                  "num": "Слова поля «Война» на 1000 слов по периодам: " + ", ".join(f"{PERIODS[j][0]} — {war[j]:.1f}" for j in range(len(PERIODS))) +
                         ". Война — тема раннего Гари, к поздним книгам её доля " + ("падает" if war[-1] < war[0] else "не падает") + "."})
    ajf = next(a for a in fr_at if a["sign"] == "Émile Ajar"); gf = [a for a in fr_at if a["sign"] == "Gary"]
    sl_ratio = ajf["sl_med"] / min(a["sl_med"] for a in gf)
    mt_lower = ajf["mattr"] < min(a["mattr"] for a in gf)
    g_sl = ", ".join(f"{a['sl_med']:.0f}" for a in gf); g_mt = ", ".join(f"{a['mattr']:.0f}" for a in gf)
    myths.append({"id": "simple", "q": "Ажар пишет проще: короче фразы, беднее словарь",
                  "v": "yes" if sl_ratio <= 0.8 and mt_lower else ("part" if sl_ratio <= 0.9 or mt_lower else "no"),
                  "num": f"По-французски: типичная фраза «Жизни впереди» — {ajf['sl_med']:.0f} слов, у Гари — {g_sl}. "
                         f"Разных слов на 500: {ajf['mattr']:.0f} против {g_mt}."})
    S = V["ru"]["summary"]["narr"]["200"]
    mv = S["mav"]
    myths.append({"id": "translator", "q": "По-русски Ажар отличается от Гари только из-за переводчиков",
                  "v": "part" if mv["ga"] and mv["gg"] and mv["ga"]["med"] <= mv["gg"]["max"] else "no",
                  "num": f"У одного переводчика (Н. Мавлевич) «Голубчик» отстоит от её переводов Гари на {mv['ga']['med']:.2f}, а её переводы Гари друг от друга — на {mv['gg']['med']:.2f}. "
                         f"У разных переводчиков Ажар дальше от позднего Гари ({S['ajar_late']['med']:.2f}), чем два перевода одной книги друг от друга ({S['noise']['med']:.2f})."})
    nb = V["night"]
    myths.append({"id": "night", "q": "«Ночь будет спокойной» — разговор двоих",
                  "v": "none",
                  "num": f"Бонди принадлежит {100 * nb['bondy']['words'] / (nb['bondy']['words'] + nb['gary']['words']):.0f}% слов книги: {nb['bondy']['paras']} реплик, "
                         f"типичная — {nb['bondy']['len_med']:.0f} слов. У Гари типичный ответ — {nb['gary']['len_med']:.0f} слов, самый длинный — {nb['gary']['len_max']}. "
                         f"Кто на самом деле писал вопросы, по частым словам не проверить: вопрос и ответ — разные жанры речи."})

    # ---------- мир Гари (русские переводы): места, пантеон, полки ----------
    ru_ix = {d["id"]: ru_atlas_ix[d["id"]] for d in ru}
    ALIAS = {"голля": "голль"}  # pymorphy даёт две леммы одной фамилии
    geo = defaultdict(Counter); pers = defaultdict(Counter)
    for d in ru:
        b = ru_ix[d["id"]]; toks_ = d["tokens"]
        for i, t in enumerate(d["tokens"]):
            if not is_person_or_place(d, i) or d["paras"][d["para_of_tok"][i]]["k"] == "head":
                continue
            l = ALIAS.get(d["lemmas"][i], d["lemmas"][i])
            if d["is_geo"][i]:
                geo[l][b] += 1
            elif d["is_name"][i] and len(t) > 2:
                # имя перед фамилией и отчество не считаются отдельным человеком (канон 4.11)
                if i + 1 < len(toks_) and toks_[i + 1][:1].isupper() and (d["is_name"][i + 1] or not d["known"][i + 1]) \
                        and d["para_of_tok"][i + 1] == d["para_of_tok"][i]:
                    continue
                pers[l][b] += 1
    # исправления (писать в методике): написания одного имени и не-имена
    NOT_PERSON = {"господь", "бог", "мадам", "месье", "мадемуазель", "мисс", "мистер", "сэр", "синьор", "доктор", "роза",
                  # одиночные личные имена: это персонажи разных книг, а не один человек
                  "жан", "карл", "жанна", "мария", "марсель", "морис", "пьер", "жак", "поль", "джон", "джек", "джеймс", "мишель",
                  "анри", "виктор", "луи", "пьеро", "чарли", "билл", "джо", "том", "анна", "ганс", "фауст",
                  # «Франс» — Коллеж де Франс, «Эр Франс», «Франс-Суар», «Франс Пресс» (проверено по контекстам)
                  "франс"}
    SHOW = {"голль": "де Голль", "арк": "Жанна д'Арк", "нью-йорке": "Нью-Йорк"}
    def rank(D, min_books=3, top=40, drop=()):
        rows = []
        for l, c in D.items():
            if l in drop:
                continue
            nb = len(c)
            if nb >= min_books:
                rows.append([SHOW.get(l, spell("ru", l)), nb, sum(c.values()), [[b, n] for b, n in c.most_common(12)]])
        rows.sort(key=lambda r: (-r[1], -r[2]))
        return rows[:top]
    places = rank(geo, 3, 45)
    pantheon = rank(pers, 4, 40, NOT_PERSON)

    SHELVES = {
        "Звери": "слон собака пёс удав змея питон птица кошка кот лошадь конь обезьяна горилла голубь лев тигр крыса мышь медведь волк лиса бык корова осёл верблюд кит акула черепаха попугай орёл ворона бабочка",
        "Напитки": "вино водка коньяк шампанское пиво кофе ром бренди мартини текила абсент кальвадос портвейн херес вермут сок молоко лимонад джин виски",
        "Транспорт": "самолёт автомобиль такси поезд корабль пароход лодка велосипед мотоцикл автобус грузовик джип кадиллак трамвай метро вертолёт яхта телега повозка карета лифт",
        "Оружие": "револьвер пистолет винтовка пулемёт ружьё нож граната бомба кольт карабин штык кинжал сабля пушка патрон",
    }
    SHELVES = {k: v.split() for k, v in SHELVES.items()}
    # правила омонимов: «чай» (частица) не входит; «джин» — только со строчной (Джин Сиберг);
    # «виски» — по словоформе, если перед ней нет «в/на/по/к/у/его/её/свои» (висок)
    shelf = {k: defaultdict(Counter) for k in SHELVES}
    ex_shelf = {}
    for d in ru:
        b = ru_ix[d["id"]]
        toks = d["tokens"]
        for i, (t, l) in enumerate(zip(toks, d["lemmas"])):
            tl = t.lower()
            for k, ws in SHELVES.items():
                key = None
                if l in ws and l not in ("джин", "виски"):
                    key = l
                elif l == "джин" and t[:1].islower():
                    key = "джин"
                elif tl == "виски" and k == "Напитки" and (i == 0 or toks[i - 1].lower() not in ("в", "на", "по", "к", "у", "его", "её", "ее", "свои", "мои", "ему", "ей")):
                    key = "виски"
                if key and key in ws:
                    shelf[k][key][b] += 1
                    if key not in ex_shelf:
                        p = d["paras"][d["para_of_tok"][i]]
                        s = next((s for s in p["sents"] if t in s), p["t"])
                        if 5 <= sent_len(s) <= 35:
                            ex_shelf[key] = [s[:220], b]
    shelves = {}
    for k, D in shelf.items():
        rows = [[w, len(c), sum(c.values()), [[b, n] for b, n in c.most_common(6)], ex_shelf.get(w)] for w, c in D.items()]
        rows.sort(key=lambda r: (-r[2]))
        shelves[k] = rows
    # аудит по сырому тексту: основа слова в тексте против засчитанного (канон 4.11)
    audit = []
    raw = "\n".join(p["t"].lower() for d in ru for p in d["paras"])
    for k, ws in SHELVES.items():
        for w in ws:
            stem = w if len(w) <= 5 else w[:-1]
            stem = stem.replace("ё", "[её]")
            n_raw = len(re.findall(r"\b" + stem + r"[а-яё]{0,3}\b", raw))
            n_cnt = sum(r[2] for r in shelves[k] if r[0] == w)
            if n_raw > 1.6 * n_cnt + 5:
                audit.append([k, w, n_cnt, n_raw])

    # ---------- главное коротко ----------
    tot_ru = sum(len(d["tokens"]) for d in ru); tot_fr = sum(len(d["tokens"]) for d in fr)
    out = {
        "periods": [p[0] for p in PERIODS], "per_note": PER_NOTE, "per_tokens": per_tok,
        "overview": {"ru_texts": len(ru), "ru_words": tot_ru, "fr_texts": len(fr), "fr_words": tot_fr,
                     "self_words": sum(len(d["tokens"]) for d in self_),
                     "oral_words": sum(len(d["tokens"]) for d in docs if d["role"] == "oral"),
                     "twin_words": sum(len(d["tokens"]) for d in twin_docs),
                     "works": len(works), "translators": len({t.strip() for d in ru if d["tr"] and d["tr"] != "нет данных" for t in d["tr"].split(",")}),
                     "signs": sorted({SIGN_RU[d["sign"]] for d in ru + fr}),
                     "ru_by_sign": {SIGN_RU[s]: sum(len(d["tokens"]) for d in ru if d["sign"] == s) for s in {d["sign"] for d in ru}},
                     "ru_by_genre": dict(Counter(d["genre"] for d in ru)), "mattr_ru": mattr([t for d in ru for t in d["tokens"]]),
                     "files": MAN_COUNTS},
        "atlas": atlas, "works": works, "eras": eras, "ajar_words": [[w, round(z, 1), a, b] for w, z, a, b in ajar_words],
        "gary_words": [[w, round(z, 1), a, b] for w, z, a, b in gary_words],
        "top_words": top_words, "fields": {"names": list(FIELDS), "per": fields_per, "sign": fields_sign, "words": fields_words, "lead": fields_lead},
        "lex": lex, "sign_tokens": sign_tokens, "places": places, "pantheon": pantheon, "shelves": shelves, "shelf_audit": audit, "pairs": pairs, "twins": twins, "records": rec, "myths": myths,
    }
    json.dump(out, open(HERE / "stats.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("stats.json", round((HERE / "stats.json").stat().st_size / 1024), "KB; лемм в словоискателе", len(lex), "с примером", len(lex_ex))
    if A.qa:
        for m in myths:
            print(f"[{m['v']}] {m['q']}\n     {m['num']}")
        for e in eras:
            print(e["p"], e["books"], [f"{w}({nb})" for w, z, n, nb in e["top"][:14]])
        print("Ажар:", [w for w, *_ in ajar_words[:20]]); print("Гари:", [w for w, *_ in gary_words[:20]])
        print("поля по периодам:", {f: [fields_per[j][f] for j in range(4)] for f in list(FIELDS)[:16]})
        for a in atlas:
            print(f"{a['i']:>2} {a['lang']} {a['year']} {a['work'][:30]:30} sl={a['sl_med']} dlg={a['dlg']} mattr={a['mattr'] and round(a['mattr'])} fp={a['fp']} !={a['punct']['!']} names={[n for n, _ in a['names'][:4]]}")
        for p in pairs:
            print(p)
        print(rec)
        print("МЕСТА:", [(r[0], r[1]) for r in places[:30]])
        print("ПАНТЕОН:", [(r[0], r[1]) for r in pantheon[:40]])
        for k, rows in shelves.items():
            print(k, [(r[0], r[2], r[1]) for r in rows[:25]])
        print("АУДИТ (по тексту больше засчитанного):", audit)


ru_parse_cache = {}
MAN_COUNTS = {}
if __name__ == "__main__":
    # кеш лемм по словоформе для примеров словоискателя
    import pymorphy3
    _m = pymorphy3.MorphAnalyzer()

    class _C(dict):
        def get(self, w, default=None):
            if w not in self:
                self[w] = _m.parse(w)[0].normal_form
            return self[w]
    ru_parse_cache = _C()
    main()
