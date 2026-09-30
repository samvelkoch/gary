"""Пилот разметки иронии: выборка фрагментов → analysis/pilot_sample.json (вне репозитория: цитаты)

Правила записаны до разметки:
  * книги: «Обещание на рассвете» (Гари, 1960), «Пляска Чингиз-Хаима» (Гари, 1967), «Вся жизнь впереди» (Ажар, 1975) —
    русские переводы; фрагмент — абзац повествования или реплики длиной 25–160 слов;
  * из каждой книги 100 фрагментов: 60 случайных и 40 пойманных маркерами (столкновение высокого и низкого,
    иронические кавычки, притворная уверенность — см. markers.py); зерно фиксировано;
  * для слепой разметки заказчиком — 80 фрагментов: из каждой книги поровну случайных и маркерных пропорционально (≈16 + 10),
    перемешаны, слой (случайный / маркерный) не показывается;
  * модель размечает все 300 и фиксирует разметку в git до того, как увидит разметку заказчика;
  * вердикт пилота: каппа Коэна по «ирония есть / нет» (ответ «не уверен» считается «нет») на 80 фрагментах;
    ≥ 0,6 — разметка модели пригодна, пилот расширяется на корпус; < 0,6 — не публикуем, возвращаемся к постановке.
"""
import json, pickle, random, re
from pathlib import Path
import markers as M

HERE = Path(__file__).parent
BOOKS = ["La Promesse de l'aube", "La Danse de Gengis Cohn", "La Vie devant soi"]
TITLE = {"La Promesse de l'aube": "Обещание на рассвете", "La Danse de Gengis Cohn": "Пляска Чингиз-Хаима", "La Vie devant soi": "Вся жизнь впереди"}
N_RAND, N_MARK, N_USER = 60, 40, 80
SEED = 20260930


def marker_hits(p):
    """Какие маркеры срабатывают в абзаце."""
    hits = []
    for s in p["sents"]:
        L = M.sent_lemmas(s, "ru")
        if L & M.HIGH_RU and L & M.LOW_RU:
            hits.append("столкновение"); break
    if p["k"] == "narr":
        for m in M.SCARE.finditer(p["t"]):
            q = m.group(1).strip()
            if 1 <= len(q.split()) <= 3 and q[:1].islower():
                hits.append("кавычки"); break
    low = p["t"].lower()
    if any(re.search(r"(?<![а-яё])" + re.escape(w) + r"(?![а-яё])", low) for w in M.CERT_RU):
        hits.append("уверенность")
    return hits


def main():
    import pymorphy3
    M.morph = pymorphy3.MorphAnalyzer()
    docs = pickle.load(open(HERE / "corpus.pkl", "rb"))
    rng = random.Random(SEED)
    sample = []
    for w in BOOKS:
        d = next(x for x in docs if x["work"] == w and x["lang"] == "ru" and x["role"] == "own")
        cand = [(i, p) for i, p in enumerate(d["paras"]) if p["k"] in ("narr", "dialog") and 25 <= p["ntok"] <= 160]
        marked = [(i, p, marker_hits(p)) for i, p in cand]
        pool_m = [x for x in marked if x[2]]
        # если маркерных абзацев меньше 40, берутся все, а недостающее добирается случайными (100 на книгу)
        n_mark = min(N_MARK, len(pool_m) // 2)
        rnd = rng.sample(cand, N_RAND + N_MARK - n_mark)
        taken = {i for i, _ in rnd}
        mk = rng.sample([x for x in pool_m if x[0] not in taken], min(n_mark, len([x for x in pool_m if x[0] not in taken])))
        for i, p in rnd:
            sample.append({"book": TITLE[w], "para": i, "stratum": "random", "markers": marker_hits(p), "text": p["t"]})
        for i, p, h in mk:
            sample.append({"book": TITLE[w], "para": i, "stratum": "marker", "markers": h, "text": p["t"]})
        print(f"{TITLE[w]}: абзацев-кандидатов {len(cand)}, с маркерами {len(pool_m)} ({100 * len(pool_m) / len(cand):.0f}%)")
    for k, x in enumerate(sample):
        x["id"] = f"f{k:03d}"
    # подвыборка для заказчика: из каждой книги 16 случайных и 10 маркерных (+2 случайных добор до 80), перемешать
    user = []
    for t in TITLE.values():
        r = [x for x in sample if x["book"] == t and x["stratum"] == "random"]; m = [x for x in sample if x["book"] == t and x["stratum"] == "marker"]
        user += rng.sample(r, 16) + rng.sample(m, min(10, len(m)))
    rest = [x for x in sample if x not in user and x["stratum"] == "random"]
    user += rng.sample(rest, N_USER - len(user))
    rng.shuffle(user)
    ids = [x["id"] for x in user]
    json.dump({"rule": __doc__, "sample": sample, "user_ids": ids}, open(HERE / "pilot_sample.json", "w"), ensure_ascii=False, indent=1)
    print("фрагментов:", len(sample), "для заказчика:", len(ids), "из них маркерных:", sum(1 for x in user if x["stratum"] == "marker"))


if __name__ == "__main__":
    main()
