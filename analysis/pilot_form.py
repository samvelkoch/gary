"""Страница слепой разметки иронии для заказчика → analysis/pilot_form.html (публикуется как приватный артефакт с db).
Показывает 80 фрагментов из pilot_sample.json без слоя и без маркеров; ответ пишется в db: labels/<id> = {v, target, at}."""
import json
from pathlib import Path

HERE = Path(__file__).parent
S = json.load(open(HERE / "pilot_sample.json"))
by = {x["id"]: x for x in S["sample"]}
items = [{"id": i, "book": by[i]["book"], "text": by[i]["text"]} for i in S["user_ids"]]
data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
html = r"""<title>Ирония у Гари</title>
<style>
/* Лист самиздата, как у отчёта «на просвет»: светлые карточки на тёплом фоне, красный карандаш для отметок. */
:root{ --page:#e9e4da; --surface:#fcfaf5; --ink:#211b16; --ink-2:#4b4238; --muted:#675d51; --rule:#cfc6b6; --mark:#b8391f;
  --yes:#0d6f42; --no:#8a7f70; --unsure:#85560a; --sel-ink:#fcfaf5;
  --f-body:"PT Serif", Georgia, serif; --f-mono:"IBM Plex Mono", ui-monospace, Menlo, monospace; }
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ color-scheme:dark; --page:#16110e; --surface:#211b17; --ink:#f0e8d8; --ink-2:#c4b9a6;
  --muted:#9c907e; --rule:#362d25; --mark:#ff8064; --yes:#4cd08a; --no:#a09480; --unsure:#e6b04a; --sel-ink:#16110e; } }
:root[data-theme="dark"]{ color-scheme:dark; --page:#16110e; --surface:#211b17; --ink:#f0e8d8; --ink-2:#c4b9a6; --muted:#9c907e; --rule:#362d25;
  --mark:#ff8064; --yes:#4cd08a; --no:#a09480; --unsure:#e6b04a; --sel-ink:#16110e; }
*{box-sizing:border-box}
body{background:var(--page); color:var(--ink); font-family:var(--f-body); font-size:17px; line-height:1.55; margin:0; padding-block:0 60px; padding-inline:16px}
.wrap{max-width:760px; margin-inline:auto}
header{position:sticky; top:env(safe-area-inset-top,0px); z-index:5; background:var(--page); padding-block:18px 10px; border-bottom:1px solid var(--rule)}
h1{font-family:var(--f-mono); font-size:22px; letter-spacing:-.01em; margin:0 0 6px; text-transform:uppercase}
.lead{margin:0 0 10px; color:var(--ink-2); font-size:15.5px}
.bar{height:6px; background:var(--rule); border-radius:3px; overflow:hidden}
.bar i{display:block; height:100%; width:0; background:var(--mark); transition:width .3s}
.count{font-family:var(--f-mono); font-size:12.5px; color:var(--muted); margin-top:6px; display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap}
.state{color:var(--mark)}
article{background:var(--surface); border:1px solid var(--rule); padding:16px 18px 14px; margin-top:16px}
.meta{font-family:var(--f-mono); font-size:11.5px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); margin-bottom:8px}
.txt{margin:0 0 12px; white-space:pre-wrap}
.row{display:flex; flex-wrap:wrap; gap:8px; align-items:center}
.row button{font-family:var(--f-mono); font-size:13px; padding:6px 12px; border:1.5px solid var(--rule); background:transparent; color:var(--ink); border-radius:2px; cursor:pointer}
.row button:hover{border-color:var(--ink)}
.row button[aria-pressed="true"][data-v="yes"]{background:var(--yes); border-color:var(--yes); color:var(--sel-ink)}
.row button[aria-pressed="true"][data-v="no"]{background:var(--no); border-color:var(--no); color:var(--sel-ink)}
.row button[aria-pressed="true"][data-v="unsure"]{background:var(--unsure); border-color:var(--unsure); color:var(--sel-ink)}
.row button:focus-visible, input:focus-visible{outline:2px solid var(--mark); outline-offset:2px}
input[type=text]{flex:1; min-width:0; font:inherit; font-size:15px; padding:6px 10px; border:1px solid var(--rule); background:var(--page); color:var(--ink); border-radius:2px}
.done{border-left:4px solid var(--mark)}
.note{font-size:14px; color:var(--muted); margin-top:18px}
</style>
<div class="wrap">
<header>
  <h1>Ирония у Гари: слепая разметка</h1>
  <p class="lead">80 абзацев из трёх книг. Для каждого решите: есть ли здесь ирония или сарказм автора (или рассказчика). Если есть и понятно, над кем или чем, — коротко напишите. Думать долго не нужно: первое впечатление — это и есть данные.</p>
  <div class="bar"><i id="prog"></i></div>
  <div class="count"><span id="cnt">размечено 0 из 80</span><span class="state" id="state">подключаюсь к хранилищу…</span></div>
</header>
<main id="list"></main>
<p class="note">Ответы сохраняются сразу после нажатия. Можно закрыть страницу и вернуться. Порядок абзацев случайный; какие из них отобраны автоматически, не показано намеренно.</p>
</div>
<script type="application/json" id="items">__DATA__</script>
<script>
const ITEMS = JSON.parse(document.getElementById('items').textContent);
const L = {}; let db = null, writable = true;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const list = document.getElementById('list');
list.innerHTML = ITEMS.map((x,i)=>`<article id="a-${x.id}"><div class="meta">${i+1} / ${ITEMS.length} · ${esc(x.book)}</div><p class="txt">${esc(x.text)}</p>
  <div class="row"><button type="button" data-id="${x.id}" data-v="yes" aria-pressed="false">ирония есть</button><button type="button" data-id="${x.id}" data-v="no" aria-pressed="false">нет</button><button type="button" data-id="${x.id}" data-v="unsure" aria-pressed="false">не уверен</button>
  <label class="sr" for="t-${x.id}" style="position:absolute;left:-9999px">над кем или чем</label><input type="text" id="t-${x.id}" data-id="${x.id}" placeholder="над кем / чем (необязательно)" autocomplete="off"></div></article>`).join('');
function paint(){
  let n = 0;
  ITEMS.forEach(x => { const r = L[x.id]; const art = document.getElementById('a-'+x.id);
    art.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(!!r && r.v === b.dataset.v)));
    const inp = document.getElementById('t-'+x.id); if (r && document.activeElement !== inp && inp.value !== (r.target||'')) inp.value = r.target || '';
    art.classList.toggle('done', !!(r && r.v)); if (r && r.v) n++; });
  document.getElementById('cnt').textContent = `размечено ${n} из ${ITEMS.length}`;
  document.getElementById('prog').style.width = (100*n/ITEMS.length)+'%';
}
const state = t => { document.getElementById('state').textContent = t; };
async function save(id, patch){
  if (!db || !writable) { state('сохранить нельзя: хранилище недоступно'); return; }
  const next = {...(L[id]||{}), ...patch, at: new Date().toISOString()};
  L[id] = next; paint();
  try { await db.collection('labels').doc(id).set(next); state('сохранено'); }
  catch(e){ if (e && e.code === 'invalid_argument') { writable = false; state('у вас нет права записи на этой странице'); }
            else if (e && e.code === 'unavailable') { setTimeout(()=>db.collection('labels').doc(id).set(next).then(()=>state('сохранено')).catch(()=>state('не сохранилось, попробуйте ещё раз')), 800+Math.random()*800); }
            else state('не сохранилось: ' + (e && e.code || 'ошибка')); }
}
list.addEventListener('click', e => { const b = e.target.closest('button[data-v]'); if (b) save(b.dataset.id, {v: b.dataset.v}); });
const timers = {};
list.addEventListener('input', e => { const t = e.target.closest('input[data-id]'); if (!t) return; const id = t.dataset.id;
  clearTimeout(timers[id]); timers[id] = setTimeout(()=>save(id, {target: t.value.trim()}), 700); });
paint();
(async () => {
  try { db = await (window.claude && window.claude.use ? window.claude.use('db') : null); } catch(e){ db = null; }
  if (!db) { state('хранилище недоступно в этом окне — ответы не сохранятся'); return; }
  state('хранилище подключено');
  db.collection('labels').onSnapshot(snap => { snap.docs.forEach(d => { if (d.exists) L[d.id] = d.data(); }); paint(); },
    e => state('связь с хранилищем прервалась: ' + (e && e.code || '')));
})();
</script>
"""
(HERE / "pilot_form.html").write_text(html.replace("__DATA__", data), encoding="utf-8")
print("pilot_form.html", round((HERE / "pilot_form.html").stat().st_size / 1024), "KB,", len(items), "фрагментов")
