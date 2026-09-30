"""Шаг 3. Очистка, разбиение и разметка корпуса → analysis/corpus.pkl

Вход: texts/manifest.csv и тексты в texts/ (роли own, self, twin, oral).
Для каждого текста: абзацы с типом (заголовок / повествование / диалог), говорящий
(в интервью), предложения, слова; русские леммы — pymorphy3, французские — spaCy
(отдельное окружение .venv-fr, скрипт lemmatize_fr.py).

Режимы: --qa — начало и конец каждого очищенного текста, счётчики.
"""
import argparse, csv, json, pickle, re, subprocess, functools
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
TX = ROOT / "texts"

AUTHOR_LINE = re.compile(r"^(Ромен|Роман)\s+Гари\.?$|^Эмиль Ажар$|^Шатан Богат$|^ГАРИ РОМАН$|^Romain Gary$|^РОМЕН ГАРИ$", re.I)
JUNK = re.compile(r"^(Annotation|notes|Примечания|FIN|КОНЕЦ)$|Перевод (с )?(французского|английского)|^©|^\[Musique\]$", re.I)

# явные разрезы: (фрагмент имени файла) → (начать с абзаца, который начинается так; закончить перед абзацем, который начинается так)
CUTS = {
    "Les_Racines_du_ciel_fe76": ("PREMIÈRE PARTIE", None),
    "L_Homme_à_la_colombe": ("I", None),                      # после примечания издателя
    "Le_Sens_de_ma_vie": ("LA PROMESSE DE L’AUBE", "Du même auteur"),
    "Ces_femmes_que_j_aime": (None, None),                     # делится на статью и интервью ниже
}
# чужое предисловие внутри книги: срезать до подписи включительно
AFTER = {"Le_Vin_des_morts": "Филипп Брено"}
# тексты журналистов с цитатами Гари — не голос Гари, в меры не идут
JOURNALIST = ("Portrait_interview_par_Paul_Guth", "Entretien_avec_Claudine_Jardin")

TERM = re.compile(r"[.!?…:;»\"”)\]]\s*$")
DIALOG = re.compile(r"^\s*[—–-]\s|^\s*«")
SENT = re.compile(r"(?<=[.!?…])[»\"”)]*\s+(?=[—–«\"„(]?\s*[A-ZА-ЯЁÀ-Ý0-9])")
TOK_RU = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*|[A-Za-z]+")
L = "A-Za-zÀ-ÖØ-öø-ÿŒœ"
TOK_FR = re.compile(rf"aujourd['’]hui|(?:jusqu|lorsqu|puisqu|quoiqu|qu|[cdjlmnst])['’](?=[{L}])|[{L}]+(?:-[{L}]+)*", re.I)


def paras_of(t):
    ps = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    ps = [p for p in ps if not re.match(r"^\[\d{1,3}\]\s", p)]      # сноски вида «[54] текст»
    return [re.sub(r"\[\d{1,3}\]|\{\d{1,3}\}", "", p).strip() for p in ps]  # метки сносок в тексте


def clean_book(ps, fname):
    """Срезать аннотацию, выходные данные, оглавление и хвост со сносками."""
    cut = next((v for k, v in CUTS.items() if k in fname), None)
    # хвост сносок: последний «notes»/«Примечания», после которого ≥30% абзацев — голые номера
    for i in range(len(ps) - 1, -1, -1):
        if ps[i] in ("notes", "Примечания", "Комментарии"):
            rest = ps[i + 1:]
            if not rest or sum(bool(re.fullmatch(r"\d{1,3}", r)) for r in rest) >= 0.3 * len(rest):
                ps = ps[:i]
            break
    ps = [p for p in ps if not JUNK.search(p)]
    if cut:
        start, end = cut
        if start:
            i = next(i for i, p in enumerate(ps) if p.startswith(start) and (start != "I" or i > 3))
            ps = ps[i:]
        if end:
            j = next((j for j, p in enumerate(ps) if p.startswith(end)), len(ps))
            ps = ps[:j]
        return ps
    # общее правило: после строки с именем автора — первый абзац длиннее 15 слов; перед ним
    # оставляется ближайший заголовок (для атласа), оглавление выбрасывается
    a = next((i for i, p in enumerate(ps[:40]) if AUTHOR_LINE.match(p)), -1)
    first = next(i for i in range(a + 1, len(ps)) if len(ps[i].split()) >= 15)
    ps = ps[first:]
    after = next((v for k, v in AFTER.items() if k in fname), None)
    if after:  # чужое предисловие: всё до подписи его автора включительно
        ps = ps[next(i for i, p in enumerate(ps) if p == after) + 1:]
    return ps


DIALOG_MAX = 120  # абзац-реплика длиннее — это рассказ героя (рассказ в рассказе), он считается повествованием


def kind(p):
    n = len(p.split())
    if n <= 8 and not TERM.search(p):
        return "head"
    return "dialog" if DIALOG.match(p) and n <= DIALOG_MAX else "narr"


def split_speakers_night(ps):
    """«Ночь будет спокойной»: реплики Бонди и Гари. Абзац без метки — продолжение прежнего говорящего."""
    out, cur = [], None
    for p in ps:
        m = re.match(r"^(Франсуа Бонди\.|Ф\. ?Б\.|Ромен Гари\.|Р\. ?Г\.)\s*", p)
        if m:
            cur = "bondy" if m.group(1).startswith(("Ф", "Франсуа")) else "gary"
            p = p[m.end():]
        if p:
            out.append((p, cur or "gary"))
    return out


def split_femmes(ps):
    """Femmes.md: статья «Ces femmes que j'aime» + интервью Пьеру Сиприо (реплики R.G. / P.S.)."""
    art, itv, mode, cur = [], [], "art", None
    for p in ps:
        if p.startswith("Entretien avec Pierre Sipriot"):
            mode = "itv"; continue
        if re.match(r"^(Team paru|Texte paru|Interview publi)", p):
            continue
        if mode == "art":
            if p not in ("Ces femmes que j'aime", "Romain Gary") and not p.startswith("Être deux"):
                art.append((p, "gary"))
        else:
            m = re.match(r"^(Pierre Sipriot|P\.S\.|Romain Gary|R\.G\.)\s*[-–]?\s*", p)
            if m:
                cur = "gary" if m.group(1) in ("Romain Gary", "R.G.") else "sipriot"
                p = p[m.end():]
            if p:
                itv.append((p, cur or "sipriot"))
    return art, itv


def proust_answers(ps):
    out = []
    for p in ps:
        if re.match(r"^\*?(Texte paru|¹)", p):
            continue
        a = re.sub(r"\*\*[^*]+\*\*", "", p).strip()
        if a:
            out.append((a, "gary"))
    return out


morph = None


@functools.lru_cache(maxsize=None)
def ru_parse(w):
    p = morph.parse(w)[0]
    return p.normal_form, str(p.tag.POS), ("Name" in p.tag or "Surn" in p.tag or "Patr" in p.tag), ("Geox" in p.tag), morph.word_is_known(w)


def sentences(p):
    return [s.strip() for s in SENT.split(p) if s.strip()]


def build_doc(m, units, lang):
    """units: список (абзац, говорящий)."""
    paras = []
    for p, spk in units:
        k = kind(p)
        toks = (TOK_RU if lang == "ru" else TOK_FR).findall(p)
        paras.append({"t": p, "k": k, "spk": spk, "sents": sentences(p) if k != "head" else [p], "ntok": len(toks)})
    return {**m, "lang": lang, "paras": paras}


def main():
    global morph
    ap = argparse.ArgumentParser(); ap.add_argument("--qa", action="store_true"); a = ap.parse_args()
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()
    man = [r for r in csv.DictReader(open(TX / "manifest.csv", encoding="utf-8")) if r["file"]]
    docs = []
    for m in man:
        t = (TX / m["file"]).read_text(encoding="utf-8")
        f = m["file"]; lang = m["src_lang"]
        m = {k: m[k] for k in ("file", "role", "year", "sign", "genre", "work", "tr", "id")}
        m["year"] = int(m["year"]) if m["year"] else None
        if m["role"] == "oral":
            words = re.sub(r"\[[^\]]*\]", " ", t)
            k = words.lower().find("radioscopie")  # реклама перед началом передачи
            if 0 < k < 3000:
                words = words[k:]
            units = [(" ".join(words.split()), "gary")]
            d = build_doc(m, units, lang); d["paras"][0]["k"] = "oral"
            docs.append(d); continue
        if any(j in f for j in JOURNALIST):
            m["role"] = "journalist"
            docs.append(build_doc(m, [(p, "mixed") for p in paras_of(t)], lang)); continue
        ps = paras_of(t)
        if "Ces_femmes_que_j_aime" in f:
            art, itv = split_femmes([p for p in ps if not JUNK.search(p)])
            docs.append(build_doc({**m, "work": "Ces femmes que j'aime", "genre": "статья", "year": 1974}, art, lang))
            docs.append(build_doc({**m, "id": m["id"] + "-s", "work": "Entretien avec Pierre Sipriot (Clair de femme)",
                                   "genre": "интервью", "year": 1977}, itv, lang))
            continue
        if "Questionnaire_de_Marcel_Proust" in f:
            docs.append(build_doc({**m, "year": 1967}, proust_answers(ps), lang)); continue
        ps = clean_book(ps, f)
        units = split_speakers_night(ps) if "La_nuit_sera_calme" in f else [(p, "gary") for p in ps]
        docs.append(build_doc(m, units, lang))

    # слова и леммы
    fr_jobs = []
    for d in docs:
        d["tokens"], d["lemmas"], d["pos"], d["para_of_tok"] = [], [], [], []
        d["is_name"], d["is_geo"], d["known"] = [], [], []
        for pi, p in enumerate(d["paras"]):
            toks = (TOK_RU if d["lang"] == "ru" else TOK_FR).findall(p["t"])
            d["tokens"] += toks; d["para_of_tok"] += [pi] * len(toks)
        if d["lang"] == "ru":
            for w in d["tokens"]:
                l, pos, nm, geo, kn = ru_parse(w.lower())
                d["lemmas"].append(l); d["pos"].append(pos); d["is_name"].append(nm); d["is_geo"].append(geo); d["known"].append(kn)
        else:
            fr_jobs.append(d)
    # французский: леммы spaCy по тем же токенам (отдельное окружение)
    job = HERE / "_fr_tokens.json"
    json.dump([d["tokens"] for d in fr_jobs], open(job, "w"), ensure_ascii=False)
    subprocess.run([str(HERE / ".venv-fr/bin/python"), str(HERE / "lemmatize_fr.py"), str(job)], check=True)
    res = json.load(open(job.with_suffix(".out.json")))
    for d, (lem, pos) in zip(fr_jobs, res):
        d["lemmas"], d["pos"] = lem, pos
        d["is_name"] = [p == "PROPN" for p in pos]; d["is_geo"] = [False] * len(pos); d["known"] = [True] * len(pos)
    job.unlink(); job.with_suffix(".out.json").unlink()

    pickle.dump(docs, open(HERE / "corpus.pkl", "wb"))
    c = Counter((d["role"], d["lang"]) for d in docs)
    wc = Counter()
    for d in docs:
        wc[(d["role"], d["lang"])] += len(d["tokens"])
    for k in sorted(c):
        print(f"{k[0]:10} {k[1]} текстов {c[k]:>3}  слов {wc[k]:>9}")
    print("уникальных русских форм:", ru_parse.cache_info().currsize)
    if a.qa:
        for d in docs:
            ps = [p for p in d["paras"] if p["k"] != "head"]
            k = Counter(p["k"] for p in d["paras"])
            spk = Counter(p["spk"] for p in d["paras"])
            print(f"\n## {d['file']} [{d['role']}] {len(d['tokens'])} сл. {dict(k)} {dict(spk) if len(spk) > 1 else ''}")
            if ps:
                print("   НАЧАЛО:", ps[0]["t"][:160])
                print("   КОНЕЦ: ", ps[-1]["t"][-160:])


if __name__ == "__main__":
    main()
