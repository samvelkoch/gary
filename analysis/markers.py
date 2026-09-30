"""Маркеры иронической манеры (не «ирония», а её следы) → analysis/markers.json

Правила записаны до первого прогона:
  1. Столкновение высокого и низкого: фраза, где есть слово из «высокого» списка и слово из «низкого».
     Нулевая модель: внутри книги метки «низкое» перемешиваются между фразами одной группы длины
     (децили по числу слов), 300 перестановок. Отношение = наблюдаемое / среднее по перестановкам.
     Вывод: ≥ 1,15 — «чаще случайного», ≤ 0,90 — «реже», между — «не систематический приём» (как звук в каноне);
     считается только для книг, где ожидаемое число столкновений ≥ 5.
  2. Иронические кавычки: 1–3 слова в «ёлочках» или "лапках", первое слово со строчной буквы,
     внутри абзаца повествования (не реплика, не начало абзаца). На 10 000 слов.
  3. Притворная уверенность: «разумеется», «конечно», «как известно»… в повествовании. На 10 000 слов.
Подкорпуса не смешиваются: русские переводы и французские оригиналы — отдельно.
Режим --qa: примеры по каждому маркеру для чтения глазами.
"""
import argparse, json, pickle, random, re, functools
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
N_PERM, RATIO_UP, RATIO_DOWN, MIN_EXP = 300, 1.15, 0.90, 5

HIGH_RU = set("""человечество человечность достоинство цивилизация идеал братство гуманизм гуманист благородство благородный честь
милосердие справедливость свобода надежда духовный вечность бессмертие душа святой святыня величие великий героизм герой подвиг
родина отечество демократия прогресс культура красота истина вера благородство возвышенный священный идеализм""".split())
LOW_RU = set("""зад задница жопа дерьмо говно моча мочиться пердеть блевать рвота сортир унитаз клозет уборная шлюха проститутка бордель
вонь вонять вонючий вшивый вошь сопля плевать плевок отрыжка понос кишка кишки свинья сволочь мерзавец подонок мразь
пьяный пьяница блевотина испражнение навоз помойка отбросы грязь мусор""".split())
HIGH_FR = set("""humanité humain dignité civilisation idéal fraternité humanisme humaniste noblesse noble honneur miséricorde justice
liberté espoir espérance spirituel éternité immortalité âme sacré saint grandeur grand héroïsme héros patrie progrès culture
beauté vérité foi sublime idéalisme""".split()) - {"grand", "humain"}  # слишком частые в обычном значении
LOW_FR = set("""cul merde pisse pisser péter vomir vomi chiotte chiottes putain pute bordel puanteur puer pourri pou morve cracher
crachat rot diarrhée tripe tripes cochon salaud salope ordure ordures poubelle fumier crotte fesse fesses ivrogne soûl saoul""".split())

CERT_RU = ["разумеется", "конечно", "естественно", "само собой", "как известно", "несомненно", "безусловно", "к счастью", "увы",
           "слава богу", "как водится", "понятное дело", "ясное дело"]
CERT_FR = ["évidemment", "bien sûr", "naturellement", "bien entendu", "comme chacun sait", "sans doute", "heureusement", "hélas",
           "Dieu merci", "cela va de soi", "il va sans dire"]

WORD_RU = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*")
WORD_FR = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœ]+")
SCARE = re.compile(r"(?<!^)[«\"“]([^»\"”«\n]{1,40})[»\"”]")

morph = None


@functools.lru_cache(maxsize=None)
def lem_ru(w):
    return morph.parse(w)[0].normal_form


def sent_lemmas(s, lang):
    if lang == "ru":
        return {lem_ru(w.lower()) for w in WORD_RU.findall(s)}
    return {w.lower() for w in WORD_FR.findall(s)}  # французские списки заданы словоформами


def clash(doc, rng):
    lang = doc["lang"]; hi, lo = (HIGH_RU, LOW_RU) if lang == "ru" else (HIGH_FR, LOW_FR)
    rows = []
    for p in doc["paras"]:
        if p["k"] not in ("narr", "dialog"):
            continue
        for s in p["sents"]:
            L = sent_lemmas(s, lang)
            n = len((WORD_RU if lang == "ru" else WORD_FR).findall(s))
            if n < 3:
                continue
            rows.append((n, bool(L & hi), bool(L & lo), s, sorted(L & hi), sorted(L & lo)))
    if not rows:
        return None
    n = np.array([r[0] for r in rows]); H = np.array([r[1] for r in rows]); Lw = np.array([r[2] for r in rows])
    obs = int((H & Lw).sum())
    # группы длины: децили
    edges = np.unique(np.percentile(n, np.linspace(0, 100, 11)))
    grp = np.digitize(n, edges[1:-1], right=True)
    perm = []
    for _ in range(N_PERM):
        Lp = Lw.copy()
        for g in np.unique(grp):
            ix = np.where(grp == g)[0]
            Lp[ix] = Lw[ix][rng.permutation(len(ix))]
        perm.append(int((H & Lp).sum()))
    exp = float(np.mean(perm))
    ratio = obs / exp if exp > 0 else None
    p = float(np.mean([x >= obs for x in perm]))
    verdict = None
    if exp >= MIN_EXP:
        verdict = "more" if ratio >= RATIO_UP else ("less" if ratio <= RATIO_DOWN else "none")
    ex = sorted([r for r in rows if r[1] and r[2]], key=lambda r: r[0])
    ex = [[r[3][:260], r[4], r[5]] for r in ex if 6 <= r[0] <= 40][:8]
    return {"sents": len(rows), "high": int(H.sum()), "low": int(Lw.sum()), "obs": obs, "exp": round(exp, 2),
            "ratio": round(ratio, 3) if ratio else None, "p": round(p, 3), "v": verdict, "ex": ex}


def scare_quotes(doc):
    n_words = 0; hits = []
    for p in doc["paras"]:
        if p["k"] != "narr":
            continue
        n_words += p["ntok"]
        for m in SCARE.finditer(p["t"]):
            q = m.group(1).strip()
            ws = q.split()
            if 1 <= len(ws) <= 3 and q[:1].islower():
                a, b = max(0, m.start() - 70), min(len(p["t"]), m.end() + 50)
                hits.append([q, p["t"][a:b]])
    return {"n": len(hits), "per10k": round(10000 * len(hits) / max(1, n_words), 2), "narr_words": n_words,
            "top": Counter(h[0].lower() for h in hits).most_common(12), "ex": hits[:10]}


def certainty(doc):
    lst = CERT_RU if doc["lang"] == "ru" else CERT_FR
    txt = " ".join(p["t"] for p in doc["paras"] if p["k"] == "narr").lower()
    n_words = sum(p["ntok"] for p in doc["paras"] if p["k"] == "narr")
    c = {w: len(re.findall(r"(?<![а-яёa-zà-ÿ])" + re.escape(w.lower()) + r"(?![а-яёa-zà-ÿ])", txt)) for w in lst}
    tot = sum(c.values())
    return {"n": tot, "per10k": round(10000 * tot / max(1, n_words), 2), "by": {k: v for k, v in c.items() if v}}


def main():
    global morph
    ap = argparse.ArgumentParser(); ap.add_argument("--qa", action="store_true"); a = ap.parse_args()
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()
    docs = pickle.load(open(HERE / "corpus.pkl", "rb"))
    rng = np.random.default_rng(20260930)
    out = []
    for d in docs:
        if d["role"] not in ("own", "self") or d["role"] == "self" and d["lang"] == "fr" and len(d["tokens"]) < 3000:
            continue
        if len(d["tokens"]) < 5000:
            continue  # короткие рассказы: ожидаемых столкновений слишком мало
        out.append({"work": d["work"], "year": d["year"], "sign": d["sign"], "lang": d["lang"], "role": d["role"], "tr": d["tr"],
                    "words": len(d["tokens"]), "clash": clash(d, rng), "scare": scare_quotes(d), "cert": certainty(d)})
    json.dump({"rule": {"n_perm": N_PERM, "up": RATIO_UP, "down": RATIO_DOWN, "min_exp": MIN_EXP,
                        "high_ru": sorted(HIGH_RU), "low_ru": sorted(LOW_RU), "high_fr": sorted(HIGH_FR), "low_fr": sorted(LOW_FR),
                        "cert_ru": CERT_RU, "cert_fr": CERT_FR}, "books": out},
              open(HERE / "markers.json", "w"), ensure_ascii=False, indent=0)
    print(f"{'книга':38} {'яз':2} {'подп':6} {'фраз':>6} {'выс':>5} {'низ':>5} {'набл':>4} {'ожид':>6} {'отн':>5} {'p':>5} вывод | кавычки/10к | уверенность/10к")
    for b in sorted(out, key=lambda b: (b["lang"], b["year"] or 0)):
        c = b["clash"]
        print(f"{b['work'][:38]:38} {b['lang']:2} {b['sign'][:6]:6} {c['sents']:>6} {c['high']:>5} {c['low']:>5} {c['obs']:>4} {c['exp']:>6} "
              f"{str(c['ratio']):>5} {c['p']:>5} {str(c['v']):5} | {b['scare']['per10k']:>6} | {b['cert']['per10k']:>6}")
    if a.qa:
        for b in out:
            print(f"\n## {b['work']} ({b['lang']})")
            for s, h, l in b["clash"]["ex"][:4]:
                print(f"   СТОЛКН {h}/{l}: {s}")
            print("   КАВЫЧКИ:", b["scare"]["top"][:8])
            for q, ctx in b["scare"]["ex"][:3]:
                print("     …", ctx.replace("\n", " "))
            print("   УВЕРЕННОСТЬ:", b["cert"]["by"])


if __name__ == "__main__":
    main()
