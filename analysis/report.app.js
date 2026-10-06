/* ================= данные и названия ================= */
const A = D.atlas, PER = D.periods, NPER = PER.length;
const RU_T = {"Le Vin des morts":"Вино мертвецов","Éducation européenne":"Европейское воспитание","Tulipe":"Тюльпан","Le Grand Vestiaire":"Большая барахолка",
 "Les Couleurs du jour":"Цвета дня","Les Racines du ciel":"Корни неба","La Promesse de l'aube":"Обещание на рассвете","Citoyen pigeon":"Гражданин голубь",
 "Décadence":"Декаданс","Gloire à nos illustres pionniers":"Слава нашим доблестным первопроходцам","J'ai soif d'innocence":"Как я мечтал о бескорыстии",
 "Je parle de l'héroïsme":"Я говорю о героизме","La Plus Vieille Histoire du monde":"Старая-престарая история","Le Faux":"Подделка","Le Luth":"Лютня",
 "Les Habitants de la Terre":"Жители Земли","Les Joies de la nature":"Радости природы","Les oiseaux vont mourir au Pérou":"Птицы прилетают умирать в Перу",
 "Tout va bien sur le Kilimandjaro":"На Килиманджаро всё в порядке","Un humaniste":"Гуманист","Une page d'histoire":"Страница истории","Lady L.":"Леди Л.",
 "Les Mangeurs d'étoiles":"Пожиратели звёзд","La Danse de Gengis Cohn":"Пляска Чингиз-Хаима","La Tête coupable":"Повинная голова",
 "Adieu Gary Cooper":"Прощай, Гари Купер!","Chien blanc":"Белая собака","Europa":"Европа","Les Enchanteurs":"Чародеи","Gros-Câlin":"Голубчик",
 "Les Têtes de Stéphanie":"Головы Стефани","Au-delà de cette limite votre ticket n'est plus valable":"Дальше ваш билет недействителен",
 "La Vie devant soi":"Вся жизнь впереди","Pseudo":"Псевдо","Charge d'âme":"Спасите наши души","Clair de femme":"Свет женщины",
 "L'Angoisse du roi Salomon":"Страхи царя Соломона","Les Clowns lyriques":"Грустные клоуны","Les Cerfs-volants":"Воздушные змеи",
 "La nuit sera calme":"Ночь будет спокойной","Vie et mort d'Émile Ajar":"Жизнь и смерть Эмиля Ажара","L'Homme à la colombe":"Человек с голубкой"};
const clean = w => String(w).replace(/\s*\(оригинал не установлен\)/,'');
const T = a => a.lang==='fr' ? a.work : (RU_T[a.work] || clean(a.work));
const TQ = a => `«${T(a)}»`;
const TS = (a,n=30) => { const t=T(a); return t.length>n ? t.slice(0,n-1)+'…' : t; };
const SIGN = {"Gary":"Гари","Émile Ajar":"Эмиль Ажар","Shatan Bogat":"Шатан Богат","Fosco Sinibaldi":"Фоско Синибальди"};
const SIGNC = {"Gary":"--s1","Émile Ajar":"--s2","Shatan Bogat":"--c3","Fosco Sinibaldi":"--c4"};
const sc = s => `var(${SIGNC[s]||'--neutral-bar'})`;
const LANG = {ru:'рус.', fr:'фр.'};
const ROLE = {own:'художественная проза', self:'Гари о себе'};
const yr = a => a.year || 'без даты';
const big = a => a.lang==='ru' && a.role==='own' && a.words>=10000;
const RU_OWN = A.filter(a=>a.lang==='ru'&&a.role==='own'), FR_OWN = A.filter(a=>a.lang==='fr'&&a.role==='own');
const pct = v => fmt1(v)+'%';
function verdictHTML(v){ const m={yes:['v-yes','✓ подтверждается'],no:['v-no','✗ не подтверждается'],part:['v-part','≈ отчасти'],none:['v-part','цифрами не решается']}[v]||['v-part','—'];
  return `<span class="verdict ${m[0]}">${m[1]}</span>`; }
function legendTo(host, items){ host.innerHTML=items.map(([l,c])=>`<span><i style="background:${c}"></i>${esc(l)}</span>`).join(''); }
const SIGN_ITEMS = [['Гари','var(--s1)'],['Эмиль Ажар','var(--s2)'],['Шатан Богат','var(--c3)'],['Фоско Синибальди','var(--c4)']];

/* ================= шапка ================= */
const O = D.overview;
const VF = V.fr.variants, F200 = VF.narr.by_mfw['200'];
$('#lede').innerHTML = `${O.ru_texts} ${plural(O.ru_texts, ['текст', 'текста', 'текстов'])} в русском переводе и ${O.fr_texts} ${plural(O.fr_texts, ['французский оригинал', 'французских оригинала', 'французских оригиналов'])}, ${fmt(O.ru_words+O.fr_words)} ${plural(O.ru_words+O.fr_words, ['слово', 'слова', 'слов'])}, плюс интервью и эссе «о себе». `+
  `Главное видно по оригиналам: <strong>под маской Эмиля Ажара Гари действительно писал другим голосом</strong> — «Жизнь впереди» отстоит от его романов дальше (${fmt2(F200.ajar_gary)}), чем два романа Гари друг от друга (${fmt2(F200.base[0])}). `+
  `А Фоско Синибальди по частым словам от Гари не отличить.`;
const FIG=[[fmt(O.ru_texts),plural(O.ru_texts, ['текст', 'текста', 'текстов'])+' в русском переводе'],[fmt(Math.round(O.ru_words/1000))+' тыс.','слов в переводах'],[fmt(Math.round(O.fr_words/1000))+' тыс.','слов во французских оригиналах'],
  ['4','подписи: Гари, Ажар, Богат, Синибальди'],[fmt(O.translators),plural(O.translators, ['переводчик', 'переводчика', 'переводчиков'])]];
$('#figures').innerHTML=FIG.map(([n,l])=>`<div class="fig"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');

/* листы: книги по годам, абзацы — штрихами */
const LEX = D.lex; const LEXN = {}; Object.keys(LEX).forEach(k=>{ LEXN[norm(k)]=k; }); const LEXK = Object.keys(LEXN);
const lexBooks = k => { const L=LEX[k]; if(!L) return new Map(); const m=new Map(); for(let i=0;i<L[3].length;i+=2) m.set(L[3][i],L[3][i+1]); return m; };
const GROUPS = [['1937–1962', a=>a.lang==='ru'&&a.role==='own'&&(a.year||0)<=1962&&a.year],['1963–1980', a=>a.lang==='ru'&&a.role==='own'&&((a.year||0)>1962||!a.year)],
  ['оригиналы', a=>a.lang==='fr'&&a.role==='own'],['о себе', a=>a.role==='self']];
const hs = {hl:null, sel:null}; let SH=null;
function drawSheets(){
  const box=$('#sheets'), cv=$('#sheets-cv'); const W=box.clientWidth; const dpr=Math.min(2,devicePixelRatio||1);
  const labW = W<560?0:88, gap=W<560?6:9; const perRow = W<560?8:W<900?12:16;
  const sw=Math.max(28,Math.min(74,(W-labW-gap*(perRow-1))/perRow)), sh=Math.round(sw*2.1), tab=7, capH=16;
  const rows=[]; GROUPS.forEach(([g,f])=>{ const L=A.filter(f); for(let i=0;i<L.length;i+=perRow) rows.push({g:i?'':g, items:L.slice(i,i+perRow)}); });
  const H=rows.length*(sh+tab+capH+gap+6)+4;
  cv.width=W*dpr; cv.height=H*dpr; cv.style.width=W+'px'; cv.style.height=H+'px';
  const c=cv.getContext('2d'); c.setTransform(dpr,0,0,dpr,0,0); c.clearRect(0,0,W,H);
  const hi=hs.hl?lexBooks(hs.hl):null; const hiMax=hi&&hi.size?Math.max(...[...hi.entries()].map(([b,n])=>n/A[b].words)):1;
  const ink=css('--hink'), sheet=css('--hsheet'), mark=css('--hmark'), mute=css('--hmute'), lab=css('--hlabel'), sel=css('--hsel');
  const boxes=[];
  rows.forEach((r,ri)=>{ const y0=ri*(sh+tab+capH+gap+6)+2;
    if(r.g && labW){ c.fillStyle=lab; c.font='12px "IBM Plex Mono", monospace'; c.fillText(r.g,0,y0+tab+14); }
    r.items.forEach((a,j)=>{ const x=labW+j*(sw+gap), y=y0+tab;
      const on = !hi || hi.has(a.i); const alpha = on?1:.22;
      c.globalAlpha=alpha;
      c.fillStyle=css(SIGNC[a.sign]||'--hmute'); c.fillRect(x,y-tab,sw,tab-2);
      c.fillStyle=sheet; c.fillRect(x,y,sw,sh);
      // штрихи абзацев
      const seq=a.seq, k=a.seqk; const inner=sh-8; let n=seq.length; let step=1; while(n/step*1.25>inner) step++;
      const rh=inner/Math.ceil(n/step); const maxw=sw-8;
      for(let i=0,row=0;i<n;i+=step,row++){ let len=0, dl=0, hd=0; for(let q=i;q<Math.min(n,i+step);q++){ len=Math.max(len,seq[q]); if(k[q]==='1') dl++; if(k[q]==='2') hd++; }
        if(hd===Math.min(step,n-i)) continue;
        const w=Math.max(1.5,Math.min(1,len/110)*maxw); c.fillStyle= dl*2>=Math.min(step,n-i) ? mark : ink; c.globalAlpha=alpha*(dl*2>=Math.min(step,n-i)?.95:.7);
        c.fillRect(x+4,y+4+row*rh,w,Math.max(.8,rh*.62)); }
      c.globalAlpha=alpha;
      if(hi && hi.has(a.i)){ const t=Math.min(1,(hi.get(a.i)/a.words)/hiMax); c.strokeStyle=sel; c.lineWidth=1+2.5*t; c.strokeRect(x-1,y-1,sw+2,sh+2); }
      if(hs.sel===a.i){ c.strokeStyle=sel; c.lineWidth=2; c.setLineDash([3,2]); c.strokeRect(x-3,y-tab-3,sw+6,sh+tab+6); c.setLineDash([]); }
      c.fillStyle=lab; c.font='10.5px "IBM Plex Mono", monospace'; c.textAlign='center'; c.fillText(String(a.year||'—')+(a.lang==='fr'?' фр':''),x+sw/2,y+sh+12); c.textAlign='left';
      c.globalAlpha=1; boxes.push({x,y:y-tab,w:sw,h:sh+tab,i:a.i}); }); });
  SH={boxes};
}
function sheetAt(e){ const cv=$('#sheets-cv'); const r=cv.getBoundingClientRect(); const mx=e.clientX-r.left, my=e.clientY-r.top; return SH&&SH.boxes.find(b=>mx>=b.x&&mx<=b.x+b.w&&my>=b.y&&my<=b.y+b.h); }
$('#sheets-cv').addEventListener('pointermove',e=>{ const b=sheetAt(e); if(!b){ tip.hidden=true; return; } const a=A[b.i];
  const hl=hs.hl?lexBooks(hs.hl).get(a.i):null;
  showTipHTML(`<b>${esc(T(a))}</b><br>${yr(a)} · ${SIGN[a.sign]||''} · ${LANG[a.lang]}<br>${pn(a.words,['слово','слова','слов'])} · диалог ${fmt1(a.dlg)}%${hl?`<br>«${esc(hs.hl)}»: ${pnr(hl,['раз','раза','раз'])}`:''}`,e.clientX,e.clientY); });
$('#sheets-cv').addEventListener('pointerleave',()=>{ tip.hidden=true; });
$('#sheets-cv').addEventListener('click',e=>{ const b=sheetAt(e); if(b){ selectBook(b.i,true); } });
legendTo($('#sheets-legend'), SIGN_ITEMS.concat([['реплики диалога','var(--hmark)']]));
chart(drawSheets, $('#sheets'));
function setHL(k){ hs.hl = k&&LEX[k]?k:null; drawSheets();
  const n=hs.hl?lexBooks(hs.hl).size:0; $('#hl-count').textContent = hs.hl?`«${hs.hl}»: ${pn(LEX[hs.hl][0],['раз','раза','раз'])} в ${n} ${plural(n,['книге','книгах'])}`:''; }
function sugg(q,n=8){ const k=norm(q); if(!k) return []; const out=[]; for(const key of LEXK){ if(key.startsWith(k)){ out.push(LEXN[key]); if(out.length>=n) break; } } return out; }
const HL_EX=['слон','мать','клоун','собака','удав','смех','Морель','надежда','еврей','Франция'];
function hlChips(list){ const h=$('#hl-chips'); h.innerHTML=''; list.forEach(k=>{ if(!LEX[k]) return; const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=k; b.addEventListener('click',()=>{ $('#hl-input').value=k; setHL(k); }); h.appendChild(b); }); }
hlChips(HL_EX);
$('#hl-input').addEventListener('input',e=>{ const q=e.target.value; const exact=LEXN[norm(q)]; if(exact){ setHL(exact); } else if(!q.trim()){ setHL(null); hlChips(HL_EX); } else { const s=sugg(q); setHL(null); hlChips(s); $('#hl-count').textContent=s.length?'нет в словаре — выберите слово из подсказок':'нет в словаре'; } });

/* ================= I. обзор ================= */
const MY = Object.fromEntries(D.myths.map(m=>[m.id,m]));
const PR = D.pairs; const promP = PR.find(p=>p.work==="La Promesse de l'aube");
const fwar = D.fields.per.map(r=>r['Война']);
const momRatio = (MY.mother.num.match(/в (\d+) раз/)||[])[1];
const pn0 = D.pantheon[0];
const ajFR = FR_OWN.find(a=>a.sign==='Émile Ajar'), gFR = FR_OWN.filter(a=>a.sign==='Gary');
const FIND=[
  [`${fmt2(F200.ajar_gary)} против ${fmt2(F200.base[0])}`,'расстояние «Жизнь впереди» ↔ романы Гари против расстояния между двумя романами Гари (по оригиналам)'],
  [`×${momRatio}`,'так чаще, чем в типичной книге, в «Обещании на рассвете» звучат слова «мать», «мама», «матушка»'],
  [`${fmt1(fwar[0])} → ${fmt1(fwar[NPER-1])}`,'слов о войне на 1000 слов: от ранних книг (1937–1949) к поздним (1970–1980)'],
  [`${Math.round(100*V.night.bondy.words/(V.night.bondy.words+V.night.gary.words))}%`,'слов «Ночи будет спокойной» приходится на вопросы Франсуа Бонди, остальное — Гари'],
  [`${Math.round(ajFR.mattr)} против ${gFR.map(a=>Math.round(a.mattr)).join('–')}`,'разных слов на каждые 500: словарь Ажара беднее, чем у Гари, хотя фраза такой же длины'],
  [`${esc(pn0[0])} — ${pn0[1]}`,`${plural(pn0[1], ['книга', 'книги', 'книг'])}, где назван ${esc(pn0[0])}: он чаще всех реальных людей появляется у Гари`]];
$('#findings').innerHTML=FIND.map(([b,s])=>`<div><b>${b}</b><span>${s}</span></div>`).join('');
$('#myths').innerHTML=D.myths.map(m=>`<article><p class="q">${esc(m.q)}</p>${verdictHTML(m.v)}<p class="num">${esc(m.num).replace(/(\d)\.(\d)/g,'$1,$2')}</p></article>`).join('');

/* хронология */
const EVENTS=[[1935,'гражданство Франции'],[1940,'к де Голлю'],[1945,'премия критиков'],[1956,'Гонкур'],[1961,'уход из дипломатии'],[1974,'первый Ажар'],[1975,'Гонкур Ажару'],[1980,'смерть']];
const WORKS=D.works;
$('#t-chrono').textContent=`В корпусе ${WORKS.length} ${plural(WORKS.length, ['произведение', 'произведения', 'произведений'])} от «Вина мертвецов» (написано в 1937-м, издано посмертно) до «Воздушных змеев» (1980). Больше всего книг вышло в 1962 году — это рассказы сборника «Слава нашим доблестным первопроходцам»: в корпусе ${WORKS.filter(w=>w.year===1962).length} из шестнадцати.`;
legendTo($('#lg-chrono'), SIGN_ITEMS);
chart(()=>{ const box=$('#c-chrono'); const h=250; const [s,w]=svg(box,h); const L=44,R=10,T0=46,B=26; const y0=1935,y1=1981;
  const sx=y=>L+(w-L-R)*(y-y0)/(y1-y0); const wk=WORKS.filter(x=>x.year).map(x=>({...x,a:A[x.ru!=null?x.ru:x.fr]}));
  const byY={}; wk.forEach(x=>{ (byY[x.year]=byY[x.year]||[]).push(x); });
  const maxStack=Math.max(...Object.values(byY).map(L=>L.reduce((a,x)=>a+x.a.words,0)));
  const mx=niceMax(maxStack/1000); const sy=v=>h-B-(h-B-T0)*v/mx; const ax=el('g',{class:'ax'},s);
  ticks(mx,3).forEach(t=>{ el('line',{x1:L,x2:w-R,y1:sy(t),y2:sy(t),stroke:css('--grid')},ax); txt(ax,L-6,sy(t)+4,fmt(t)+' т.',{'text-anchor':'end'}); });
  for(let y=1940;y<=1980;y+=10) txt(ax,sx(y),h-8,y,{'text-anchor':'middle'});
  EVENTS.forEach(([y,t],i)=>{ const x=sx(y), lv=i%3; el('line',{x1:x,x2:x,y1:T0-8+lv*12,y2:h-B,stroke:css('--muted'),'stroke-dasharray':'2 3'},s);
    const right=x+t.length*6+6<w; txt(s,right?x+3:x-3,T0-10+lv*12,t,{'text-anchor':right?'start':'end',style:'fill:var(--ink-2);font-size:10.5px'}); });
  const bw=Math.max(3,(w-L-R)/(y1-y0)-2);
  Object.entries(byY).forEach(([y,L_])=>{ let acc=0; L_.forEach(x=>{ const v=x.a.words/1000; const top=sy(acc+v), bot=sy(acc);
    el('rect',{x:sx(+y)-bw/2,y:top,width:bw,height:Math.max(1,bot-top-1),fill:sc(x.sign),'data-tip':`<b>${esc(T(x.a))}</b><br>${y} · ${SIGN[x.sign]} · ${pn(x.a.words,['слово','слова','слов'])}${x.a.lang==='fr'?' (оригинал)':''}<br>нажмите — карточка ${y} года`,class:'clickable'},s)
      .addEventListener('click',()=>yearCard(+y,true)); acc+=v; }); });
  el('line',{x1:L,x2:w-R,y1:h-B,y2:h-B,stroke:css('--axis')},s);
}, $('#c-chrono'));
hbars($('#c-corpus'), [
  {l:'Проза, русские переводы',v:O.ru_words/1000},{l:'Проза, оригиналы',v:O.fr_words/1000},{l:'Гари о себе',v:O.self_words/1000},
  {l:'Устная речь (радио)',v:O.oral_words/1000},{l:'Вторые переводы',v:O.twin_words/1000}], {labelW:190, fmtv:v=>fmt(Math.round(v))});
hbars($('#c-signs'), Object.entries(O.ru_by_sign).map(([k,v])=>({l:k,v:v/1000,c:sc(Object.keys(SIGN).find(s=>SIGN[s].includes(k))||'Gary')})).sort((a,b)=>b.v-a.v), {labelW:130, fmtv:v=>fmt(Math.round(v))});

/* ================= II. проза ================= */
function scatterYear(box, rows, {h=280, fmtv=fmt1, q=false, labelTop=4}={}){
  return chart(()=>{ const [s,w]=svg(box,h); const L=44,R=14,T0=16,B=28; const xs=rows.map(r=>r.x), y0=Math.min(...xs)-1, y1=Math.max(...xs)+1;
    const top_=Math.max(...rows.map(r=>q?r.q3:r.v)); const stp=niceMax(top_/4); const vmax=Math.ceil(top_*1.05/stp)*stp;
    const sx=x=>L+(w-L-R)*(x-y0)/(y1-y0), sy=v=>h-B-(h-B-T0)*v/vmax;
    const ax=el('g',{class:'ax'},s); for(let t=0;t<=vmax+1e-9;t+=stp){ el('line',{x1:L,x2:w-R,y1:sy(t),y2:sy(t),stroke:css('--grid')},ax); txt(ax,L-6,sy(t)+4,fmtv(+t.toFixed(6)),{'text-anchor':'end'}); }
    const step=(y1-y0)>30?10:5; for(let y=Math.ceil(y0/step)*step;y<=y1;y+=step) txt(ax,sx(y),h-8,y,{'text-anchor':'middle'});
    rows.forEach(r=>{ const x=sx(r.x); if(q) el('line',{x1:x,x2:x,y1:sy(r.q1),y2:sy(r.q3),stroke:r.c,'stroke-width':2.5,'stroke-linecap':'round',opacity:.4},s); });
    rows.forEach(r=>{ const c=el('circle',{cx:sx(r.x),cy:sy(r.v),r:r.r||5.5,fill:r.c,stroke:css('--surface'),'stroke-width':1.5,'data-tip':r.tip,class:r.onClick?'clickable':''},s);
      if(r.onClick) c.addEventListener('click',r.onClick); });
    // подписи: самые высокие точки, с проверкой пересечений и края
    const placed=[]; const cand=[...rows].filter(r=>r.lab).sort((a,b)=>b.v-a.v).slice(0,labelTop*3); let n=0;
    for(const r of cand){ if(n>=labelTop) break; const tw=r.lab.length*6.3+4, x=sx(r.x), y=sy(r.v)-8; const right=x+8+tw<=w-R;
      const bx=right?x+8:x-8-tw; const b={x0:bx,x1:bx+tw,y0:y-11,y1:y+3};
      if(placed.some(p=>!(b.x1<p.x0||b.x0>p.x1||b.y1<p.y0||b.y0>p.y1))) continue;
      placed.push(b); n++; txt(s,right?x+8:x-8,y,r.lab,{'text-anchor':right?'start':'end',style:'fill:var(--ink);font-size:11px;paint-order:stroke;stroke:var(--surface);stroke-width:3px'}); }
    el('line',{x1:L,x2:w-R,y1:h-B,y2:h-B,stroke:css('--axis')},s);
  }, box);
}
const jitter = i => (((i*2654435761)>>>0)%1000/1000-.5)*.8;
let slLang='ru';
function drawFraza(){ const L=A.filter(a=>a.role==='own'&&a.lang===slLang&&a.year);
  $('#u-fraza').textContent = slLang==='ru'?'русские переводы: точка — медиана, отрезок — от 25% до 75% фраз':'французские оригиналы';
  scatterYear($('#c-fraza'), L.map(a=>({x:a.year+jitter(a.i),v:a.sl_med,q1:a.sl_q1,q3:a.sl_q3,c:sc(a.sign),lab:a.words>=10000?T(a):'',r:a.words>=10000?6:4,
    tip:`<b>${esc(T(a))}</b>, ${a.year}<br>типичная фраза: ${pn(a.sl_med,['слово','слова','слов'],1)} (${fmt1(a.sl_q1)}–${fmt1(a.sl_q3)})<br>перевод: ${esc(a.tr||'—')}`, onClick:()=>selectBook(a.i,true)})), {q:true, labelTop:3}); }
seg($('#sl-lang'), [['ru','русские переводы'],['fr','оригиналы']], 'ru', v=>{ slLang=v; drawFraza(); });
drawFraza();
(()=>{ const B=RU_OWN.filter(a=>a.words>=10000); const mx=B.reduce((a,b)=>b.sl_med>a.sl_med?b:a), mn=B.reduce((a,b)=>b.sl_med<a.sl_med?b:a);
  $('#f-fraza').textContent=`Самая длинная типичная фраза в книге ${TQ(mx)} (${pn(mx.sl_med,['слово','слова','слов'],1)}), самая короткая — в книге ${TQ(mn)} (${fmt1(mn.sl_med)}). По-французски фраза длиннее: у трёх книг, которые есть на обоих языках, ${PR.map(p=>`${fmt1(p.sl[0])} → ${fmt1(p.sl[1])}`).join(', ')} слов (оригинал → перевод).`; })();
(()=>{ const B=RU_OWN.filter(big).sort((a,b)=>b.dlg-a.dlg);
  hbars($('#c-dialog'), B.map(a=>({l:`${TS(a)} · ${a.year||''}`,v:a.dlg,c:sc(a.sign),tip:`<b>${esc(T(a))}</b><br>${fmt1(a.dlg)}% слов в репликах<br>перевод: ${esc(a.tr||'—')}`,i:a.i})), {labelW:260, unit:'%', rowH:22, onClick:r=>selectBook(r.i,true)});
  const p=B[B.length-1];
  $('#f-dialog').textContent=`Самая разговорная книга — ${TQ(B[0])}: ${fmt1(B[0].dlg)}% слов в репликах. Самая молчаливая — ${TQ(p)}: ${fmt1(p.dlg)}%. Медиана по книгам — ${fmt1([...B].sort((a,b)=>a.dlg-b.dlg)[Math.floor(B.length/2)].dlg)}%.`; })();
(()=>{ const B=RU_OWN.filter(big);
  scatterYear($('#c-ya'), B.map(a=>({x:a.year+jitter(a.i),v:a.fp,c:sc(a.sign),lab:T(a),tip:`<b>${esc(T(a))}</b>, ${a.year}<br>«я» на 1000 слов: ${fmt1(a.fp)}`,onClick:()=>selectBook(a.i,true)})), {labelTop:5});
  const s=[...B].sort((a,b)=>b.fp-a.fp); const aj=B.filter(a=>a.sign==='Émile Ajar');
  const med=L=>{ const v=L.map(a=>a.fp).sort((x,y)=>x-y); return v[Math.floor(v.length/2)]; };
  const early=B.filter(a=>a.sign==='Gary'&&a.year<1963), late=B.filter(a=>a.sign==='Gary'&&a.year>=1970);
  $('#f-ya').textContent=`Больше всего «я» в книге ${TQ(s[0])} (${fmt1(s[0].fp)} на 1000 слов) и ${TQ(s[1])} (${fmt1(s[1].fp)}). Все четыре романа Ажара написаны от первого лица: ${aj.map(a=>fmt1(a.fp)).join(', ')}. У позднего Гари (1970–1980) типичная книга даёт ${fmt1(med(late))} «я» на 1000 слов, у раннего (до 1963) — ${fmt1(med(early))}: к концу жизни Гари всё чаще рассказывает от себя.`; })();
const MARKS=[['!','!'],['?','?'],['…','…'],['— внутри фразы','тире'],[';',';'],['(','скобки']];
let pmKey='!';
function drawZnaki(){ const B=RU_OWN.filter(big);
  scatterYear($('#c-znaki'), B.map(a=>({x:a.year+jitter(a.i),v:a.punct[pmKey],c:sc(a.sign),lab:T(a),tip:`<b>${esc(T(a))}</b>, ${a.year}<br>«${esc(pmKey)}» на 1000 слов: ${fmt1(a.punct[pmKey])}`,onClick:()=>selectBook(a.i,true)})), {labelTop:3}); }
seg($('#pm-seg'), MARKS, '!', v=>{ pmKey=v; drawZnaki(); });
drawZnaki();
(()=>{ const B=RU_OWN.filter(big).sort((a,b)=>b.punct['!']-a.punct['!']); const late=B.filter(a=>a.year>=1963);
  $('#f-znaki').textContent=`Восклицательных знаков больше всего в ранних книгах: ${TQ(B[0])} — ${fmt1(B[0].punct['!'])} на 1000 слов, ${TQ(B[1])} — ${fmt1(B[1].punct['!'])}. В книгах после 1962 года их в среднем ${fmt1(late.reduce((s,a)=>s+a.punct['!'],0)/late.length)}.`; })();

/* атлас */
let atSort='year';
function drawAtlasList(){ const L=[...A]; if(atSort==='words') L.sort((a,b)=>b.words-a.words); else if(atSort==='dlg') L.sort((a,b)=>b.dlg-a.dlg); else if(atSort==='sl') L.sort((a,b)=>b.sl_med-a.sl_med);
  const key={year:'words',words:'words',dlg:'dlg',sl:'sl_med'}[atSort]; const u={year:'',words:'',dlg:'%',sl:''}[atSort];
  hbars($('#c-atlas'), L.map(a=>({l:`${TS(a)} · ${yr(a)}${a.lang==='fr'?' · фр.':''}`,v:key==='words'?a.words/1000:a[key],c:sc(a.sign),i:a.i,
    tip:`<b>${esc(T(a))}</b> — ${key==='words'?pn(a.words,['слово','слова','слов']):fmt1(a[key])+u}`})), {labelW:270, rowH:20, onClick:r=>selectBook(r.i,false), fmtv:key==='words'?v=>fmt(Math.round(v))+' т.':fmt1, unit:key==='words'?'':u}); }
seg($('#at-sort'), [['year','по годам'],['words','по объёму'],['sl','по фразе'],['dlg','по диалогу']], 'year', v=>{ atSort=v; drawAtlasList(); });
drawAtlasList();
function selectBook(i, scroll){ hs.sel=i; drawSheets(); const a=A[i]; const host=$('#card');
  const orig = a.lang==='ru' && RU_T[a.work] ? `<i>${esc(a.work)}</i>` : '';
  const tiles=[[fmt(a.words),plural(a.words,['слово','слова','слов'])],[fmt1(a.sl_med),plural(a.sl_med,['слово в типичной фразе','слова в типичной фразе','слов в типичной фразе'],1)],[fmt1(a.dlg)+'%','в репликах'],[fmt1(a.fp),'«я» на 1000 слов'],[a.mattr?Math.round(a.mattr):'—',a.mattr?plural(Math.round(a.mattr),['разное слово на 500','разных слова на 500','разных слов на 500']):'разных слов на 500'],[fmt1(a.punct['!']),'«!» на 1000 слов']];
  const chars=a.char.slice(0,12).map(([w,z])=>`<button type="button" class="chip" data-w="${esc(w)}">${esc(w)}</button>`).join('');
  const names=a.names.slice(0,8).map(([n,c])=>`${esc(n)} <span class="muted">${c}</span>`).join(' · ');
  let fl=''; if(a.fields && Object.keys(a.fields).length){ const avg=D.fields.per.reduce((acc,r)=>{ for(const k in r) acc[k]=(acc[k]||0)+r[k]/NPER; return acc; },{});
    const top=Object.entries(a.fields).map(([k,v])=>[k,v,v/(avg[k]||1e-9)]).sort((x,y)=>y[2]-x[2]).slice(0,5);
    fl=`<h4>Темы громче обычного</h4><div class="mini">${top.map(([k,v,r])=>`<span>${esc(k)}</span><span class="bars"><i style="width:${Math.min(100,r*25)}%;background:${sc(a.sign)}"></i></span>`).join('')}</div>`; }
  host.innerHTML=`<div class="eyebrow">${a.role==='self'?'Гари о себе':'атлас'} · ${LANG[a.lang]}</div><div class="ttl">${esc(T(a))}</div>
    <div class="meta">${orig?orig+' · ':''}${yr(a)} · <span class="tagl" style="background:${sc(a.sign)}">${SIGN[a.sign]||''}</span>${a.lang==='ru'?` · перевод: ${esc(a.tr||'нет данных')}`:''}</div>
    <div class="tiles">${tiles.map(([b,s])=>`<div><b>${b}</b><span>${s}</span></div>`).join('')}</div>
    <h4>Строение: абзацы по порядку</h4><div class="struct" id="card-struct"></div><p class="struct-note">Штрих — абзац, длина — число слов. Красные — реплики диалога.</p><button type="button" class="btn" id="card-cmp" style="margin-top:10px">+ в «Строение рядом»</button>
    <h4>Характерные слова</h4><div class="chips">${chars||'<span class="muted">—</span>'}</div>
    <h4>Главные имена и места</h4><p style="font-size:14.5px;margin:0">${names||'—'}</p>${fl}
    <h4>Первая фраза</h4><blockquote>${esc(a.first)}</blockquote><h4>Последняя фраза</h4><blockquote>${esc(a.last)}</blockquote>`;
  host.querySelectorAll('button[data-w]').forEach(b=>b.addEventListener('click',()=>{ const k=LEXN[norm(b.dataset.w)]; if(k){ openWord(k,true); } }));
  drawStruct($('#card-struct'), a); $('#card-cmp').addEventListener('click',()=>{ cmpAdd(i); goTo('cmp-panel'); });
  if(scroll) document.getElementById('atlas').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}); }
function drawStruct(host, a){ const W=Math.max(200,host.clientWidth||300); const n=a.seq.length; const rh=Math.max(1.4,Math.min(4,560/n)); const H=Math.ceil(n*rh)+4;
  const cv=document.createElement('canvas'); const dpr=Math.min(2,devicePixelRatio||1); cv.width=W*dpr; cv.height=H*dpr; cv.style.width=W+'px'; cv.style.height=H+'px'; host.innerHTML=''; host.appendChild(cv);
  const c=cv.getContext('2d'); c.setTransform(dpr,0,0,dpr,0,0); const mx=Math.min(250,Math.max(...a.seq)); const ink=css('--ink-2'), mark=css('--mark');
  a.seq.forEach((v,i)=>{ const k=a.seqk[i]; if(k==='2') return; c.fillStyle=k==='1'?mark:ink; c.globalAlpha=k==='1'?.9:.55; c.fillRect(0,2+i*rh,Math.max(2,Math.min(1,v/mx)*(W-4)),Math.max(.8,rh*.7)); }); c.globalAlpha=1; }
selectBook(A.findIndex(a=>a.work==="La Promesse de l'aube"&&a.lang==='ru'), false);

/* ================= III. слова ================= */
let twLang='ru', twPos='nouns';
function drawTop(){ const L=D.top_words[twLang][twPos]; hbars($('#c-top'), L.slice(0,20).map(([w,n,r])=>({l:w,v:r,tip:`${esc(w)}: ${pn(n,['раз','раза','раз'])}, ${fmt1(r)} на 10 000`,w})), {labelW:120, rowH:22,
  onClick:twLang==='ru'?(r=>{ const k=LEXN[norm(r.w)]; if(k) openWord(k,true); }):null}); }
seg($('#tw-lang'), [['ru','переводы'],['fr','оригиналы']], 'ru', v=>{ twLang=v; drawTop(); });
seg($('#tw-pos'), [['nouns','существительные'],['verbs','глаголы'],['adjs','прилагательные']], 'nouns', v=>{ twPos=v; drawTop(); });
drawTop();

const X_EX=['слон','мать','клоун','надежда','удав','смех','Морель','Роза','достоинство','еврей','собака','Африка'];
function xSug(list){ const h=$('#x-sug'); h.innerHTML=''; list.forEach(k=>{ const kk=LEXN[norm(k)]; if(!kk) return; const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=kk; b.addEventListener('click',()=>openWord(kk,false)); h.appendChild(b); }); }
xSug(X_EX);
$('#x-input').addEventListener('input',e=>{ const q=e.target.value; const k=LEXN[norm(q)]; if(k) renderWord(k); else if(!q.trim()) xSug(X_EX); else { const s=sugg(q,10); xSug(s); $('#x-out').innerHTML=`<p class="note" style="margin:0">«${esc(q.trim())}» нет в словаре: в нём слова, которые встречаются в русских переводах не меньше 10 раз.${s.length?' Выберите подсказку выше.':''}</p>`; const b=$('#c-xbooks'); RB.delete(b); b.innerHTML=''; $('#x-t2').textContent='Где встречается'; } });
function openWord(k, scroll){ $('#x-input').value=k; renderWord(k); if(scroll) document.getElementById('poisk').scrollIntoView({behavior:'auto'}); }
function renderWord(k, hl){ const L=LEX[k]; if(!L) return; const [tot,per,sg,bk,ex]=L; const PT=D.per_tokens; const ST=D.sign_tokens;
  const rates=per.map((n,j)=>10000*n/PT[j]); const sr=['Гари','Ажар','Шатан Богат'].map((s,j)=>[s,10000*sg[j]/ST[s]]);
  const nb=bk.length/2;
  $('#x-out').innerHTML=`<div class="big">${esc(k)}</div><p class="count">${pn(tot,['раз','раза','раз'])} в ${nb} ${plural(nb,['книге','книгах'])} из ${RU_OWN.length}</p>
    <div class="chart" id="c-xper"></div>
    <div class="mini" style="margin-top:8px">${sr.map(([s,r])=>`<span>${s}: ${fmt1(r)} на 10 000</span><span class="bars"><i style="width:${Math.min(100,100*r/Math.max(...sr.map(x=>x[1]),1e-9))}%;background:${sc(Object.keys(SIGN).find(x=>SIGN[x].includes(s.split(' ')[0])))}"></i></span>`).join('')}</div>
    ${ex?`<blockquote>${esc(ex[0])}<cite>${esc(T(A[ex[1]]))}</cite></blockquote>`:''}`;
  vbars($('#c-xper'), rates.map((v,j)=>({l:PER[j],v,tip:`${PER[j]}: ${fmt1(v)} на 10 000 (${pnr(per[j],['раз','раза','раз'])})`})), {h:150, fmtv:fmt1});
  const rows=[]; for(let i=0;i<bk.length;i+=2) rows.push({l:`${TS(A[bk[i]],22)} · ${A[bk[i]].year||''}`,v:bk[i+1],c:sc(A[bk[i]].sign),i:bk[i]});
  $('#x-t2').textContent=`Где встречается «${k}»`;
  hbars($('#c-xbooks'), rows.slice(0,18), {labelW:190, rowH:21, onClick:r=>selectBook(r.i,true), fmtv:fmt});
  if(hl!==false){ setHL(k); $('#hl-input').value=k; } }
renderWord(LEX['слон']?'слон':Object.keys(LEX)[0], false);

$('#eras').innerHTML=D.eras.map(e=>{ const mx=Math.max(...e.top.map(t=>t[1])); return `<div class="era"><div class="h"><b>${e.p}</b><span>${e.books} кн. · ${esc(e.note)}</span></div><ul class="wl">${
  e.top.slice(0,14).map(([w,z,n,nb])=>`<li><button type="button" data-w="${esc(w)}" data-tip="${esc(w)}: ${pnr(n,['раз','раза','раз'])}, в ${nb} ${plural(nb,['книге','книгах'])} периода">${esc(w)} <span class="muted">(${nb})</span></button><span class="bar" style="width:${Math.round(84*z/mx)}px"></span></li>`).join('')}</ul></div>`; }).join('');
$('#eras').querySelectorAll('button[data-w]').forEach(b=>b.addEventListener('click',()=>{ const k=LEXN[norm(b.dataset.w)]; if(k) openWord(k,true); }));

const FN=D.fields.names; let flMode='per', flDrill=FN.indexOf('Звери');
function drawFields(){ const cols = flMode==='per'?PER:['Гари','Ажар','Шатан Богат'];
  const M = FN.map(f=> flMode==='per'? D.fields.per.map(r=>r[f]) : cols.map(c=>D.fields.sign[c][f]));
  heatTable($('#c-fields'), FN, cols, M, {labelW:170, cellH:27, active:flDrill, onRow:i=>{ flDrill=i; drawFields(); thPick(i,true); },
    tipf:(i,j)=>`${esc(FN[i])} · ${esc(cols[j])}: ${fmt2(M[i][j])} на 1000 слов`, fmtv:fmt1}); }
seg($('#fl-mode'), [['per','по периодам'],['sign','по подписям']], 'per', v=>{ flMode=v; drawFields(); });
drawFields();
(()=>{ const P=D.fields.per; const prev=f=>P.slice(0,NPER-1).reduce((a,r)=>a+r[f],0)/(NPER-1);
  const rel=FN.map(f=>[f,P[NPER-1][f]/Math.max(prev(f),1e-9)]).sort((a,b)=>b[1]-a[1]); const up=rel.slice(0,2), dn=rel.slice(-2).reverse();
  const zi=P.map(r=>r['Звери']);
  $('#f-temy').textContent=`В поздних книгах (1970–1980) чаще, чем в среднем раньше, звучат темы «${up[0][0]}» (×${fmt1(up[0][1])}) и «${up[1][0]}» (×${fmt1(up[1][1])}); реже — «${dn[0][0]}» (×${fmt1(dn[0][1])}) и «${dn[1][0]}» (×${fmt1(dn[1][1])}). Тема «Звери» громче всего звучит в ${PER[zi.indexOf(Math.max(...zi))]}, больше всего — в книге ${TQ(A[D.fields.lead['Звери'][0]])}.`; })();
hbars($('#c-aw'), D.ajar_words.slice(0,20).map(([w,z,a,b])=>({l:w,v:z,c:'var(--s2)',tip:`${esc(w)}: у Ажара ${a}, у Гари ${b}`,w})), {labelW:120, rowH:21, onClick:r=>{ const k=LEXN[norm(r.w)]; if(k) openWord(k,true); }});
hbars($('#c-gw'), D.gary_words.slice(0,20).map(([w,z,a,b])=>({l:w,v:z,c:'var(--s1)',tip:`${esc(w)}: у Гари ${a}, у Ажара ${b}`,w})), {labelW:120, rowH:21, onClick:r=>{ const k=LEXN[norm(r.w)]; if(k) openWord(k,true); }});

/* ================= IV. голоса ================= */
const FRB = V.fr.books; const BKC={Promesse:'var(--s1)',Racines:'var(--g6)',Vie:'var(--s2)',Colombe:'var(--c4)'};
const BKN={Promesse:'«Обещание на рассвете» (Гари, 1960)',Racines:'«Корни неба» (Гари, 1956)',Vie:'«Жизнь впереди» (Ажар, 1975)',Colombe:'«Человек с голубкой» (Синибальди, 1958)'};
const BKS={Promesse:'Обещание',Racines:'Корни неба',Vie:'Жизнь впереди',Colombe:'Человек с голубкой'};
const VNAME={differs:'отличается сильнее, чем романы Гари друг от друга',within:'в пределах разброса самого Гари',border:'на границе',unstable:'в пределах разброса или на границе — зависит от числа частых слов'};
legendTo($('#lg-map'), Object.keys(BKN).map(k=>[BKN[k],BKC[k]]));
chart(()=>{ const box=$('#c-map'); const pts=F200.map; const h=Math.min(440,Math.max(300,box.clientWidth*.62)); const [s,w]=svg(box,h); const P=26;
  const xs=pts.map(p=>p[2]), ys=pts.map(p=>p[3]); const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const sx=x=>P+(w-2*P)*(x-x0)/(x1-x0||1), sy=y=>h-P-(h-2*P)*(y-y0)/(y1-y0||1);
  el('line',{x1:P,x2:w-P,y1:sy(0),y2:sy(0),stroke:css('--grid')},s); el('line',{x1:sx(0),x2:sx(0),y1:P,y2:h-P,stroke:css('--grid')},s);
  pts.forEach(([b,j,x,y,nb])=>{ el('circle',{cx:sx(x),cy:sy(y),r:b==='Colombe'?7:5.5,fill:BKC[b],stroke:css('--surface'),'stroke-width':1.5,opacity:.9,
    'data-tip':`${esc(BKN[b])}<br>кусок ${j+1}<br>ближайшая чужая книга: ${esc(BKS[nb])}`},s); });
  const cen={}; pts.forEach(([b,,x,y])=>{ (cen[b]=cen[b]||[]).push([x,y]); });
  Object.entries(cen).forEach(([b,L])=>{ const cx=L.reduce((a,p)=>a+p[0],0)/L.length, cy=L.reduce((a,p)=>a+p[1],0)/L.length;
    txt(s,sx(cx),sy(cy)-12,BKS[b],{'text-anchor':'middle',style:'fill:var(--ink);font-size:12.5px;font-weight:600;paint-order:stroke;stroke:var(--surface);stroke-width:4px'}); });
}, $('#c-map'));
(()=>{ const near={}; F200.map.forEach(([b,,,,nb])=>{ near[b]=near[b]||{}; near[b][nb]=(near[b][nb]||0)+1; });
  const vie=near.Vie||{}; const col=near.Colombe||{};
  $('#n-map').textContent=`Оси — два главных направления различий (${Math.round(100*F200.ev[0])}% и ${Math.round(100*F200.ev[1])}% разброса). Для каждого куска найдена ближайшая чужая книга: для кусков «Жизни впереди» это ${Object.entries(vie).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`«${BKS[k]}» (${n})`).join(', ')}; для кусков «Человека с голубкой» — ${Object.entries(col).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`«${BKS[k]}» (${n})`).join(', ')}.`; })();
let gvVar='narr', gvN='200';
function drawGdist(){ const R=VF[gvVar].by_mfw[gvN]; const M=R.M; const base=R.base[0];
  const rows=[{l:'Корни неба ↔ Обещание (Гари ↔ Гари)',v:base,c:'var(--s1)'},
    {l:'Человек с голубкой ↔ романы Гари',v:R.sini_gary,c:'var(--c4)'},{l:'Жизнь впереди ↔ романы Гари',v:R.ajar_gary,c:'var(--s2)'},
    {l:'внутри «Обещания» (кусок ↔ кусок)',v:M['Promesse|Promesse'],c:'var(--neutral-bar)'},{l:'внутри «Жизни впереди»',v:M['Vie|Vie'],c:'var(--neutral-bar)'}];
  chart(()=>{ const box=$('#c-gdist'); const rowH=30, labelW=Math.min(300,box.clientWidth*.45); const h=rows.length*rowH+28; const [s,w]=svg(box,h);
    const lo=Math.min(...rows.map(r=>r.v))*.85, hi=Math.max(...rows.map(r=>r.v))*1.05; const sx=v=>labelW+(w-labelW-50)*(v-lo)/(hi-lo);
    rows.forEach((r,i)=>{ const y=i*rowH+6; txt(s,labelW-8,y+14,r.l,{'text-anchor':'end',style:'font-family:var(--f-body);font-size:13.5px;fill:var(--ink)'});
      el('rect',{x:labelW,y,width:Math.max(1,sx(r.v)-labelW),height:rowH-10,rx:3,fill:r.c,'data-tip':`${esc(r.l)}: ${fmt2(r.v)}`},s); txt(s,sx(r.v)+6,y+14,fmt2(r.v)); });
    const xb=sx(base); el('line',{x1:xb,x2:xb,y1:0,y2:h-18,stroke:css('--ink'),'stroke-dasharray':'4 3'},s);
    const xm=sx(base*V.rule.margin); el('line',{x1:xm,x2:xm,y1:0,y2:h-18,stroke:css('--muted'),'stroke-dasharray':'1 3'},s);
    txt(s,xb,h-4,'Гари ↔ Гари',{'text-anchor':'middle',style:'fill:var(--ink-2);font-size:10.5px'}); txt(s,xm+2,h-4,'+10%',{style:'fill:var(--muted);font-size:10.5px'});
  }, $('#c-gdist'));
  $('#n-gdist').textContent=`Правило задано до подсчёта: дальше, чем два романа Гари друг от друга, плюс 10% запаса — «отличается»; не дальше них — «в пределах разброса Гари». В этом варианте: Ажар — ${VNAME[R.v_ajar]}, Синибальди — ${VNAME[R.v_sini]}. Итог по трём наборам частых слов: Ажар — ${VNAME[VF[gvVar].v_ajar]}, Синибальди — ${VNAME[VF[gvVar].v_sini]}.`; }
seg($('#gv-var'), [['narr','повествование'],['narr_nopron','без местоимений'],['all','с диалогами']], 'narr', v=>{ gvVar=v; drawGdist(); });
seg($('#gv-mfw'), [['100','100'],['200','200'],['300','300']], '200', v=>{ gvN=v; drawGdist(); });
drawGdist();
$('#f-golosa').textContent=`Ажар стоит отдельно: «Жизнь впереди» отстоит от романов Гари на ${fmt2(F200.ajar_gary)}, а романы Гари друг от друга — на ${fmt2(F200.base[0])}. Разница держится без местоимений (${fmt2(VF.narr_nopron.by_mfw['200'].ajar_gary)} против ${fmt2(VF.narr_nopron.by_mfw['200'].base[0])}), то есть дело не только в рассказе от первого лица. Синибальди от Гари не отличить: ${fmt2(F200.sini_gary)}.`;

/* русские переводы: шум, Ажар, Мавлевич */
const RS=V.ru.summary.narr['200'];
function strip(box, groups){ return chart(()=>{ const rowH=34, labelW=Math.min(290,box.clientWidth*.44); const h=groups.length*rowH+26; const [s,w]=svg(box,h);
  const all=groups.flatMap(g=>g.v); const lo=Math.min(...all)*.95, hi=Math.max(...all)*1.03; const sx=v=>labelW+(w-labelW-16)*(v-lo)/(hi-lo);
  const ax=el('g',{class:'ax'},s); for(let k=0;k<=4;k++){ const v=lo+(hi-lo)*k/4; el('line',{x1:sx(v),x2:sx(v),y1:0,y2:h-20,stroke:css('--grid')},ax); txt(ax,sx(v),h-5,fmt2(v),{'text-anchor':'middle'}); }
  groups.forEach((g,i)=>{ const y=i*rowH+rowH/2; txt(s,labelW-8,y+4,g.l,{'text-anchor':'end',style:'font-family:var(--f-body);font-size:13.5px;fill:var(--ink)'});
    g.v.forEach((v,j)=>el('circle',{cx:sx(v),cy:y+((j*7)%9-4),r:4.5,fill:g.c,opacity:.8,'data-tip':`${esc(g.l)}: ${fmt2(v)}${g.t?'<br>'+esc(g.t[j]):''}`},s));
    if(g.v.length>2){ const m=[...g.v].sort((a,b)=>a-b)[Math.floor(g.v.length/2)]; el('line',{x1:sx(m),x2:sx(m),y1:y-11,y2:y+11,stroke:css('--ink'),'stroke-width':2},s); } });
}, box); }
(()=>{ const RN=V.ru.variants.narr['200']; const I={}; RN.names.forEach((b,i)=>I[b]=i); const d=(a,b)=>RN.M[I[a]][I[b]]; const meta=V.ru.meta;
  const tt=b=>RU_T[meta[b].work]||meta[b].work;
  const pairsOf=(A_,B_,same)=>{ const v=[],t=[]; A_.forEach((a,i)=>(same?A_.slice(i+1):B_).forEach(b=>{ if(a!==b){ v.push(d(a,b)); t.push(`${tt(a)} ↔ ${tt(b)}`); } })); return [v,t]; };
  const late=RS.late_books, ajar=RS.ajar_books, bog=RN.names.filter(b=>meta[b].sign==='Shatan Bogat');
  const [gv,gt]=pairsOf(late,late,true), [av,at]=pairsOf(ajar,late), [aav,aat]=pairsOf(ajar,ajar,true), [bv,bt]=pairsOf(bog,late);
  const mg=RS.mav.gary, ma=RS.mav.ajar; const [mgv,mgt]=pairsOf(mg,mg,true), [mav,mat]=pairsOf(ma,mg);
  strip($('#c-shum'), [
    {l:'Два перевода одной книги',v:RS.twins.map(x=>x[2]),t:RS.twins.map(x=>tt(x[0])),c:'var(--neutral-bar)'},
    {l:'Поздний Гари ↔ поздний Гари',v:gv,t:gt,c:'var(--s1)'},{l:'Шатан Богат ↔ поздний Гари',v:bv,t:bt,c:'var(--c3)'},
    {l:'Ажар ↔ поздний Гари',v:av,t:at,c:'var(--s2)'},{l:'Ажар ↔ Ажар',v:aav,t:aat,c:'var(--s2)'},
    {l:'Мавлевич: Гари ↔ Гари',v:mgv.filter(x=>x),t:mgt,c:'var(--g6)'},{l:'Мавлевич: Ажар ↔ Гари',v:mav,t:mat,c:'var(--g8)'}]);
  $('#n-shum').textContent=`Черта — медиана группы. Два перевода одной книги расходятся на ${fmt2(RS.noise.min)}–${fmt2(RS.noise.max)}: это шум перевода. Книги позднего Гари между собой — ${fmt2(RS.gg_late.min)}–${fmt2(RS.gg_late.max)}, Ажар от позднего Гари — ${fmt2(RS.ajar_late.min)}–${fmt2(RS.ajar_late.max)}. У одной переводчицы, Натальи Мавлевич, «Голубчик» отстоит от её переводов Гари на ${fmt2(RS.mav.ga.min)}–${fmt2(RS.mav.ga.max)}, а её переводы Гари друг от друга — на ${fmt2(RS.mav.gg.min)}–${fmt2(RS.mav.gg.max)}: диапазоны ${RS.mav.ga.max<=RS.mav.gg.max?'перекрываются':'почти не перекрываются'}. Это одна книга Ажара и ${pnr(RS.mav.gary.length,['книга','книги','книг'])} Гари — мало для вывода.`;
  const mavIn = RS.mav.ga.max<=RS.mav.gg.max;
  const TC=V.translation_check; const TCv=Object.values(TC); const same=TCv.filter(x=>x.same_order).length; const pass=same===TCv.length;
  const nearOk=TCv.every(x=>x.ru && x.fr.indexOf(Math.min(...x.fr))===0 && x.ru.indexOf(Math.min(...x.ru))===0);
  const RV={narr:V.ru.summary.narr.v_ajar, nopron:V.ru.summary.narr_nopron.v_ajar};
  const gap=Math.min(...TCv.map(x=>Math.abs(x.ru[1]-x.ru[2])));
  $('#f-shum').textContent = pass
    ? `По-русски Ажар отстоит от позднего Гари в среднем на ${fmt2(RS.ajar_late.med)}, а книги позднего Гари между собой расходятся до ${fmt2(RS.gg_late.max)}: по тому же правилу, что и для оригиналов, это «${VNAME[RV.narr]}» (без местоимений — «${VNAME[RV.nopron]}»). Два перевода одной книги расходятся меньше (${fmt2(RS.noise.med)}), так что Ажар дальше от Гари, чем шум перевода, но не дальше, чем поздний Гари от самого себя.`
    : `По-русски Ажар в среднем дальше от позднего Гари (${fmt2(RS.ajar_late.med)}), чем два перевода одной книги друг от друга (${fmt2(RS.noise.med)}). ${mavIn?'Но у одного и того же переводчика «Голубчик» не выходит за разброс между книгами Гари. ':''}По русским текстам голос Ажара нельзя отделить от голоса его переводчиков — ответ на вопрос о голосе дают только оригиналы.`;
  $('#w-check').innerHTML = pass
    ? `<b>Проверка перевода пройдена.</b> Три книги есть на обоих языках, и порядок трёх расстояний между ними совпадает во французском и в русском при 100, 200 и 300 частых словах. Поэтому русское сравнение получает вердикт по тому же правилу, что и французское. Проверка хрупкая: две дальние пары по-русски различаются всего на ${fmt2(gap)}, так что русский вердикт слабее французского.`
    : `<b>Проверка перевода.</b> Три книги есть на обоих языках. ${nearOk?'Самая близкая пара — «Обещание» и «Корни неба» — совпадает в обоих языках при любом числе частых слов. Но п':'П'}орядок всех трёх расстояний перевод сохраняет только в ${same} ${plural(same,['варианте','вариантах'])} из ${TCv.length}. По правилу, заданному заранее, по русским переводам вердиктов о голосе не ставится: эта часть описательная, вердикт даёт только сравнение оригиналов.`;
  // переводчик или годы
  const P=RS.pairs; const col=s=>s===true?'var(--s2)':s===false?'var(--s1)':'var(--neutral-bar)';
  legendTo($('#lg-pairs'), [['один переводчик','var(--s2)'],['разные переводчики','var(--s1)'],['переводчик неизвестен','var(--neutral-bar)']]);
  chart(()=>{ const box=$('#c-pairs'); const h=280; const [s,w]=svg(box,h); const L=44,R=12,T0=10,B=28;
    const gx=Math.max(...P.map(p=>p[3])); const ys=P.map(p=>p[2]); const lo=Math.min(...ys)*.97, hi=Math.max(...ys)*1.02;
    const sx=x=>L+(w-L-R)*x/gx, sy=v=>h-B-(h-B-T0)*(v-lo)/(hi-lo); const ax=el('g',{class:'ax'},s);
    for(let k=0;k<=4;k++){ const v=lo+(hi-lo)*k/4; el('line',{x1:L,x2:w-R,y1:sy(v),y2:sy(v),stroke:css('--grid')},ax); txt(ax,L-6,sy(v)+4,fmt2(v),{'text-anchor':'end'}); }
    for(let x=0;x<=gx;x+=10) txt(ax,sx(x),h-8,x+' лет',{'text-anchor':'middle'});
    P.forEach(p=>el('circle',{cx:sx(p[3]),cy:sy(p[2]),r:p[4]===true?5.5:3.6,fill:col(p[4]),opacity:p[4]===true?.95:.55,'data-tip':`${esc(tt(p[0]))} ↔ ${esc(tt(p[1]))}<br>${pnr(p[3],['год','года','лет'])}, дельта ${fmt2(p[2])}`},s));
  }, $('#c-pairs'));
  const grp=f=>{ const v=P.filter(f).map(p=>p[2]); return {n:v.length, m:v.reduce((a,b)=>a+b,0)/Math.max(1,v.length)}; };
  const sameT=grp(p=>p[4]===true), diffT=grp(p=>p[4]===false), unk=grp(p=>p[4]===null); const near=grp(p=>p[3]<=5&&p[4]!==true), far=grp(p=>p[3]>=20&&p[4]!==true);
  $('#n-pairs').textContent=`Пар книг одного переводчика в корпусе ${sameT.n}${sameT.n<3?' — слишком мало, чтобы сравнивать переводчиков между собой':`: в среднем ${fmt2(sameT.m)} против ${fmt2(diffT.m)} у разных`}; у ${unk.n} ${plural(unk.n,['пары','пар'])} переводчик хотя бы одной книги неизвестен. Время заметно сильнее: книги, написанные с разницей до пяти лет, в среднем на ${fmt2(near.m)} (${pnr(near.n,['пара','пары','пар'])}), с разницей от двадцати лет — на ${fmt2(far.m)} (${pnr(far.n,['пара','пары','пар'])}).`; })();

/* «Ночь будет спокойной» */
(()=>{ const N=V.night; const g=N.gary, b=N.bondy; const tot=g.words+b.words;
  $('#noch-vs').innerHTML=[[`${Math.round(100*b.words/tot)}%`,'слов книги — вопросы Бонди',`${pn(b.paras,['реплика','реплики','реплик'])}, типичная — ${pn(b.len_med,['слово','слова','слов'],1)}`,'var(--c3)'],
    [`${Math.round(100*g.words/tot)}%`,'слов — ответы Гари',`${pn(g.paras,['реплика','реплики','реплик'])}, типичная — ${pn(g.len_med,['слово','слова','слов'],1)}, самая длинная — ${fmt(g.len_max)}`,'var(--s1)'],
    [`${fmt1(1000*b.ty/b.words)} и ${fmt1(1000*g.ty/g.words)}`,'«ты» на 1000 слов: у Бонди и у Гари','вопросы обращены к собеседнику, ответы — к читателю','var(--ink)'],
    [`${fmt1(1000*g.ya/g.words)} и ${fmt1(1000*b.ya/b.words)}`,'«я» на 1000 слов: у Гари и у Бонди','книга о себе — в ответах, а не в вопросах','var(--ink)']]
    .map(([n,h,s,c])=>`<div class="box"><h3>${h}</h3><div class="big" style="color:${c}">${n}</div><div class="sub">${s}</div></div>`).join('');
  $('#f-noch').textContent=`Разговор вдвоём здесь только по форме: Бонди принадлежит ${Math.round(100*b.words/tot)}% слов, его типичная реплика — ${pn(b.len_med,['слово','слова','слов'],1)}, типичный ответ Гари — ${fmt1(g.len_med)}. Кто писал вопросы, по частым словам не проверить: вопрос и ответ — разные жанры речи, и расстояние между ними покажет разницу жанров, а не авторов.`;
  chart(()=>{ const box=$('#c-noch'); const S=N.seq; const h=96; const [s,w]=svg(box,h); const L=58,R=4; const tot=S.reduce((a,x)=>a+x[0],0); const sx=v=>L+(w-L-R)*v/tot;
    const lanes=[['Бонди',1,10,'var(--c3)'],['Гари',0,46,'var(--s1)']]; lanes.forEach(([n,k,y])=>txt(s,L-8,y+14,n,{'text-anchor':'end',style:'font-family:var(--f-mono);font-size:11.5px;fill:var(--ink-2)'}));
    let acc=0; S.forEach(([n,k])=>{ const [,,y,c]=lanes[k?0:1]; el('rect',{x:sx(acc),y,width:Math.max(.6,sx(acc+n)-sx(acc)-.3),height:22,fill:c,'data-tip':`${k?'Бонди':'Гари'}: ${pnr(n,['слово','слова','слов'])}`},s); acc+=n; });
    const ax=el('g',{class:'ax'},s); txt(ax,L,h-6,'начало книги'); txt(ax,w-R,h-6,'конец',{'text-anchor':'end'});
  }, $('#c-noch'));
  $('#noch-q').innerHTML=N.examples_q.map(q=>`<p><span class="who">Бонди</span>${esc(q)}</p>`).join(''); })();

/* устная речь */
(()=>{ const PJ=V.fr.projection; const SETS=[['oral','вся устная речь'],['propos','«Propos et confidences», 1980'],['radioscopie','«Радиоскопия», 1975'],['sens','«Le Sens de ma vie» (книга)']];
  const BK=['Promesse','Vie','Racines','Colombe']; let pv='narr';
  function draw(){ const rows=SETS.filter(([k])=>PJ[pv][k]); const M=rows.map(([k])=>BK.map(b=>PJ[pv][k].to_book[b]));
    heatTable($('#c-ustno'), rows.map(r=>r[1]), BK.map(b=>BKS[b]), M, {labelW:230, cellH:30, fmtv:fmt2,
      colorf:(v,i)=>{ const r=M[i]; const mn=Math.min(...r), mx=Math.max(...r); return mixc(css('--heat-hi'),css('--heat-lo'),Math.sqrt((v-mn)/Math.max(mx-mn,1e-9))); },
      tipf:(i,j)=>`${esc(rows[i][1])} → ${esc(BKS[BK[j]])}: ${fmt2(M[i][j])}`}); }
  seg($('#us-var'), [['narr','все частые слова'],['narr_nopron','без местоимений']], 'narr', v=>{ pv=v; draw(); });
  draw();
  const o=PJ.narr.oral.to_book, p=PJ.narr.propos.to_book, r=PJ.narr.radioscopie.to_book;
  const second=t=>Math.min(...Object.entries(t).filter(([k])=>k!=='Promesse').map(([,v])=>v));
  $('#f-ustno').textContent=`Вслух Гари говорит ближе всего к «Обещанию на рассвете»: так во всех вариантах — вся устная речь, отдельно каждая передача, с местоимениями и без. Чище всего это видно в «Propos et confidences», где говорит почти один Гари: ${fmt2(p.Promesse)} против ${fmt2(second(p))} до следующей книги. В «Радиоскопии» отрыв меньше (${fmt2(r.Promesse)} против ${fmt2(second(r))}): там в субтитрах есть и голос ведущего.`; })();

/* ================= V. мир Гари ================= */
function listLinks(title){ const k=LEXN[norm(title)]; const inNet=EX.net.nodes.some(n=>n.name===title);
  return (k||inNet)?`<p class="chips" style="margin-top:14px">${k?`<button type="button" class="btn" data-open="${esc(k)}">Открыть в словоискателе →</button>`:''}${inNet?`<button type="button" class="btn" data-net="${esc(title)}">Карточка в «Круге Гари» →</button>`:''}</p>`:''; }
function listCard(host, title, sub, books, ex){ const mx=Math.max(...books.map(x=>x[1]),1);
  host.innerHTML=`<div class="eyebrow">${esc(sub)}</div><div class="ttl">${esc(title)}</div><ul class="sh-list" style="margin-top:10px">${
    books.map(([b,n])=>`<li><button type="button" data-b="${b}" title="${esc(T(A[b]))}">${esc(T(A[b]))} <span class="muted">${A[b].year||''}</span></button><span class="b"><i style="width:${Math.max(3,Math.round(100*n/mx))}%;background:${sc(A[b].sign)}"></i></span><span class="n">${fmt(n)}</span></li>`).join('')}</ul>
    ${ex?`<h4>Пример</h4><blockquote>${esc(ex[0])}<cite>${esc(T(A[ex[1]]))}</cite></blockquote>`:''}${listLinks(title)}`;
  host.querySelectorAll('button[data-open]').forEach(x=>x.addEventListener('click',()=>openWord(x.dataset.open,true)));
  host.querySelectorAll('button[data-net]').forEach(x=>x.addEventListener('click',()=>{ ntSelectByName(x.dataset.net); goTo('krug'); }));
  host.querySelectorAll('button[data-b]').forEach(x=>x.addEventListener('click',()=>selectBook(+x.dataset.b,true))); }
(()=>{ const P=D.pantheon; hbars($('#c-panteon'), P.slice(0,30).map(r=>({l:r[0],v:r[1],r,tip:`${esc(r[0])}: ${pnr(r[1],['книга','книги','книг'])}, ${pnr(r[2],['упоминание','упоминания','упоминаний'])}`})), {labelW:140, rowH:21, fmtv:fmt, onClick:x=>listCard($('#pn-card'),x.r[0],`${pnr(x.r[1],['книга','книги','книг'])} · ${pnr(x.r[2],['упоминание','упоминания','упоминаний'])}`,x.r[3])});
  listCard($('#pn-card'),P[0][0],`${pnr(P[0][1],['книга','книги','книг'])} · ${pnr(P[0][2],['упоминание','упоминания','упоминаний'])}`,P[0][3]);
  $('#f-panteon').textContent=`Чаще всех реальных людей у Гари появляются ${P.slice(0,5).map(r=>`${r[0]} (${pnr(r[1],['книга','книги','книг'])})`).join(', ')}. Диктаторы и святые, писатели и художники стоят в одном списке: ${P.slice(5,12).map(r=>r[0]).join(', ')}.`; })();
(()=>{ const P=D.places; hbars($('#c-mesta'), P.slice(0,30).map(r=>({l:r[0],v:r[1],r,tip:`${esc(r[0])}: ${pnr(r[1],['книга','книги','книг'])}, ${pnr(r[2],['упоминание','упоминания','упоминаний'])}`})), {labelW:130, rowH:21, fmtv:fmt, onClick:x=>listCard($('#ms-card'),x.r[0],`${pnr(x.r[1],['книга','книги','книг'])} · ${pnr(x.r[2],['упоминание','упоминания','упоминаний'])}`,x.r[3])});
  listCard($('#ms-card'),P[0][0],`${pnr(P[0][1],['книга','книги','книг'])} · ${pnr(P[0][2],['упоминание','упоминания','упоминаний'])}`,P[0][3]);
  $('#f-mesta').textContent=`${P[0][0]} и ${P[1][0]} названы в ${P[0][1]} и ${P[1][1]} ${plural(P[1][1],['книге','книгах'])} из ${RU_OWN.length}, но мир Гари шире Европы: Африка — в ${pnr((P.find(r=>r[0]==='Африка')||[0,0])[1],['книге','книгах'])}, Америка — в ${(P.find(r=>r[0]==='Америка')||[0,0])[1]}, Россия — в ${(P.find(r=>r[0]==='Россия')||[0,0])[1]}.`; })();
const SHV=D.shelves;
(()=>{ const Z=SHV['Звери']; hbars($('#c-zveri'), Z.slice(0,24).map(r=>({l:r[0],v:r[2],r,tip:`${esc(r[0])}: ${pnr(r[2],['раз','раза','раз'])} в ${r[1]} ${plural(r[1],['книге','книгах'])}`})), {labelW:110, rowH:21, fmtv:fmt, onClick:x=>listCard($('#zv-card'),x.r[0],`${pnr(x.r[2],['раз','раза','раз'])} · ${pnr(x.r[1],['книга','книги','книг'])}`,x.r[3],x.r[4])});
  listCard($('#zv-card'),Z[0][0],`${pnr(Z[0][2],['раз','раза','раз'])} · ${pnr(Z[0][1],['книга','книги','книг'])}`,Z[0][3],Z[0][4]);
  const dog=Z.find(r=>r[0]==='собака'), boa=Z.find(r=>r[0]==='удав');
  const inBook=(r,f)=>r[3].filter(([b])=>f(A[b])).reduce((a,[,n])=>a+n,0);
  const slR=inBook(Z[0],a=>a.work==='Les Racines du ciel'), boaA=inBook(boa,a=>a.sign==='Émile Ajar');
  $('#f-zveri').textContent=`Главный зверь Гари — ${Z[0][0]}: ${pnr(Z[0][2],['упоминание','упоминания','упоминаний'])}, из них ${slR} (${Math.round(100*slR/Z[0][2])}%) в «Корнях неба». По числу книг впереди собака — ${pnr(dog[1],['книга','книги','книг'])} из ${RU_OWN.length}, больше всего в «Белой собаке». Удав упомянут ${pnr(boa[2],['раз','раза','раз'])}, ${Math.round(100*boaA/boa[2])}% — у Ажара: это Голубчик из одноимённого романа.`; })();
(()=>{ const host=$('#shelves'); const keys=['Напитки','Транспорт','Оружие']; const cols={Напитки:'var(--g7)',Транспорт:'var(--g2)',Оружие:'var(--g1)'};
  host.innerHTML=keys.map(k=>{ const L=SHV[k]; const mx=Math.max(...L.map(r=>r[2])); return `<div class="sh-group"><div class="sh-h"><i class="sw" style="background:${cols[k]}"></i><b>${k}</b><span class="muted">${fmt(L.reduce((a,r)=>a+r[2],0))}</span></div><ul class="sh-list">${
    L.slice(0,12).map((r,j)=>`<li><button type="button" data-k="${k}" data-j="${j}">${esc(r[0])}</button><span class="b"><i style="width:${Math.round(100*r[2]/mx)}%;background:${cols[k]}"></i></span><span class="n">${r[2]}</span></li>`).join('')}</ul></div>`; }).join('');
  host.querySelectorAll('button[data-k]').forEach(b=>b.addEventListener('click',()=>{ const r=SHV[b.dataset.k][+b.dataset.j]; listCard($('#sh-card'),r[0],`${pnr(r[2],['раз','раза','раз'])} · ${pnr(r[1],['книга','книги','книг'])}`,r[3],r[4]); }));
  const r=SHV['Напитки'][0]; listCard($('#sh-card'),r[0],`${pnr(r[2],['раз','раза','раз'])} · ${pnr(r[1],['книга','книги','книг'])}`,r[3],r[4]); })();

/* ================= VI. оригинал и перевод ================= */
(()=>{ const rows=[['слов','words',fmt],['фраз','sents',fmt],['слов в типичной фразе','sl',fmt1],['% слов в репликах','dlg',fmt1],['«!» на 1000 слов','excl',fmt1],['«?» на 1000 слов','q',fmt1],['«…» на 1000 слов','ell',fmt1],['«я» на 1000 слов','fp',fmt1]];
  $('#t-original').innerHTML=`<table class="cmp"><thead><tr><th></th>${PR.map(p=>`<th>${esc(RU_T[p.work]||p.work)}<br>фр. → рус. (${esc(p.tr)})</th>`).join('')}</tr></thead><tbody>${
    rows.map(([l,k,f])=>`<tr><td>${l}</td>${PR.map(p=>`<td>${f(p[k][0])} → <b>${f(p[k][1])}</b></td>`).join('')}</tr>`).join('')}</tbody></table>`;
  const wr=PR.map(p=>p.words[1]/p.words[0]), sr=PR.map(p=>p.sents[1]/p.sents[0]);
  $('#f-original').textContent=`Русский перевод короче оригинала на ${Math.round(100*(1-Math.max(...wr)))}–${Math.round(100*(1-Math.min(...wr)))}% слов, а фраз в нём столько же (${PR.map(p=>`${fmt(p.sents[0])} → ${fmt(p.sents[1])}`).join('; ')}). Переводчики сохраняют деление на фразы, а слов нужно меньше: в русском нет артиклей, и падежи заменяют предлоги. ${PR.every(p=>p.excl[1]*p.words[1]>=p.excl[0]*p.words[0])?'Восклицательных знаков в переводе больше не только на тысячу слов, но и в штуках':'Восклицательных знаков на тысячу слов в переводе больше, но отчасти потому, что слов меньше'}: ${PR.map(p=>`${Math.round(p.excl[0]*p.words[0]/1000)} → ${Math.round(p.excl[1]*p.words[1]/1000)}`).join(', ')}.`; })();
(()=>{ const TW=D.twins; $('#twins').innerHTML=TW.map((t,i)=>`<div class="panel"><div class="cap"><span class="t">${esc(RU_T[t.work]||t.work)}</span><span class="u">${esc(t.tr[0])} · ${esc(t.tr[1])}</span></div>
  <table class="cmp"><thead><tr><th></th><th>перевод 1: ${esc(t.tr[0])}</th><th>перевод 2: ${esc(t.tr[1])}</th></tr></thead><tbody>
  <tr><td>слов</td><td>${fmt(t.words[0])}</td><td>${fmt(t.words[1])}</td></tr><tr><td>слов в типичной фразе</td><td>${fmt1(t.sl[0])}</td><td>${fmt1(t.sl[1])}</td></tr>
  <tr><td>разных слов на 500</td><td>${t.mattr[0]?Math.round(t.mattr[0]):'—'}</td><td>${t.mattr[1]?Math.round(t.mattr[1]):'—'}</td></tr><tr><td>«!» на 1000 слов</td><td>${fmt1(t.excl[0])}</td><td>${fmt1(t.excl[1])}</td></tr></tbody></table>
  <div class="pair2"><blockquote>${esc(t.first[0])}<cite>перевод 1</cite></blockquote><blockquote>${esc(t.first[1])}<cite>перевод 2</cite></blockquote></div></div>`).join('');
  $('#f-dva').textContent=`Один и тот же текст у двух переводчиков расходится по частым словам на ${fmt2(RS.noise.min)}–${fmt2(RS.noise.max)} (медиана ${fmt2(RS.noise.med)}), а две разные книги позднего Гари — на ${fmt2(RS.gg_late.min)}–${fmt2(RS.gg_late.max)} (медиана ${fmt2(RS.gg_late.med)}). Переводчик меняет частые слова почти так же сильно, как смена книги. Первые фразы ниже показывают, откуда берётся разница.`; })();

/* ================= VII. рекорды, корпус, методика ================= */
(()=>{ const R=D.records; const card=(k,i,d)=>`<div class="rec"><div class="k">${k}</div><div class="v">${esc(T(A[i]))}</div><div class="d">${d}</div></div>`;
  $('#records').innerHTML=[card('Самая большая книга',R.biggest,`${pn(A[R.biggest].words,['слово','слова','слов'])} в переводе`),card('Больше всего диалога',R.most_dialog,`${fmt1(A[R.most_dialog].dlg)}% слов в репликах`),
    card('Меньше всего диалога',R.least_dialog,`${fmt1(A[R.least_dialog].dlg)}% слов в репликах`),card('Больше всего «!»',R.most_excl,`${fmt1(A[R.most_excl].punct['!'])} на 1000 слов`),
    card('Больше всего «?»',R.most_q,`${fmt1(A[R.most_q].punct['?'])} на 1000 слов`),card('Больше всего «я»',R.most_fp,`${fmt1(A[R.most_fp].fp)} на 1000 слов`),
    card('Самая длинная типичная фраза',R.longest_sl,`${pn(A[R.longest_sl].sl_med,['слово','слова','слов'],1)}`),card('Богаче всего словарь',R.richest,`${pnr(Math.round(A[R.richest].mattr),['разное слово','разных слова','разных слов'])} на 500`),card('Самая короткая типичная фраза',R.shortest_sl,`${pn(A[R.shortest_sl].sl_med,['слово','слова','слов'],1)}`)].join('');
  $('#longest-ru').innerHTML=`${esc(R.longest_ru[1])}…<cite>${pnr(R.longest_ru[0],['слово','слова','слов'])} · «${esc(RU_T[R.longest_ru[2]]||R.longest_ru[2])}», русский перевод</cite>`;
  $('#longest-fr').innerHTML=`${esc(R.longest_fr[1])}…<cite>${R.longest_fr[0]} mots · «${esc(R.longest_fr[2])}», оригинал</cite>`; })();
(()=>{ const rows=A.map(a=>[T(a), a.lang==='ru'&&RU_T[a.work]?a.work:'', String(a.year||'—'), SIGN[a.sign]||'', a.lang==='ru'?(a.tr||'нет данных'):'оригинал', fmt(a.words)]);
  $('#t-corpus').innerHTML=`<table><thead><tr><th>Книга</th><th>Оригинал</th><th>Год</th><th>Подпись</th><th>Перевод</th><th>Слов</th></tr></thead><tbody>${rows.map(r=>'<tr>'+r.map(c=>`<td>${esc(c)}</td>`).join('')+'</tr>').join('')}</tbody></table>`; })();
const METHOD=[
 `<b>Корпус.</b> Тексты из папок заказчика (EPUB, fb2, docx, md, субтитры) и из ~/Downloads. Классификация по содержимому, а не по имени файла: в папке с материалами прошлого проекта имена файлов не совпадали с содержимым. Дубли — по совпадению 5-словных цепочек (больше 90% общих — дубль; 65–99% — редакция того же перевода; меньше 10% — независимый перевод). Всего файлов ${Object.values(O.files).reduce((a,b)=>a+b,0)}: в анализ вошли ${(O.files.own||0)+(O.files.self||0)+(O.files.oral||0)+(O.files.twin||0)}, дублей ${O.files.dup||0}, нетекстовых (pdf, mp3, zip) ${O.files.nontext||0}. Исключены, но посчитаны: биография М. Анисимов, сборник статей о Гари, психологические профили, промпты, текст «Клуб последних жён».`,
 `<b>Годы.</b> Год первой публикации по библиографии французской Википедии (статьи «Romain Gary» и «Gloire à nos illustres pionniers»). «Вино мертвецов» написано в 1937 году и отнесено к нему, хотя издано в 2014-м. Для двух рассказов («Я ем ботинок», «Письмо к моей соседке по столу») оригинал установить не удалось — они без даты. Хронология событий — из фактологического профиля заказчика.`,
 `<b>Переводчики.</b> Из выходных данных внутри книг и из метаданных fb2 (текст сверен: 100% общих цепочек). Для «Голубчика» (Н. Мавлевич), «Псевдо» (А. Беляк) и «Страхов царя Соломона» (Л. Лунгина) — из каталогов изданий, в файлах переводчик не указан.`,
 `<b>Очистка.</b> Срезаны аннотации, выходные данные, оглавления, сноски трёх форматов, чужие предисловия (Ф. Брено в «Вине мертвецов», Р. Гренье в «Le Sens de ma vie», примечание издателя в «Человеке с голубкой»), авторское предисловие 1980 года к французским «Корням неба». Абзац длиной до 8 слов без знака в конце считается заголовком.`,
 `<b>Диалог.</b> Абзац-реплика — абзац, который начинается с тире или кавычки и короче ${120} слов. Более длинный абзац с тире или кавычкой — это рассказ героя (в «Корнях неба» такие монологи идут десятками абзацев, и во французском издании каждый открывается кавычкой), он считается повествованием. Доля диалога — доля слов в абзацах-репликах. Это верхняя оценка: в некоторых изданиях реплика и авторский текст после неё стоят в одном абзаце.`,
 `<b>Слова.</b> Русские слова приводятся к начальной форме программой pymorphy3 (первый разбор, без снятия омонимии: «есть» — быть и кушать — не различаются), французские — spaCy fr_core_news_sm (модель ошибается: «Madame» получает начальную форму «monsieur»). Имя — слово с пометой имени, фамилии или топонима, слово вне словаря с заглавной буквы или слово, которое в ≥ 70% случаев пишется с заглавной.`,
 `<b>Фраза.</b> Граница фразы — точка, «!», «?» или многоточие, после которых идёт заглавная буква, тире или кавычка. Инициалы («Ф. Б.») дают лишние границы. Типичная фраза — медиана.`,
 `<b>Разных слов на 500.</b> Текст режется на отрезки по 500 слов, в каждом считаются разные словоформы, результат усредняется.`,
 `<b>Слова эпох и словарь Ажара.</b> Сила отличия — логарифм отношения шансов с информативным априорным распределением (Monroe, Colaresi, Quinn, 2008). Слово эпохи должно встречаться ≥ 10 раз и хотя бы в двух книгах периода. Периоды: 1937–1949, 1952–1962, 1963–1969, 1970–1980 — по вехам биографии.`,
 `<b>Темы.</b> 16 тем по 12–20 слов, списки слов приведены в разделе «Темы» (нажмите на тему). Частота — на 1000 слов периода.`,
 `<b>Голоса.</b> Дельта Барроуза по ${V.rule.mfw.join(', ')} самым частым словоформам. Куски по 3000 слов (французский) и 5000 слов (русский) только из повествования, без имён собственных. Частые слова и средние для z-оценок берутся из равного числа кусков каждой книги. Расстояние книга ↔ книга — среднее по всем парам кусков. Правило вердикта записано до подсчёта: дальше максимума расстояний между книгами Гари больше чем на 10% — «отличается», не дальше максимума — «в пределах разброса», между — «на границе»; вердикт ставится, если он одинаков при 100, 200 и 300 словах. Французская и русская шкалы не смешиваются. Оговорка: у Ажара во французском корпусе одна книга, у Гари две; французские «Корни неба» — окончательная редакция 1980 года, «Человек с голубкой» — редакция 1984 года, редакция французского «Обещания» в файле не указана. Поздние авторские правки могут сближать тексты Гари с Ажаром 1975 года.`,
 `<b>Проверка перевода.</b> Для трёх книг, которые есть на двух языках, сравнивается порядок трёх попарных расстояний во французском и в русском. Правило задано заранее: русское сравнение получает вердикт, только если порядок совпадает при 100, 200 и 300 словах. ${Object.values(V.translation_check).every(x=>x.same_order)?'Сейчас совпадает, но отрыв между двумя дальними парами мал — вердикт по переводам слабее вердикта по оригиналам. До исправления правила диалога (длинные монологи в «Корнях неба» считались репликами) проверка не проходила.':'Сейчас не совпадает, поэтому по русским переводам вердиктов о голосе нет.'}`,
 `<b>«Ночь будет спокойной».</b> Реплики размечены в тексте («Франсуа Бонди.», «Ф. Б.», «Р. Г.»); абзац без метки считается продолжением прежнего говорящего. Вопросы и ответы сравниваются только описательно.`,
 `<b>Устная речь.</b> Автоматические субтитры (две передачи, 1975 и 1980) без пунктуации и с ошибками распознавания; говорящие в них не разделены, поэтому в «Радиоскопии» есть и реплики Жака Шанселя и ведущего архивного выпуска. Используются только частые слова; расстояние считается в системе французской карты голосов, отдельно по каждой передаче, с местоимениями и без. Вердикт: «Обещание» ближе всех во всех вариантах и отрыв от следующей книги не меньше 5% — «подтверждается»; ближе всех, но отрыв где-то меньше — «отчасти».`,
 `<b>Мир Гари.</b> Рейтинги по числу книг. Имя перед фамилией не считается отдельным человеком; одиночные личные имена («Жан», «Мария», «Карл») исключены — это разные персонажи. Явные исправления: «Голль»/«Голля» склеены в «де Голль»; «Франс» исключён (это «Эр Франс», «Коллеж де Франс», «Франс-Суар»). Полки: «виски» считается, если перед словом нет «в», «на», «по», «к», «у», «его», «её»; «джин» — только со строчной; «чай» не считается. Аудит по сырому тексту просмотрен: расхождения — другие слова с той же основой («ром» — «роман», «метро» — «метров», «голубь» — «Голубчик»). Числа — нижняя оценка.`,
 `<b>Что это не доказывает.</b> Русские числа описывают переводы, а не французский текст Гари; различия книг смешаны с различиями переводчиков. Стилометрия по частым словам различает манеру письма, но не доказывает авторства.`];
$('#method').innerHTML=METHOD.map(m=>`<li>${m}</li>`).join('');

/* тема и ширина */
let lastW=innerWidth; addEventListener('resize',()=>{ if(Math.abs(innerWidth-lastW)>40){ lastW=innerWidth; rerenderAll(); } });
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',rerenderAll);
new MutationObserver(rerenderAll).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
