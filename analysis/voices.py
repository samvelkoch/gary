"""Голоса: Гари, Ажар, Синибальди, Богат — стилометрия по частым словам (Delta Барроуза).

Правила (записаны до первого прогона, канон 5.4):
  * шкалы не смешиваются: французский вердикт — по французской базе, русский — по русской;
  * сравниваются книги, а не куски одной книги: расстояние книга↔книга = среднее Delta по всем парам кусков;
  * основной вариант — только повествование (абзацы без реплик), без имён собственных, словоформы;
    дополнительные варианты — без личных и притяжательных местоимений (влияние рассказчика) и с диалогами;
  * частые слова и z-оценки — на сбалансированной выборке: одинаковое число кусков от каждой книги;
  * устойчивость: 100, 200 и 300 частых слов; вердикт ставится, только если совпадает на всех трёх.
Вердикт для пары «псевдоним ↔ Гари» при базе B = расстояния между книгами Гари:
  D > max(B) × 1,10  → «отличается»;  D ≤ max(B) → «в пределах разброса Гари»;  иначе → «на границе».
«Ночь будет спокойной»: вопросы Бонди — только описательно, без вердикта (другой регистр речи).
Вход: corpus.pkl. Выход: voices.json.
"""
import json, pickle, re
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
MFW_SET = (100, 200, 300)
MAIN = 200
MARGIN = 1.10


def verdict(d, base):
    mx = max(base)
    if d > mx * MARGIN:
        return "differs"
    if d <= mx:
        return "within"
    return "border"


PRON_RU = {"я", "ты", "он", "она", "оно", "мы", "вы", "они", "мой", "твой", "наш", "ваш", "свой", "себя"}
PRON_FR = {"je", "me", "moi", "tu", "te", "toi", "il", "elle", "lui", "nous", "vous", "ils", "elles", "leur", "eux", "se", "soi",
           "mon", "ton", "son", "notre", "votre", "leurs", "mien", "tien", "sien"}


LOWER_SEEN = {}


def stream(d, kinds=("narr",), drop_pron=False):
    """Словоформы документа из абзацев нужного типа, без имён собственных.
    Имя: разметка морфологии (Name/Surn/Patr у pymorphy, PROPN у spaCy) или слово с заглавной,
    которое в корпусе этого языка ни разу не встречается со строчной."""
    seen = LOWER_SEEN[d["lang"]]
    keep_para = {i for i, p in enumerate(d["paras"]) if p["k"] in kinds and p.get("spk", "gary") in ("gary", None)}
    out = []
    lang = d["lang"]
    for t, l, pos, nm, pi in zip(d["tokens"], d["lemmas"], d["pos"], d["is_name"], d["para_of_tok"]):
        if pi not in keep_para or nm:
            continue
        if t[:1].isupper() and t.lower() not in seen:
            continue
        if drop_pron:
            if lang == "ru" and (l in PRON_RU or pos == "NPRO"):
                continue
            if lang == "fr" and (l in PRON_FR or pos == "PRON"):
                continue
        out.append(t.lower().replace("ё", "е").replace("’", "'"))
    return out


def chunks(words, size):
    n = len(words) // size
    return [words[i * size:(i + 1) * size] for i in range(n)]


def delta_space(books, size, mfw_n, seed_k=None):
    """books: {name: [words]} → (names_per_chunk, Z, mfw). z-оценки по сбалансированной выборке."""
    ch = {b: chunks(w, size) for b, w in books.items()}
    ch = {b: c for b, c in ch.items() if len(c) >= 1}
    k = seed_k or max(1, min(len(c) for c in ch.values() if len(c) >= 2))
    # сбалансированная выборка: k равномерно разнесённых кусков от каждой книги
    bal = []
    for b, c in ch.items():
        idx = np.linspace(0, len(c) - 1, min(k, len(c))).round().astype(int)
        bal += [c[i] for i in sorted(set(idx))]
    cnt = Counter()
    for c in bal:
        cnt.update(c)
    mfw = [w for w, _ in cnt.most_common(mfw_n)]
    ix = {w: i for i, w in enumerate(mfw)}

    def freq(c):
        v = np.zeros(len(mfw))
        for w in c:
            j = ix.get(w)
            if j is not None:
                v[j] += 1
        return v / len(c)

    Fb = np.array([freq(c) for c in bal])
    mu, sd = Fb.mean(0), Fb.std(0) + 1e-12
    labels, rows = [], []
    for b, c in ch.items():
        for i, x in enumerate(c):
            labels.append((b, i)); rows.append(freq(x))
    Z = (np.array(rows) - mu) / sd
    return labels, Z, mfw, k


def pair_delta(Z):
    return np.abs(Z[:, None, :] - Z[None, :, :]).mean(-1)


def book_dist(labels, D):
    names = sorted({b for b, _ in labels}, key=lambda x: [b for b, _ in labels].index(x))
    idx = defaultdict(list)
    for i, (b, _) in enumerate(labels):
        idx[b].append(i)
    M = {}
    for a in names:
        for b in names:
            A, B = idx[a], idx[b]
            if a == b:
                sub = D[np.ix_(A, A)]
                m = sub[~np.eye(len(A), dtype=bool)].mean() if len(A) > 1 else np.nan
            else:
                m = D[np.ix_(A, B)].mean()
            M[(a, b)] = float(m)
    return names, M


def pca2(Z):
    Zc = Z - Z.mean(0)
    U, S, Vt = np.linalg.svd(Zc, full_matrices=False)
    xy = U[:, :2] * S[:2]
    ev = (S ** 2) / (S ** 2).sum()
    return xy, ev[:2]


def main():
    docs = pickle.load(open(HERE / "corpus.pkl", "rb"))
    for lg in ("ru", "fr"):
        LOWER_SEEN[lg] = {t for d in docs if d["lang"] == lg for t in d["tokens"] if t[:1].islower()}
    out = {"rule": {"margin": MARGIN, "mfw": list(MFW_SET), "main_mfw": MAIN}}

    # ================= французский: оригиналы =================
    FR_BOOKS = {
        "Promesse": ("La Promesse de l'aube", "Gary", 1960),
        "Racines": ("Les Racines du ciel", "Gary", 1956),
        "Vie": ("La Vie devant soi", "Ajar", 1975),
        "Colombe": ("L'Homme à la colombe", "Sinibaldi", 1958),
    }
    key_of = {"La Promesse de l'aube": "Promesse", "Les Racines du ciel": "Racines",
              "La Vie devant soi": "Vie", "L'Homme à la colombe": "Colombe"}
    fr = {key_of[d["work"]]: d for d in docs if d["lang"] == "fr" and d["role"] == "own"}
    size_fr = 3000
    fr_res = {}
    for variant, kinds, dp in [("narr", ("narr",), False), ("narr_nopron", ("narr",), True), ("all", ("narr", "dialog"), False)]:
        books = {k: stream(fr[k], kinds, dp) for k in FR_BOOKS}
        res = {}
        for n in MFW_SET:
            labels, Z, mfw, kbal = delta_space(books, size_fr, n)
            D = pair_delta(Z)
            names, M = book_dist(labels, D)
            base = [M[("Promesse", "Racines")]]
            res[n] = {
                "M": {f"{a}|{b}": round(v, 4) for (a, b), v in M.items()},
                "ajar_gary": round((M[("Vie", "Promesse")] + M[("Vie", "Racines")]) / 2, 4),
                "sini_gary": round((M[("Colombe", "Promesse")] + M[("Colombe", "Racines")]) / 2, 4),
                "base": [round(x, 4) for x in base],
                "chunks": dict(Counter(b for b, _ in labels)), "balanced_k": kbal,
            }
            res[n]["v_ajar"] = verdict(res[n]["ajar_gary"], base)
            res[n]["v_sini"] = verdict(res[n]["sini_gary"], base)
            if variant == "narr" and n == MAIN:
                xy, ev = pca2(Z)
                # ближайшая чужая книга для каждого куска
                near = []
                for i, (b, j) in enumerate(labels):
                    other = [(D[i, q], labels[q][0]) for q in range(len(labels)) if labels[q][0] != b]
                    near.append(min(other)[1])
                res[n]["map"] = [[b, j, round(float(x), 3), round(float(y), 3), nb] for (b, j), (x, y), nb in zip(labels, xy, near)]
                res[n]["ev"] = [round(float(e), 3) for e in ev]
                res[n]["mfw_list"] = mfw[:60]
        vs = {res[n]["v_ajar"] for n in MFW_SET}
        vs2 = {res[n]["v_sini"] for n in MFW_SET}
        fr_res[variant] = {"by_mfw": res, "v_ajar": vs.pop() if len(vs) == 1 else "unstable",
                           "v_sini": vs2.pop() if len(vs2) == 1 else "unstable"}
    out["fr"] = {"books": FR_BOOKS, "size": size_fr, "variants": fr_res,
                 "words_narr": {k: len(stream(fr[k])) for k in FR_BOOKS},
                 "words_all": {k: len(fr[k]["tokens"]) for k in FR_BOOKS}}

    # устная и отредактированная речь — проекция в то же пространство (в расчёт вердиктов не входит)
    oral = [d for d in docs if d["role"] == "oral"]
    oral_words = []
    for d in oral:
        oral_words += [t.lower().replace("’", "'") for t in d["tokens"]]
    sens = next(d for d in docs if d["work"] == "Le Sens de ma vie")
    books = {k: stream(fr[k]) for k in FR_BOOKS}
    labels, Z, mfw, _ = delta_space(books, size_fr, MAIN)
    ix = {w: i for i, w in enumerate(mfw)}
    # те же μ, σ: пересчёт из сбалансированной выборки
    ch = {b: chunks(w, size_fr) for b, w in books.items()}
    k = min(len(c) for c in ch.values())
    bal = []
    for b, c in ch.items():
        idx = np.linspace(0, len(c) - 1, k).round().astype(int)
        bal += [c[i] for i in sorted(set(idx))]

    def freq(c):
        v = np.zeros(len(mfw))
        for w in c:
            j = ix.get(w)
            if j is not None:
                v[j] += 1
        return v / len(c)
    Fb = np.array([freq(c) for c in bal]); mu, sd = Fb.mean(0), Fb.std(0) + 1e-12
    extra = {"oral": chunks(oral_words, size_fr), "sens": chunks(stream(sens, ("narr", "dialog")), size_fr)}
    D0 = pair_delta(Z)
    names, M = book_dist(labels, D0)
    proj = {}
    for nm, cs in extra.items():
        if not cs:
            continue
        Ze = (np.array([freq(c) for c in cs]) - mu) / sd
        dd = np.abs(Ze[:, None, :] - Z[None, :, :]).mean(-1)
        proj[nm] = {"n_chunks": len(cs),
                    "to_book": {b: round(float(dd[:, [i for i, l in enumerate(labels) if l[0] == b]].mean()), 4) for b in FR_BOOKS}}
    out["fr"]["projection"] = proj

    # ================= русский: переводы =================
    ru_own = [d for d in docs if d["lang"] == "ru" and d["role"] in ("own", "twin")]
    size_ru = 5000
    # рассказы 1962 одного переводчика — одна «книга»
    stories = [d for d in ru_own if d["genre"] == "рассказ" and d["role"] == "own"]
    books, meta = {}, {}
    for d in ru_own:
        if d["genre"] == "рассказ":
            continue
        key = d["work"] + (" [2]" if d["role"] == "twin" else "")
        books[key] = d
        meta[key] = {"work": d["work"], "sign": d["sign"], "year": d["year"], "tr": d["tr"] or "нет данных", "role": d["role"]}
    by_tr = defaultdict(list)
    for d in stories:
        by_tr[d["tr"] or "нет данных"].append(d)
    for tr, ds in by_tr.items():
        key = f"Рассказы 1962 ({tr})"
        books[key] = ds
        meta[key] = {"work": key, "sign": "Gary", "year": 1962, "tr": tr, "role": "own"}

    def words_of(v, kinds, dp):
        if isinstance(v, list):
            w = []
            for d in v:
                w += stream(d, kinds, dp)
            return w
        return stream(v, kinds, dp)

    ru_res = {}
    for variant, kinds, dp in [("narr", ("narr",), False), ("narr_nopron", ("narr",), True), ("all", ("narr", "dialog"), False)]:
        W = {k: words_of(v, kinds, dp) for k, v in books.items()}
        W = {k: w for k, w in W.items() if len(w) >= 2 * size_ru}   # не меньше двух кусков
        res = {}
        for n in MFW_SET:
            labels, Z, mfw, kbal = delta_space(W, size_ru, n)
            D = pair_delta(Z)
            names, M = book_dist(labels, D)
            res[n] = {"names": names, "M": [[round(M[(a, b)], 4) for b in names] for a in names], "balanced_k": kbal}
            if variant == "narr" and n == MAIN:
                xy, ev = pca2(Z)
                res[n]["map"] = [[b, j, round(float(x), 3), round(float(y), 3)] for (b, j), (x, y) in zip(labels, xy)]
                res[n]["ev"] = [round(float(e), 3) for e in ev]
        ru_res[variant] = res
    out["ru"] = {"meta": meta, "size": size_ru, "variants": ru_res}

    # сводки по русскому варианту: шум перевода, Ажар ↔ поздний Гари, один переводчик
    def summarize(res):
        names = res["names"]; Mx = res["M"]; I = {b: i for i, b in enumerate(names)}
        d = lambda a, b: Mx[I[a]][I[b]]
        twins = [(b.replace(" [2]", ""), b) for b in names if b.endswith(" [2]") and b.replace(" [2]", "") in I]
        noise = [d(a, b) for a, b in twins]
        gary = [b for b in names if meta[b]["sign"] == "Gary" and meta[b]["role"] == "own"]
        late = [b for b in gary if (meta[b]["year"] or 0) >= 1970]
        ajar = [b for b in names if meta[b]["sign"] == "Émile Ajar"]
        bogat = [b for b in names if meta[b]["sign"] == "Shatan Bogat"]
        gg_late = [d(a, b) for i, a in enumerate(late) for b in late[i + 1:]]
        gg_all = [d(a, b) for i, a in enumerate(gary) for b in gary[i + 1:]]
        aj_late = [d(a, b) for a in ajar for b in late]
        aa = [d(a, b) for i, a in enumerate(ajar) for b in ajar[i + 1:]]
        bo_late = [d(a, b) for a in bogat for b in late]
        # один переводчик — Мавлевич
        mav_g = [b for b in names if "Мавлевич" in meta[b]["tr"] and meta[b]["sign"] == "Gary"]
        mav_a = [b for b in names if "Мавлевич" in meta[b]["tr"] and meta[b]["sign"] == "Émile Ajar"]
        mav_gg = [d(a, b) for i, a in enumerate(mav_g) for b in mav_g[i + 1:] if a.replace(" [2]", "") != b.replace(" [2]", "")]
        mav_ga = [d(a, b) for a in mav_a for b in mav_g]
        # переводчик против времени: пары книг Гари
        pairs = []
        for i, a in enumerate(gary):
            for b in gary[i + 1:]:
                ta, tb = meta[a]["tr"], meta[b]["tr"]
                if "нет данных" in (ta, tb):
                    same = None
                else:
                    same = bool(set(re.split(r",\s*", ta)) & set(re.split(r",\s*", tb)))
                pairs.append([a, b, d(a, b), abs((meta[a]["year"] or 0) - (meta[b]["year"] or 0)), same])
        st = lambda v: {"n": len(v), "min": round(min(v), 4), "med": round(float(np.median(v)), 4), "max": round(max(v), 4)} if v else None
        return {"twins": [[a, b, round(d(a, b), 4)] for a, b in twins], "noise": st(noise),
                "gg_late": st(gg_late), "gg_all": st(gg_all), "ajar_late": st(aj_late), "ajar_ajar": st(aa), "bogat_late": st(bo_late),
                "ajar_books": ajar, "late_books": late,
                "ajar_each": {a: round(float(np.mean([d(a, b) for b in late])), 4) for a in ajar},
                "mav": {"gary": mav_g, "ajar": mav_a, "gg": st(mav_gg), "ga": st(mav_ga)},
                "pairs": [[a, b, round(x, 4), g, s] for a, b, x, g, s in pairs],
                "v_ajar": verdict(float(np.mean(aj_late)), gg_late) if aj_late and gg_late else None,
                "v_ajar_vs_noise": (verdict(float(np.mean(aj_late)), noise) if noise and aj_late else None)}

    out["ru"]["summary"] = {v: {n: summarize(out["ru"]["variants"][v][n]) for n in MFW_SET} for v in out["ru"]["variants"]}
    for v, S in out["ru"]["summary"].items():
        vv = {S[n]["v_ajar"] for n in MFW_SET}
        out["ru"]["summary"][v]["v_ajar"] = vv.pop() if len(vv) == 1 else "unstable"

    # проверка перевода: порядок трёх расстояний (Promesse, Racines, Vie) по-французски и по-русски
    trio_ru = {"Promesse": "La Promesse de l'aube", "Racines": "Les Racines du ciel", "Vie": "La Vie devant soi"}
    check = {}
    for n in MFW_SET:
        f = out["fr"]["variants"]["narr"]["by_mfw"][n]["M"]
        r = out["ru"]["variants"]["narr"][n]; I = {b: i for i, b in enumerate(r["names"])}
        prs = [("Promesse", "Racines"), ("Promesse", "Vie"), ("Racines", "Vie")]
        fv = [f[f"{a}|{b}"] for a, b in prs]
        rv = [r["M"][I[trio_ru[a]]][I[trio_ru[b]]] for a, b in prs] if all(trio_ru[x] in I for x in trio_ru) else None
        check[n] = {"pairs": ["–".join(p) for p in prs], "fr": fv, "ru": rv,
                    "same_order": (rv is not None and list(np.argsort(fv)) == list(np.argsort(rv)))}
    out["translation_check"] = check

    # ================= «Ночь будет спокойной»: описательно =================
    night = next(d for d in docs if d["work"] == "La nuit sera calme")
    sp = defaultdict(lambda: {"paras": 0, "words": 0, "q": 0, "ty": 0, "ya": 0})
    for p in night["paras"]:
        s = sp[p["spk"]]
        s["paras"] += 1; s["words"] += p["ntok"]; s["q"] += p["t"].count("?")
        low = p["t"].lower()
        s["ty"] += len(re.findall(r"\b(ты|тебя|тебе|тобой|твой|твоя|твоё|твои|твоих|твоей|твоего)\b", low))
        s["ya"] += len(re.findall(r"\b(я|меня|мне|мной|мой|моя|моё|мои|моих|моей|моего)\b", low))
    lens = defaultdict(list)
    for p in night["paras"]:
        lens[p["spk"]].append(p["ntok"])
    out["night"] = {k: {**v, "len_med": float(np.median(lens[k])), "len_max": int(max(lens[k]))} for k, v in sp.items()}
    # самые длинные ответы Гари и самые короткие вопросы Бонди — для примеров
    gp = sorted([p for p in night["paras"] if p["spk"] == "gary"], key=lambda p: -p["ntok"])
    bq = [p["t"] for p in night["paras"] if p["spk"] == "bondy" and 6 <= p["ntok"] <= 18]
    out["night"]["examples_q"] = bq[:6]
    out["night"]["longest_answer_words"] = gp[0]["ntok"]

    json.dump(out, open(HERE / "voices.json", "w"), ensure_ascii=False, indent=0)
    # печать для проверки
    print("FR:", {v: (fr_res[v]["v_ajar"], fr_res[v]["v_sini"]) for v in fr_res})
    for v in fr_res:
        r = fr_res[v]["by_mfw"][MAIN]
        print(f"  {v}: база P–R {r['base']}  Ажар–Гари {r['ajar_gary']}  Синибальди–Гари {r['sini_gary']}  куски {r['chunks']} k={r['balanced_k']}")
        print("     внутри книг:", {b: r["M"][f"{b}|{b}"] for b in FR_BOOKS})
    print("проекция:", proj)
    for v in out["ru"]["summary"]:
        S = out["ru"]["summary"][v][MAIN]
        print(f"RU {v}: шум {S['noise']}  GG поздн {S['gg_late']}  Ажар–поздн {S['ajar_late']}  Богат {S['bogat_late']}  вердикт {out['ru']['summary'][v]['v_ajar']} / vs шум {S['v_ajar_vs_noise']}")
        print("     Мавлевич:", S["mav"])
    print("проверка перевода:", check)
    print("Ночь:", {k: {kk: vv for kk, vv in v.items()} for k, v in out["night"].items() if k in ("gary", "bondy")})


if __name__ == "__main__":
    main()
