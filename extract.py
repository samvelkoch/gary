"""Шаг 1. Извлечь текст из всех файлов в папках с материалами о Гари.

Каждый файл → corpus/texts/<id>.txt и строка в corpus/extracted.jsonl
(путь, формат, число слов, язык по алфавиту, md5, начало текста).
Классификация (роль, псевдоним, год) делается следующим шагом по содержимому, не по имени файла.
"""
import argparse, hashlib, html, json, os, re, zipfile
from pathlib import Path

SRC = [Path.home() / "projects" / "Romain Gary", Path.home() / "projects" / "Romain gry"]
OUT = Path(__file__).parent / "corpus"
DL = Path.home() / "Downloads"
# найдено в ~/Downloads поиском по диску: Ажар по-русски и fb2 с метаданными (переводчик, язык оригинала)
EXTRA = sorted(DL.glob("Gari_*.fb2.zip")) + [
    DL / "Azhar.Golubchik.174170.rtf",
    DL / "[French (auto-generated)] Romain Gary (1975) [DownSub.com].txt",
]

BLOCK = re.compile(r"</?(p|div|h[1-6]|li|tr|blockquote|section|title)\b[^>]*>", re.I)


def html_to_text(x: str) -> str:
    x = re.sub(r"<(script|style|head)\b.*?</\1>", " ", x, flags=re.S | re.I)
    # ссылки на сноски: <a ...><sup>[12]</sup></a>
    x = re.sub(r"<a\b[^>]*>\s*<sup[^>]*>.*?</sup>\s*</a>", "", x, flags=re.S | re.I)
    x = re.sub(r"<sup[^>]*>\s*\[?\d+\]?\s*</sup>", "", x, flags=re.I)
    x = re.sub(r"[\r\n]+", " ", x)
    x = re.sub(r"<br\b[^>]*>", "\n", x, flags=re.I)
    x = BLOCK.sub("\n\n", x)
    x = html.unescape(re.sub(r"<[^>]+>", "", x))
    x = re.sub(r"[ \t ]+", " ", x)
    x = re.sub(r" *\n *", "\n", x)
    return re.sub(r"\n{3,}", "\n\n", x).strip()


def epub_items(z: zipfile.ZipFile):
    """Документы в порядке spine."""
    opf_name = next(n for n in z.namelist() if n.endswith(".opf"))
    opf = z.read(opf_name).decode("utf-8", "replace")
    base = os.path.dirname(opf_name)
    href = {}
    for tag in re.findall(r"<item\b[^>]*>", opf):
        i = re.search(r'\bid="([^"]+)"', tag); h = re.search(r'\bhref="([^"]+)"', tag)
        if i and h:
            href[i.group(1)] = os.path.normpath(os.path.join(base, h.group(1))) if base else h.group(1)
    for idref in re.findall(r'<itemref\b[^>]*idref="([^"]+)"', opf):
        h = href.get(idref)
        if h and h in z.namelist() and h.endswith((".xhtml", ".html", ".htm")):
            yield h, z.read(h).decode("utf-8", "replace")


NOTE_ID = re.compile(r'<h\d\b[^>]*\bid="n_\d+"')  # fb2→calibre: каждая сноска — отдельный документ с <h1 id="n_12">


def epub_text(z: zipfile.ZipFile) -> tuple[str, str, int]:
    """Текст книги без сносок; отдельно — служебная часть (аннотация, выходные данные)."""
    body, notes = [], 0
    for name, x in epub_items(z):
        if "titlepage" in name:
            continue
        t = html_to_text(x)
        if NOTE_ID.search(x):
            notes += 1
            continue
        body.append(t)
    full = "\n\n".join(body)
    return full, notes


def fb2_text(p: Path) -> tuple[str, dict]:
    z = zipfile.ZipFile(p); raw = z.read(z.namelist()[0])
    enc = re.search(rb'encoding="([^"]+)"', raw[:200])
    x = raw.decode(enc.group(1).decode() if enc else "utf-8", "replace")
    ti = re.search(r"<title-info>(.*?)</title-info>", x, re.S).group(1)
    person = lambda t: " ".join(re.findall(r">\s*([^<\s][^<]*?)\s*<", t))
    meta = {"fb2_title": "".join(re.findall(r"<book-title>(.*?)</book-title>", ti)),
            "fb2_tr": "; ".join(person(t) for t in re.findall(r"<translator>(.*?)</translator>", ti, re.S)),
            "fb2_src_lang": "".join(re.findall(r"<src-lang>(.*?)</src-lang>", ti))}
    bodies = re.findall(r"<body\b([^>]*)>(.*?)</body>", x, re.S)
    main = "\n".join(b for attrs, b in bodies if 'name="notes"' not in attrs and 'name="comments"' not in attrs)
    main = re.sub(r"<a\b[^>]*type=\"note\"[^>]*>.*?</a>", "", main, flags=re.S)
    main = re.sub(r"<(v|p|subtitle)\b[^>]*>", "\n", main)
    main = re.sub(r"<(section|title|stanza|poem|epigraph|empty-line)\b[^>]*/?>", "\n\n", main)
    t = html.unescape(re.sub(r"<[^>]+>", "", main))
    t = re.sub(r"[ \t\u00a0]+", " ", t); t = re.sub(r" *\n *", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip(), meta


def rtf_text(p: Path) -> str:
    import subprocess
    return subprocess.run(["textutil", "-convert", "txt", "-stdout", str(p)], capture_output=True, text=True, check=True).stdout


def docx_text(p: Path) -> str:
    x = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8", "replace")
    x = re.sub(r"<w:tab/>", "\t", x)
    x = re.sub(r"</w:p>", "\n\n", x)
    x = html.unescape(re.sub(r"<[^>]+>", "", x))
    return re.sub(r"\n{3,}", "\n\n", x).strip()


def lang_of(t: str) -> str:
    cyr = len(re.findall(r"[а-яё]", t, re.I)); lat = len(re.findall(r"[a-zàâçéèêëîïôûùüÿœ]", t, re.I))
    tot = cyr + lat or 1
    if cyr / tot > 0.8: return "ru"
    if lat / tot > 0.8:
        fr = len(re.findall(r"\b(le|la|les|des|est|une|que|qui|pas|dans)\b", t[:20000], re.I))
        en = len(re.findall(r"\b(the|and|is|of|that|was|with|not)\b", t[:20000], re.I))
        return "fr" if fr >= en else "en"
    return "mixed"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--qa", action="store_true"); a = ap.parse_args()
    (OUT / "texts").mkdir(parents=True, exist_ok=True)
    rows = []
    items = [(p, root.parent) for root in SRC for p in sorted(root.rglob("*"))] + [(p, DL.parent) for p in EXTRA]
    for p, base in items:
            if not p.is_file() or p.name.startswith(("~$", ".")) or "__MACOSX" in p.parts:
                continue
            ext = p.suffix.lower(); notes = 0; text = None; meta = {}
            try:
                if p.name.endswith(".fb2.zip"):
                    text, meta = fb2_text(p)
                elif ext == ".rtf":
                    text = rtf_text(p)
                elif ext == ".epub":
                    text, notes = epub_text(zipfile.ZipFile(p))
                elif p.name.endswith(".epub.zip"):
                    z = zipfile.ZipFile(p)
                    inner = next(n for n in z.namelist() if n.endswith(".epub"))
                    import io
                    text, notes = epub_text(zipfile.ZipFile(io.BytesIO(z.read(inner))))
                elif ext == ".docx":
                    text = docx_text(p)
                elif ext in (".md", ".txt"):
                    text = p.read_bytes().decode("utf-8", "replace")
            except Exception as e:  # журнал пропусков
                rows.append({"path": str(p.relative_to(base)), "fmt": ext, "error": repr(e)})
                continue
            rel = str(p.relative_to(base))
            fid = hashlib.md5(rel.encode()).hexdigest()[:10]
            row = {"id": fid, "path": rel, "fmt": ext if text is not None else ext + " (не текст)",
                   "bytes": p.stat().st_size, **meta}
            if text is not None:
                norm = re.sub(r"\s+", " ", text).strip().lower()
                row.update(words=len(text.split()), lang=lang_of(text), notes_dropped=notes,
                           md5=hashlib.md5(norm.encode()).hexdigest(), head=re.sub(r"\s+", " ", text[:200]))
                (OUT / "texts" / f"{fid}.txt").write_text(text, encoding="utf-8")
            rows.append(row)
    with open(OUT / "extracted.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"файлов: {len(rows)}, с текстом: {sum('words' in r for r in rows)}, ошибок: {sum('error' in r for r in rows)}")
    if a.qa:
        for r in rows:
            print(f"{r.get('words', 0):>7} {r.get('lang', '-'):5} n={r.get('notes_dropped', 0):<3} {r['path'][:80]}  {r.get('error', '')}")


if __name__ == "__main__":
    main()
