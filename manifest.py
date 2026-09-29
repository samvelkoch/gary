"""Шаг 2. Манифест корпуса: что каждый файл такое на самом деле и что идёт в анализ.

Классификация — по содержимому (имена файлов в project/ перепутаны), явной таблицей ниже.
Источники метаданных:
  годы и французские названия — fr.wikipedia.org/wiki/Romain_Gary (библиография) и
  fr.wikipedia.org/wiki/Gloire_à_nos_illustres_pionniers (состав сборника 1962);
  переводчики — выходные данные внутри EPUB (если есть), иначе «нет данных».
Отобранные тексты копируются в texts/ (вне репозитория) с понятными именами.

Роли:
  own        — художественный текст Гари (под любой подписью)
  self       — Гари о себе: интервью, автобиографическое эссе, статьи
  oral       — устная речь в автосубтитрах (без пунктуации): только меры по словам
  twin       — второй перевод той же книги (линия шума перевода, в основной анализ не идёт)
  dup        — дубль (тот же текст)
  about      — о Гари (биография, исследования) — внешний источник, не анализируется
  aux        — служебное (промпты, профили, вики, текст пользователя) — не анализируется
"""
import csv, json, re, shutil
from pathlib import Path

HERE = Path(__file__).parent
EX = HERE / "corpus" / "extracted.jsonl"
DST = HERE / "texts"

# ключ — уникальная часть пути; значения: роль, произведение (фр. название), год первой публикации,
# язык текста, подпись, жанр, переводчик
T = {}


def w(key, role, work="", year=None, sign="Gary", genre="роман", tr="", note=""):
    T[key] = dict(role=role, work=work, year=year, sign=sign, genre=genre, tr=tr, note=note)


# ── Русские переводы: романы ──
w("Belaya_sobaka", "own", "Chien blanc", 1970, note="параллельно написан по-английски (White Dog, 1970)")
w("Bolshaya_baraholka", "own", "Le Grand Vestiaire", 1949)
w("Charodei", "own", "Les Enchanteurs", 1973)
w("Dalshe_vash_bilet_nedeystvitelen.346906", "own", "Au-delà de cette limite votre ticket n'est plus valable", 1975)
w("Dalshe_vash_bilet_nedeystvitelen_litres", "twin", "Au-delà de cette limite votre ticket n'est plus valable", 1975, tr="Н. Мавлевич")
w("Evropa.", "own", "Europa", 1972)
w("Evropeyskoe_vospitanie.346921", "own", "Éducation européenne", 1945)
w("Evropeyskoe_vospitanie.796173", "dup", "Éducation européenne", 1945, tr="В. Нугатов",
  note="75% общих 5-словных шинглов с другим файлом — редакция того же перевода, не независимый")
w("Golovyi_Stefani", "own", "Les Têtes de Stéphanie", 1974, sign="Shatan Bogat")
w("Grustnyie_klounyi", "own", "Les Clowns lyriques", 1979, note="переработка «Les Couleurs du jour» (1952)")
w("Korni_Neba", "own", "Les Racines du ciel", 1956)
w("Ledi_L..508187", "own", "Lady L.", 1963, note="написан по-английски (1958), французская версия 1963")
w("Ledi_L..810749", "twin", "Lady L.", 1963, tr="Н. Мавлевич")
w("Noch_budet_spokoynoy", "self", "La nuit sera calme", 1974, genre="интервью-книга")
w("Obeschanie_na_rassvete", "own", "La Promesse de l'aube", 1960, genre="автобиографический роман", tr="Е. Погожева")
w("Plyaska_Chingiz", "own", "La Danse de Gengis Cohn", 1967)
w("Povinnaya_golova", "own", "La Tête coupable", 1968, tr="И. Кузнецова")
w("Pozhirateli_zvezd.74989", "own", "Les Mangeurs d'étoiles", 1966, note="английская версия The Talent Scout, 1961")
w("Pozhirateli_zvezd_litres", "twin", "Les Mangeurs d'étoiles", 1966)
w("Proschay_Gari_Kuper.146735", "own", "Adieu Gary Cooper", 1969, tr="Е. Чебучева", note="английская версия The Ski Bum, 1965")
w("Proschay_Gari_Kuper_litres", "dup", "Adieu Gary Cooper", 1969, note="99% общих шинглов — тот же перевод")
w("Spasite_nashi_dushi.358176 (1)", "dup", "Charge d'âme", 1977)
w("Spasite_nashi_dushi.358176.", "own", "Charge d'âme", 1977, note="английская версия The Gasp, 1973")
w("Svet_zhenschinyi.202198", "own", "Clair de femme", 1977)
w("Svet_zhenschinyi_litres", "dup", "Clair de femme", 1977, tr="Н. Калягина", note="65% общих шинглов — редакция того же перевода")
w("Tsveta_dnya", "own", "Les Couleurs du jour", 1952)
w("Tyulpan.402281 (1)", "dup", "Tulipe", 1946)
w("Tyulpan.402281.", "own", "Tulipe", 1946)
w("Vino_mertvetsov", "own", "Le Vin des morts", 1937, note="написан 1937, опубликован 2014")
w("Vozdushnyie_zmei.781944", "own", "Les Cerfs-volants", 1980, tr="Е. Штофф")
w("Vozdushnyie_zmei.89092", "dup", "Les Cerfs-volants", 1980, note="73% общих шинглов — редакция того же перевода")
w("Zhizn_i_smert_Emilya_Azhara", "self", "Vie et mort d'Émile Ajar", 1981, genre="эссе", tr="И. Кузнецова",
  note="написано 21.03.1979, опубликовано посмертно")

# ── Русские переводы: рассказы сборника «Gloire à nos illustres pionniers» (1962) ──
for key, fr, tr in [
    ("Ptitsyi_priletayut", "Les oiseaux vont mourir au Pérou", "Л. Бондаренко, А. Фарафонов"),
    ("Lyutnya", "Le Luth", "Л. Бондаренко, А. Фарафонов"),
    ("Gumanist", "Un humaniste", "С. Козицкий"),
    ("Dekadans", "Décadence", "Л. Бондаренко, А. Фарафонов"),
    ("Poddelka", "Le Faux", "Л. Бондаренко, А. Фарафонов"),
    ("Radosti_prirodyi.338355.", "Les Joies de la nature", "Л. Бондаренко, А. Фарафонов"),
    ("Grazhdanin_golub", "Citoyen pigeon", "Л. Бондаренко, А. Фарафонов"),
    ("Stranitsa_istorii", "Une page d'histoire", "О. Кустова"),
    ("Na_Kilimandzharo", "Tout va bien sur le Kilimandjaro", "Ю. Винер"),
    ("Ya_govoryu_o_geroizme", "Je parle de l'héroïsme", "Ю. Винер"),
    ("Zhiteli_Zemli", "Les Habitants de la Terre", "М. Аннинская"),
    ("Kak_ya_mechtal", "J'ai soif d'innocence", "А. Стернина"),
    ("Staraya-prestaraya", "La Plus Vieille Histoire du monde", ""),
    ("Slava_nashim", "Gloire à nos illustres pionniers", "А. Попова"),
]:
    w(key, "own", fr, 1962, genre="рассказ", tr=tr)
w("Staraya_istoriya.194599", "twin", "La Plus Vieille Histoire du monde", 1962, genre="рассказ")
w("Radosti_prirodyi.338355 (1)", "dup", "Les Joies de la nature", 1962, genre="рассказ")
w("Ya_em_botinok", "own", "Я ем ботинок (оригинал не установлен)", None, genre="рассказ", tr="В. Козовой", note="оригинал не установлен")
w("Pismo_k_moey_sosedke", "own", "Письмо к моей соседке по столу (оригинал не установлен)", None, genre="рассказ", tr="С. Козицкий", note="оригинал не установлен")

# ── Французские оригиналы ──
w("La_promesse_de_laube", "own", "La Promesse de l'aube", 1960, genre="автобиографический роман")
w("La_vie_devant_soi", "own", "La Vie devant soi", 1975, sign="Émile Ajar")
w("Les_Racines_du_Ciel", "own", "Les Racines du ciel", 1956)
w("Fosco Sinibaldi - text.docx", "own", "L'Homme à la colombe", 1958, sign="Fosco Sinibaldi",
  note="окончательная редакция 1984; предисловие издателя вырезается")
w("Fosco Sinibaldi - dual", "dup", "L'Homme à la colombe", 1958, sign="Fosco Sinibaldi", note="фр. + рус. параллельно")
w("Fosco Sinibaldi - originale", "dup", "L'Homme à la colombe", 1958, sign="Fosco Sinibaldi", note="фр. + рус. параллельно")
w("Fosco Sinibaldi.docx", "dup", "L'Homme à la colombe", 1958, sign="Fosco Sinibaldi", note="фр. + рус., другая вёрстка")

# ── Гари о себе, французский ──
w("9782070140541", "self", "Le Sens de ma vie", 1980, genre="интервью (отредактированное)",
  note="запись интервью Радио-Канада 1980, издано 2014")
w("propos et confidences 1", "oral", "Propos et confidences, 1/4", 1980, genre="интервью (автосубтитры)",
  note="то же интервью, что Le Sens de ma vie (примечание издателя: Жан Фоше, Радио-Канада, 1980)")
w("propos et confidences 2", "oral", "Propos et confidences, 2/4", 1980, genre="интервью (автосубтитры)",
  note="то же интервью, что Le Sens de ma vie (примечание издателя: Жан Фоше, Радио-Канада, 1980)")
w("propos et confidences 3", "oral", "Propos et confidences, 3/4", 1980, genre="интервью (автосубтитры)",
  note="то же интервью, что Le Sens de ma vie (примечание издателя: Жан Фоше, Радио-Канада, 1980)")
w("propos et confidences 4", "oral", "Propos et confidences, 4/4", 1980, genre="интервью (автосубтитры)",
  note="то же интервью, что Le Sens de ma vie (примечание издателя: Жан Фоше, Радио-Канада, 1980)")
w("Romain Gary/Interview.docx", "oral", "Radioscopie, Jacques Chancel", 1975, genre="интервью (автосубтитры)",
  note="год — по второй записи той же передачи в ~/Downloads, «Romain Gary (1975)»")
w("Femmes.md", "self", "Ces femmes que j'aime", None, genre="статья")
w("Gengis_Cohn_cest_moi", "self", "Portrait-interview par Paul Guth", None, genre="интервью журналиста",
  note="текст журналиста с репликами Гари")
w("La_Danse_de_Gengis_Cohn.md", "self", "Entretien avec Claudine Jardin", 1967, genre="интервью журналиста")
w("Interview_lapaz", "self", "Questionnaire de Marcel Proust", None, genre="анкета")

# ── Дубли в project/ (имена файлов не совпадают с содержимым) ──
for key, what in [("Vie_et_mort_dEmileAjar.md", "= «Ночь будет спокойной» (EPUB)"),
                  ("Identeties.md", "= «Пляска Чингиз-Хаима» (EPUB)"),
                  ("La_tête_coupable.md", "= «Повинная голова» (EPUB)"),
                  ("Biography_Chameleon.md", "= «Жизнь и смерть Эмиля Ажара» (EPUB)"),
                  ("Interview_TY.md", "= Le Sens de ma vie (EPUB)"),
                  ("Interview_YT.md", "= Interview.docx (Шансель)"),
                  ("Questionnaire_de_Marcel_Proust.md", "= четыре части «propos et confidences»")]:
    w(key, "dup", note=what)

# ── Найдено в ~/Downloads ──
w("Azhar.Golubchik", "dup", "Gros-Câlin", 1974, sign="Émile Ajar", note="rtf из ~/Downloads, 100% общих шинглов с EPUB")
# добавлены заказчиком в Texts/ 2026-09-29; переводчик не указан ни в тексте, ни в метаданных
# переводчики — по внешним каталогам (в файлах не указаны): FantLab edition60018 (Симпозиум, 2000),
# каталоги изданий «Псевдо» (Симпозиум, 2002) и «Страхов царя Соломона» (перевод 1997)
w("Gari_Golubchik.409694", "own", "Gros-Câlin", 1974, sign="Émile Ajar", tr="Н. Мавлевич", note="переводчик по FantLab")
w("Gari_Psevdo.409695", "own", "Pseudo", 1976, sign="Émile Ajar", tr="А. Беляк", note="переводчик по каталогу издательства")
w("Gari_Strahi-carya-Solomona.409696", "own", "L'Angoisse du roi Salomon", 1979, sign="Émile Ajar", tr="Л. Лунгина",
  note="переводчик по FantLab / каталогам")
w("Vsya-zhizn-vperedi", "own", "La Vie devant soi", 1975, sign="Émile Ajar", tr="В. Орлов")
w("Romain Gary (1975) [DownSub", "oral", "Radioscopie, Jacques Chancel (2)", 1975, genre="интервью (автосубтитры)",
  note="29% общих шинглов с Interview.docx — та же передача")
# fb2 — те же переводы, что EPUB (100% общих шинглов): в анализ не идут, дают переводчика
for key, what in [("Belaya-sobaka", "Chien blanc"), ("Noch-budet-spokoynoy", "La nuit sera calme"),
                  ("Evropeyskoe-vospitanie.HzKmJA", "Éducation européenne"), ("Povinnaya-golova.RFPxEA", "La Tête coupable"),
                  ("Korni-Neba.Un93gw", "Les Racines du ciel"), ("Obeshchanie-na-rassvete", "La Promesse de l'aube"),
                  ("Plyaska-Chingiz-Haima.KqmC3g", "La Danse de Gengis Cohn"), ("Svet-zhenshchiny.FDJfLg", "Clair de femme"),
                  ("Vino-mertvecov", "Le Vin des morts"), ("Vozdushnye-zmei.M3_j_w", "Les Cerfs-volants")]:
    w(key, "dup", what, note="fb2, тот же перевод, что EPUB; источник имени переводчика")

# переводчики из метаданных fb2 (сверка текста: 100% общих 5-словных шинглов)
for key, tr in [("Belaya_sobaka", "Н. Калягина"), ("Noch_budet_spokoynoy", "Л. Бондаренко, А. Фарафонов"),
                ("Evropeyskoe_vospitanie.346921", "В. Нугатов"), ("Povinnaya_golova", "И. Кузнецова"),
                ("Korni_Neba", "Е. Голышева"), ("Obeschanie_na_rassvete", "Е. Погожева"),
                ("Plyaska_Chingiz", "Л. Цывьян"), ("Svet_zhenschinyi.202198", "Н. Калягина"),
                ("Vino_mertvetsov", "Н. Мавлевич"), ("Vozdushnyie_zmei.89092", "Е. Штофф")]:
    T[key]["tr"] = tr

# ── О Гари и служебное ──
w("_Romain_Gary_Psychological_Profile_ver_1", "about", "М. Анисимов, «Ромен Гари, хамелеон» (рус.)", note="внешний источник для сверки фактов")
w("Le_judaïsme.md", "about", "Identities — сборник статей о Гари (распознанный скан)")
w("wiki.md", "about", "Сводка из Википедии (фр.)", note="внешний источник")
w("La_nuit_sera_calm.md", "dup", note="= wiki.md")
w("_Romain_Gary_Psychological_Profile_ver_2", "aux", "психологический профиль")
w("_system_prompt_ver_1", "aux", "психологический профиль (промпт)")
w("_system_prompt_ver_2", "aux", "системный промпт персоны")
w("Le_sens_de_ma_vie.md", "aux", note="= системный промпт персоны")
w("glava_1_obyavlenie", "aux", "«Клуб последних жён», гл. 1 — не Гари")


def match(path):
    hits = [k for k in T if k in path]
    if len(hits) != 1:
        return None, hits
    return T[hits[0]], hits


def slug(s):
    s = re.sub(r"[^\w]+", "_", s, flags=re.U).strip("_")
    return s[:60]


def main():
    rows = [json.loads(l) for l in open(EX, encoding="utf-8")]
    out, problems = [], []
    for r in rows:
        meta, hits = match(r["path"])
        if meta is None:
            if "words" in r:  # у нетекстовых (pdf, mp3, zip) метаданных может не быть
                problems.append((r["path"], hits))
            meta = dict(role="nontext" if "words" not in r else "?", work="", year=None, sign="", genre="", tr="", note="")
        out.append({**r, **meta, "src_lang": "fr" if r.get("lang") == "fr" else ("ru" if r.get("lang") == "ru" else r.get("lang", ""))})
    if problems:
        for p in problems:
            print("НЕТ/НЕСКОЛЬКО СОВПАДЕНИЙ:", p)
        raise SystemExit(1)

    # texts/: только то, что идёт в анализ, и пары переводов для линии шума
    if DST.exists():
        shutil.rmtree(DST)
    for sub in ("ru", "fr", "twins", "oral"):
        (DST / sub).mkdir(parents=True)
    for m in out:
        if m["role"] not in ("own", "self", "twin", "oral"):
            m["file"] = ""
            continue
        sub = {"twin": "twins", "oral": "oral"}.get(m["role"], m["src_lang"])
        fn = f"{m['year'] or '0000'}_{slug(m['sign'])}_{slug(m['work'])}_{m['id'][:4]}.txt"
        m["file"] = f"{sub}/{fn}"
        shutil.copy(HERE / "corpus" / "texts" / f"{m['id']}.txt", DST / sub / fn)

    cols = ["file", "role", "src_lang", "year", "sign", "genre", "work", "tr", "words", "note", "path", "id"]
    with open(DST / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wr.writeheader()
        for m in sorted(out, key=lambda m: (m["role"], m["src_lang"], m["year"] or 0)):
            wr.writerow(m)
    with open(HERE / "corpus" / "manifest.jsonl", "w", encoding="utf-8") as f:
        for m in out:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    # цифры полноты
    from collections import Counter, defaultdict
    c = Counter((m["role"], m["src_lang"]) for m in out)
    wsum = defaultdict(int)
    for m in out:
        wsum[(m["role"], m["src_lang"])] += m.get("words", 0)
    print(f"{'роль':8} {'язык':6} {'файлов':>6} {'слов':>9}")
    for k in sorted(c):
        print(f"{k[0]:8} {k[1]:6} {c[k]:>6} {wsum[k]:>9}")
    sig = Counter((m["sign"], m["src_lang"]) for m in out if m["role"] == "own")
    print("подписи (own):", dict(sig))


if __name__ == "__main__":
    main()
