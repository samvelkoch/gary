"""Второй заход: сарказм. Выборка → analysis/pilot2_sample.json (вне репозитория: цитаты)

Правила записаны до разметки:
  * определение сарказма — analysis/pilot2_definition.md (согласовано с заказчиком до разметки);
  * книги — восемь, ни одна не входила в первый пилот: «Большая барахолка» (1949), «Корни неба» (1956),
    «Пожиратели звёзд» (1966), «Повинная голова» (1968), «Белая собака» (1970), «Головы Стефани» (Шатан Богат, 1974),
    «Голубчик» (Ажар, 1974), «Страхи царя Соломона» (Ажар, 1979); русские переводы;
  * из каждой книги 10 случайных абзацев повествования или реплик длиной 25–160 слов (без маркеров, без отбора); зерно фиксировано;
  * все 80 фрагментов размечают оба: модель (по определению, фиксирует разметку в git до просмотра разметки заказчика)
    и заказчик вслепую;
  * ответ: «сарказм есть / нет / не уверен» + мишень; «не уверен» = «нет»;
  * вердикт: каппа Коэна ≥ 0,6 — разметка модели пригодна, переходим к мишеням сарказма по всему корпусу;
    < 0,6 — тема закрывается, в методике пишется, что автоматически это не измеряется.
"""
import json, pickle, random
from pathlib import Path

HERE = Path(__file__).parent
BOOKS = [("Le Grand Vestiaire", "Большая барахолка"), ("Les Racines du ciel", "Корни неба"), ("Les Mangeurs d'étoiles", "Пожиратели звёзд"),
         ("La Tête coupable", "Повинная голова"), ("Chien blanc", "Белая собака"), ("Les Têtes de Stéphanie", "Головы Стефани"),
         ("Gros-Câlin", "Голубчик"), ("L'Angoisse du roi Salomon", "Страхи царя Соломона")]
N_PER, SEED = 10, 20261001


def main():
    docs = pickle.load(open(HERE / "corpus.pkl", "rb"))
    first = {x["book"] for x in json.load(open(HERE / "pilot_sample.json"))["sample"]}
    rng = random.Random(SEED)
    sample = []
    for w, t in BOOKS:
        assert t not in first
        d = next(x for x in docs if x["work"] == w and x["lang"] == "ru" and x["role"] == "own")
        cand = [(i, p) for i, p in enumerate(d["paras"]) if p["k"] in ("narr", "dialog") and 25 <= p["ntok"] <= 160]
        for i, p in rng.sample(cand, N_PER):
            sample.append({"book": t, "para": i, "text": p["t"]})
    rng.shuffle(sample)
    for k, x in enumerate(sample):
        x["id"] = f"s{k:03d}"
    json.dump({"rule": __doc__, "sample": sample}, open(HERE / "pilot2_sample.json", "w"), ensure_ascii=False, indent=1)
    print("фрагментов:", len(sample))


if __name__ == "__main__":
    main()
