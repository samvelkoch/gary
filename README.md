# Ромен Гари на просвет

Количественное исследование прозы Ромена Гари — под всеми его подписями (Гари, Эмиль Ажар,
Шатан Богат, Фоско Синибальди) — с интерактивным отчётом. Сделано по канону
[`refs/CANON.md`](refs/CANON.md) (копия канона из `samvelkoch/brodsky`, дополненная по итогам этого проекта).

> Готовый отчёт: `docs/prosvet.html` (откройте в браузере). В нём есть цитаты в объёме,
> нужном для иллюстраций.
>
> Тексты Гари и переводы защищены авторским правом. Кроме отчёта, в репозитории только код:
> корпус, тексты и посчитанные данные с цитатами создаются локально и перечислены в `.gitignore`.

## Главные вопросы

1. Пишет ли Гари под маской Ажара другим голосом? — по французским оригиналам, стилометрия
   по частым словам с заранее заданным правилом вердикта.
2. Сколько в русском Гари от Гари, а сколько от переводчика? — по парам переводов одной книги
   и по книгам одного переводчика.
3. Как меняются фраза, диалог, рассказчик, темы и словарь с 1937 по 1980 год.
4. Мир Гари: люди, которых он упоминает из книги в книгу, места, звери, напитки, транспорт, оружие.

## Корпус

| Группа | Где лежит (локально) |
|---|---|
| Всё извлечённое из исходных файлов | `corpus/texts/`, `corpus/extracted.jsonl` |
| Тексты, на которых строится анализ | `texts/ru`, `texts/fr`, `texts/oral`, `texts/twins`, манифест `texts/manifest.csv` |
| Внешние источники фактов | `refs/facts_profile.md` (фактологический профиль), `refs/wiki_fr_summary.md` |

Источники текстов: папки `~/projects/Romain Gary`, `~/projects/Romain gry` и несколько файлов
из `~/Downloads` (явный список в `extract.py`). Классификация — по содержимому (`manifest.py`),
годы — по библиографии французской Википедии, переводчики — из выходных данных книг и fb2,
для трёх книг Ажара — из каталогов изданий.

## Пайплайн

| Шаг | Скрипт | Результат (локально) |
|---|---|---|
| 1. Извлечение текста (EPUB, fb2, docx, rtf, md, txt) | `extract.py` | `corpus/` |
| 2. Манифест: роль, подпись, год, переводчик, дубли | `manifest.py` | `texts/`, `texts/manifest.csv` |
| 3. Очистка, абзацы, говорящие, леммы | `analysis/prepare.py` (+ `analysis/lemmatize_fr.py` в `.venv-fr`) | `analysis/corpus.pkl` |
| 4. Голоса: дельта Барроуза | `analysis/voices.py` | `analysis/voices.json` |
| 5. Меры прозы, слова, темы, мир, мифы | `analysis/compute.py` | `analysis/stats.json` |
| 6. Отчёт | `analysis/build_report.py` (`report.head.html`, `report.body.html`, `report.lib.js`, `report.app.js`, `report.chrome.js`) | `docs/prosvet.html` |
| 7. Живой портрет на первом экране и биография в «Хронологии» | `analysis/live_portrait/`: `portrait_block.py` (разметка, подставляется `build_report.py` вместо `{{PORTRAIT}}`, `{{PORTRAIT_JS}}`, `{{BIO_CARD}}`), `portrait.js` (поведение), `sync_assets.py` (`bio` — подпись и биография из naprosvet/gary-live; `final` — ролик и постер; `deploy` — ролик рядом со страницами); `analysis/wrap_site.py` — обёртка сайта | `docs/portrait.mp4`, `docs/portrait.webm` рядом с `docs/prosvet.html`; постер встроен в страницу (`live_portrait/final/portrait-poster.webp` в git, ролик в `.gitignore`). Без `final/` `build_report.py` падает |

## Запуск

```bash
pip install -r requirements.txt
python extract.py --qa
python manifest.py

cd analysis
python -m venv .venv-fr && .venv-fr/bin/pip install -r requirements-fr.txt
.venv-fr/bin/python -m spacy download fr_core_news_sm
python prepare.py --qa
python voices.py
python compute.py --qa
python build_report.py            # → ../docs/prosvet.html
```

## Методика

Определения мер, пороги, все ручные исправления и известные ошибки — в разделе «Методика» отчёта.
Кратко: леммы `pymorphy3` (без снятия омонимии) и `spaCy fr_core_news_sm`; фраза — до точки,
«!», «?» или многоточия; диалог — абзацы, начинающиеся с тире; стилометрия — дельта Барроуза
по 100/200/300 частым словоформам на сбалансированной выборке, только повествование, без имён;
вердикт ставится, если он устойчив на всех трёх наборах. Французская и русская шкалы не
смешиваются. Ручной разметки нет.
