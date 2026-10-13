/* ================= report.ui.js: интерактив отчёта (по образцу «Бродского» и «Чехова на просвет») ================= */
/* Подключается после report.app.js и report.chrome.js. Данные: D (stats.json), V (voices.json), EX (explore.json). */

/* ---------- общие помощники ---------- */
const PWT = D.per_tokens, PWT_TOT = PWT.reduce((a,b)=>a+b,0);
const PSH = PER.map(p=>p.slice(2,4)+'–'+p.slice(-2));
const sum = a => a.reduce((x,y)=>x+y,0);
const mean = a => a.length ? sum(a)/a.length : 0;
const sgnPct = v => (v>0?'+':v<0?'−':'')+fmt(Math.abs(Math.round(100*v)))+'%';
const cutS = (s,n) => s.length>n ? s.slice(0,n-1)+'…' : s;
const calm = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const nearScroll = h => h.scrollIntoView({behavior:calm()?'auto':'smooth',block:'nearest'});
const hasWord = k => !!(LEX[k]||LEXN[norm(k)]);
function openW(k){ const key=LEX[k]?k:LEXN[norm(k)]; if(key) openWord(key,true); }
function bookBtn(i,label){ return `<button type="button" class="lnk" data-b="${i}" data-tip="открыть в атласе">${esc(label==null?T(A[i]):label)}</button>`; }
function wordBtn(w,label){ return hasWord(w)?`<button type="button" class="lnk" data-w="${esc(w)}" data-tip="открыть в словоискателе">${esc(label==null?w:label)}</button>`:esc(label==null?w:label); }
function bindLinks(host){
  host.querySelectorAll('button[data-b]').forEach(b=>b.addEventListener('click',()=>selectBook(+b.dataset.b,true)));
  host.querySelectorAll('button[data-w]').forEach(b=>b.addEventListener('click',()=>openW(b.dataset.w))); }
const STEM = w => { w=String(w).replace(/ё/g,'е').split(' ').pop(); return w.length>=7?w.slice(0,-2):w.length>=5?w.slice(0,-1):w; };
const reEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
function hiWord(s,w){ const t=esc(s); try{ return t.replace(new RegExp('('+reEsc(STEM(w)).replace(/е/g,'[её]')+'[а-яё]*)','i'),'<b>$1</b>'); }catch(e){ return t; } }
function sparkSVG(vals,{h=58,color='var(--s1)',labels=PSH,tips=null,unit='',dec=1}={}){ const n=vals.length, w=n*46, mx=Math.max(...vals,1e-9);
  const fm=v=>Number(v).toLocaleString('ru-RU',{maximumFractionDigits:dec});
  const bars=vals.map((v,i)=>{ const bh=Math.max(v>0?2:0,(h-26)*v/mx); const tp=tips?tips[i]:`${labels[i]}: ${fm(v)}${unit}`;
    return `<rect x="${i*46+7}" y="${h-13-bh}" width="32" height="${bh}" rx="2" fill="${color}" data-tip="${esc(tp)}"/><text x="${i*46+23}" y="${h-16-bh}" text-anchor="middle" style="font-size:9.5px;fill:var(--ink-2)">${v>0?fm(v):''}</text><text x="${i*46+23}" y="${h-2}" text-anchor="middle" style="font-size:9.5px;fill:var(--muted)">${esc(labels[i])}</text>`; }).join('');
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-width:${w*1.7}px;display:block" role="img">${bars}</svg>`; }
function entityCard(host,o){
  host.innerHTML=`<div class="eyebrow">${esc(o.eyebrow||'')}</div><div class="ttl">${esc(o.title)}</div><div class="meta">${o.meta||''}</div>
    <div class="tiles">${o.tiles.map(([b,l])=>`<div><b>${b}</b><span>${l}</span></div>`).join('')}</div>${o.sparks||''}
    ${o.chips&&o.chips.length?`<h4>${esc(o.chipsTitle||'Рядом')}</h4><div class="chips">${o.chips.map((c,i)=>`<button type="button" class="chip" data-c="${i}">${esc(c.label)}</button>`).join('')}</div>`:''}${o.body||''}`;
  host.querySelectorAll('button.chip[data-c]').forEach(b=>b.addEventListener('click',()=>o.chips[+b.dataset.c].fn()));
  bindLinks(host); }
function periodBtns(host,cur,on){ host.innerHTML=''; [[-1,'все годы'],...PER.map((p,i)=>[i,p])].forEach(([i,l])=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=l; b.setAttribute('aria-pressed',String(i===cur)); b.addEventListener('click',()=>on(i)); host.appendChild(b); }); }

/* ================= III.3 карта словаря ================= */
const WMD = EX.wmap, WMK = {}; WMD.forEach(m=>{ WMK[m.k]=m; });
const WM = {per:-1, group:-1, sel:null, hov:null, timer:null, n:null, edges:null};
const wmCount = (m,p) => { const L=LEX[m.k]; return L ? (p<0 ? sum(L[1]) : L[1][p]) : 0; };
const wmRate = (m,p) => wmCount(m,p)/(p<0?PWT_TOT:PWT[p])*1000;
const RMAX_ALL = Math.max(...WMD.map(m=>wmRate(m,-1)));
const RMAX_PER = Math.max(...WMD.flatMap(m=>PER.map((_,p)=>wmRate(m,p))));
const wmGroupLabel = c => EX.wgroups[c].slice(0,2).join(' · ');
const wmRising = (m,p) => p>=0 && wmCount(m,p)>=6 && wmRate(m,p)/Math.max(wmRate(m,-1),1e-9)>=1.5;
const wmTop = (p,n=8) => WMD.filter(m=>wmRising(m,p)).sort((a,b)=>wmRate(b,p)/wmRate(b,-1)-wmRate(a,p)/wmRate(a,-1)).slice(0,n);
const wmTerrOp = () => lum(css('--surface'))<0.2?.2:.34;
$('#t-karta').textContent = `${pnr(WMD.length,['самое частое слово русских переводов разложено','самых частых слова русских переводов разложены','самых частых слов русских переводов разложены'])} на карте так, что рядом оказываются слова, которые стоят в похожем окружении (соседи — в пределах пяти значимых слов внутри абзаца, расстановка — t-SNE). Цветные области — группы близких слов. Выберите период или нажмите «Играть»: слова, которых в эти годы заметно больше, вырастут и покраснеют. Нажмите на слово, чтобы увидеть его ближайших соседей.`;
function drawWmap(){
  const box=$('#c-wmap'); const Wd=box.clientWidth||800; const h=Wd<600?Math.round(Wd*1.3):Math.round(Math.min(720,Math.max(460,Wd*0.66))); const [s,w]=svg(box,h);
  const xs=WMD.map(m=>m.x), ys=WMD.map(m=>m.y); const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const padX=Wd<600?26:54, padY=34; const sx=x=>padX+(w-2*padX)*(x-x0)/(x1-x0), sy=y=>padY+(h-2*padY)*(y-y0)/(y1-y0);
  const pos={}; WMD.forEach(m=>{ pos[m.k]=[sx(m.x),sy(m.y)]; });
  const defs=el('defs',{},s); const f=el('filter',{id:'wm-blur',x:'-20%',y:'-20%',width:'140%',height:'140%'},defs); el('feGaussianBlur',{stdDeviation:Wd<600?11:17},f);
  const terr=el('g',{class:'wm-terr',filter:'url(#wm-blur)'},s); const R=Wd<600?24:34;
  WMD.forEach(m=>el('circle',{cx:pos[m.k][0],cy:pos[m.k][1],r:R,fill:css('--g'+(m.c+1)),opacity:wmTerrOp(),'data-g':m.c},terr));
  EX.wgroups.forEach((g,c)=>{ const mm=WMD.filter(m=>m.c===c); if(!mm.length) return;
    const cx=mean(mm.map(m=>pos[m.k][0])), cy=mean(mm.map(m=>pos[m.k][1]));
    const t=txt(s,cx,cy,wmGroupLabel(c),{'text-anchor':'middle',class:'wm-lab','data-lab':c,style:`font-size:${Wd<600?9:11}px;fill:${css('--ink-2')};opacity:0`}); t.setAttribute('paint-order','stroke'); t.setAttribute('stroke',css('--surface')); t.setAttribute('stroke-width','5'); });
  WM.edges=el('g',{class:'wm-terr'},s);
  const nodes=[];
  WMD.forEach(m=>{ const [X,Y]=pos[m.k];
    const t=txt(s,X,Y,m.w,{'text-anchor':'middle',tabindex:0,role:'button','aria-label':m.w,style:'font-family:var(--f-body);cursor:pointer'});
    const c=el('circle',{cx:X,cy:Y-4,r:3.2,class:'dot clickable'},s);
    const pick=()=>{ WM.sel=(WM.sel===m.k)?null:m.k; wmApply(); };
    [t,c].forEach(n=>{ n.addEventListener('click',pick); n.addEventListener('pointerenter',e=>{ if(e.pointerType==='mouse'){ WM.hov=m.k; wmApply(); } });
      n.addEventListener('pointerleave',e=>{ if(e.pointerType==='mouse'){ WM.hov=null; wmApply(); } }); });
    t.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); pick(); } });
    nodes.push({m,t,c,X,Y}); });
  WM.n={nodes,pos}; wmApply();
}
function wmApply(){
  if(!WM.n) return; const {nodes,pos}=WM.n; const p=WM.per, focus=WM.hov||WM.sel;
  const nb=focus?new Set((EX.neighbors[focus]||[]).filter(k=>WMK[k])):new Set();
  const rmax=p<0?RMAX_ALL:RMAX_PER;
  const items=nodes.map(o=>{ const cnt=wmCount(o.m,p); const r=wmRate(o.m,p); const rise=wmRising(o.m,p); const fs=cnt>0?10.5+8.5*Math.sqrt(Math.min(1,r/rmax)):10.5; return {o,cnt,r,rise,fs}; });
  const order=items.slice().sort((a,b)=>((b.o.m.k===focus||nb.has(b.o.m.k))?1e9:0)+(b.rise?1e6:0)+b.r-(((a.o.m.k===focus||nb.has(a.o.m.k))?1e9:0)+(a.rise?1e6:0)+a.r));
  const placed=[]; const fits=b=>!placed.some(q=>b.x<q.x+q.w&&b.x+b.w>q.x&&b.y<q.y+q.h&&b.y+b.h>q.y);
  order.forEach(it=>{ const m=it.o.m, forced=(m.k===focus||nb.has(m.k)); const bw=m.w.length*it.fs*0.55+6, bh=it.fs+2;
    it.dy=0; it.show=false; if(it.cnt<=0) return;
    for(const dy of (forced||it.rise)?[0,-bh,bh,-2*bh,2*bh,-3*bh,3*bh]:[0]){ const bx={x:it.o.X-bw/2,y:it.o.Y+dy-it.fs,w:bw,h:bh}; if(fits(bx)){ it.dy=dy; it.show=true; placed.push(bx); break; } }
    if(!it.show&&forced){ it.show=true; } });
  items.forEach(it=>{ const m=it.o.m; const dim=(WM.group>=0&&m.c!==WM.group)||(focus&&m.k!==focus&&!nb.has(m.k));
    const isF=m.k===focus, isN=nb.has(m.k);
    const tip=`${esc(m.w)}<br>${fmt(it.cnt)} ${plural(it.cnt, ['раз', 'раза', 'раз'])}${p>=0?', '+PER[p]:''}<br>нажмите, чтобы увидеть близкие слова`;
    const ink=isF||isN||it.rise?'--mark':(dim?'--muted':'--ink');
    it.o.t.setAttribute('data-tip',tip); it.o.c.setAttribute('data-tip',tip);
    it.o.t.setAttribute('y',(it.o.Y+it.dy).toFixed(1));
    const st=it.o.t.style; st.fontSize=it.fs.toFixed(1)+'px'; st.fill=css(ink); st.fontWeight=(isF||it.rise)?'700':'400';
    st.opacity=it.show?(dim?.22:1):0; st.pointerEvents=it.show?'auto':'none';
    it.o.c.setAttribute('fill',css(isF||isN||it.rise?'--mark':'--neutral-bar'));
    it.o.c.style.opacity=it.show?0:(dim?.12:(it.cnt===0?.1:(it.rise?.9:.55))); it.o.c.style.pointerEvents=it.show?'none':'auto'; });
  document.querySelectorAll('#c-wmap circle[data-g]').forEach(c=>{ const g=+c.getAttribute('data-g'); c.style.opacity=(WM.group<0||g===WM.group)?wmTerrOp():.04; });
  document.querySelectorAll('#c-wmap .wm-lab').forEach(t=>{ const g=+t.getAttribute('data-lab'); t.style.opacity=(WM.group>=0&&g===WM.group)?.9:0; t.style.fontSize=(WM.group>=0&&g===WM.group)?'15px':''; });
  const E=WM.edges; while(E.firstChild) E.removeChild(E.firstChild);
  if(focus&&pos[focus]){ const [ax,ay]=pos[focus]; nb.forEach(k=>{ const [bx,by]=pos[k]; const dx=bx-ax, dy=by-ay; const cx=(ax+bx)/2-dy*0.16, cy=(ay+by)/2+dx*0.16;
    el('path',{d:`M${ax},${ay-4} Q${cx},${cy} ${bx},${by-4}`,fill:'none',stroke:css('--mark'),'stroke-width':1.5,'stroke-linecap':'round',opacity:.7},E); });
    el('circle',{cx:ax,cy:ay-4,r:14,fill:'none',stroke:css('--mark'),'stroke-width':1.5,opacity:.8},E); }
  document.querySelectorAll('#wm-groups button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===WM.group)));
  document.querySelectorAll('#wm-per button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===WM.per)));
  $('#wm-play').textContent=WM.timer?'❚❚ Пауза':'▶ Играть';
  wmReadout();
}
function wmReadout(){ const host=$('#wm-read'); const p=WM.per, k=WM.sel;
  const link=kk=>`<button type="button" class="chip" data-wk="${esc(kk)}">${esc(kk)}</button>`; let html;
  if(k){ const m=WMK[k]; const nbs=(EX.neighbors[k]||[]).filter(x=>WMK[x]);
    html=`<b>${esc(m.w)}</b> — ${fmt(wmCount(m,-1))} ${plural(wmCount(m,-1), ['раз', 'раза', 'раз'])}; по периодам: ${PER.map((pp,i)=>`${pp}: ${fmt(wmCount(m,i))}`).join(', ')}.<br>Близкие по употреблению (линии на карте): ${nbs.map(link).join(' ')||'—'} <button type="button" class="btn" data-open="${esc(k)}">Открыть в словоискателе →</button>`;
  } else if(p>=0){ const top=wmTop(p);
    html=`<b>${esc(PER[p])}</b> (${esc(D.per_note[p])}). Красным — слова, которых в эти годы заметно больше, чем в среднем (не реже чем в 1,5 раза и не меньше 6 употреблений): ${top.map(m=>link(m.k)).join(' ')||'—'}`;
  } else html=`Размер слова — как часто оно встречается; цветная область — группа слов в похожем окружении. Выберите период или нажмите «Играть», чтобы увидеть, как менялся словарь.`;
  host.innerHTML=html;
  host.querySelectorAll('[data-wk]').forEach(b=>b.addEventListener('click',()=>{ WM.sel=b.dataset.wk; wmApply(); }));
  host.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>openW(b.dataset.open))); }
function wmPlay(){ if(WM.timer){ clearInterval(WM.timer); WM.timer=null; wmApply(); return; }
  if(WM.per<0||WM.per>=NPER-1) WM.per=0; WM.timer=setInterval(()=>{ WM.per=(WM.per+1)%NPER; wmApply(); },2600); wmApply(); }
(function(){ const g=$('#wm-groups'); const mk=(i,l,c)=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.setAttribute('aria-pressed',String(i===WM.group));
    b.innerHTML=(c?`<i style="background:var(--g${i+1})"></i>`:'')+esc(l); b.addEventListener('click',()=>{ WM.group=(WM.group===i&&i>=0)?-1:i; wmApply(); }); g.appendChild(b); };
  mk(-1,'все слова',false); EX.wgroups.forEach((gr,i)=>mk(i,wmGroupLabel(i),true));
  const pr=$('#wm-per'); [[-1,'все годы'],...PER.map((pp,i)=>[i,pp])].forEach(([i,l])=>{ const b=document.createElement('button'); b.type='button'; b.textContent=l; b.setAttribute('aria-pressed',String(i===WM.per));
    b.addEventListener('click',()=>{ if(WM.timer){ clearInterval(WM.timer); WM.timer=null; } WM.per=i; wmApply(); }); pr.appendChild(b); });
  $('#wm-play').addEventListener('click',wmPlay);
  $('#wm-find').addEventListener('input',e=>{ const q=norm(e.target.value); if(!q) return; const hit=WMK[q]||WMD.find(m=>norm(m.w).startsWith(q)); if(hit){ WM.sel=hit.k; wmApply(); } });
  chart(drawWmap,$('#c-wmap')); })();

/* ================= III.4 темы: карточка ================= */
const FNm = D.fields.names;
const thChg = f => { const a=D.fields.per.map(r=>r[f]); const pr=mean(a.slice(0,NPER-1)); return pr>0 ? a[NPER-1]/pr-1 : null; };
function thPick(i, scroll){ const f=FNm[i]; const host=$('#th-card'); const per=D.fields.per.map(r=>r[f]); const sg=D.fields.sign;
  const words=D.fields.words[f].filter(x=>x[1]>0); const loud=EX.theme_loud[f]||[]; const c=thChg(f);
  entityCard(host,{eyebrow:'Тема',title:f,meta:`${words.length} ${plural(words.length, ['слово', 'слова', 'слов'])} темы встречаются в переводах`,
    tiles:[[fmt1(per[NPER-1]),`на 1000 слов, ${PER[NPER-1]}`],[c==null?'—':sgnPct(c),'поздний период к среднему прежних'],[`${fmt1(sg['Ажар'][f])} / ${fmt1(sg['Гари'][f])}`,'на 1000 слов: Ажар / Гари']],
    sparks:`<h4>По периодам, на 1000 слов</h4>${sparkSVG(per,{tips:per.map((v,j)=>`${PER[j]}: ${fmt1(v)} на 1000 слов`)})}`,
    body:`<h4>Слова темы — нажмите, чтобы открыть в словоискателе</h4><div class="chips">${words.slice(0,16).map(([w,n])=>hasWord(w)?`<button type="button" class="chip" data-w="${esc(w)}">${esc(w)} · ${fmt(n)}</button>`:`<span class="chip static">${esc(w)} · ${fmt(n)}</span>`).join('')}</div>
      <h4>Где тема звучит громче всего (книги от 10 тыс. слов)</h4><div class="mini3"><span class="h" style="text-align:left">книга</span><span class="h">год</span><span class="h">на 1000</span>${
      loud.map(([b,v])=>`<span>${bookBtn(b)}</span><span class="n">${A[b].year||'—'}</span><span class="n">${fmt1(v)}</span>`).join('')}</div>`});
  if(scroll) nearScroll(host); }
thPick(flDrill>=0?flDrill:0,false);

/* ================= III.7 цвета: палитра периодов ================= */
const PAL = EX.palette;
(function(){ const tot=PAL.map(r=>sum(r.c.map(c=>c[2]))); const share=(i,nm)=>{ const c=PAL[i].c.find(x=>x[0]===nm); return c&&tot[i]?c[2]/tot[i]:0; };
  const names=[...new Set(PAL.flatMap(r=>r.c.map(c=>c[0])))]; const tots={}; names.forEach(nm=>{ tots[nm]=sum(PAL.map(r=>(r.c.find(c=>c[0]===nm)||[0,0,0])[2])); });
  const cand=names.filter(nm=>tots[nm]>=20).map(nm=>({nm,last:share(NPER-1,nm),prev:mean(PAL.slice(0,NPER-1).map((_,i)=>share(i,nm)))}));
  const up=cand.slice().sort((a,b)=>(b.last-b.prev)-(a.last-a.prev))[0], dn=cand.slice().sort((a,b)=>(a.last-a.prev)-(b.last-b.prev))[0];
  const bw=i=>((PAL[i].c.find(c=>c[0]==='белый')||[0,0,0])[2]+(PAL[i].c.find(c=>c[0]==='чёрный')||[0,0,0])[2])/tot[i];
  $('#f-cveta').textContent=`Главные цвета Гари во все периоды — белый и чёрный: вместе ${fmt(Math.round(100*mean(PAL.map((_,i)=>bw(i)))))}% цветовых слов в среднем по периодам. Сильнее всего к концу выросла доля цвета «${up.nm}» (${fmt1(100*up.last)}% в ${PER[NPER-1]} против ${fmt1(100*up.prev)}% в среднем раньше), сильнее всего упала — «${dn.nm}» (${fmt1(100*dn.last)}% против ${fmt1(100*dn.prev)}%).`; })();
chart(()=>{ const box=$('#c-palette'); const rowH=44; const h=PAL.length*rowH+8; const [s,w]=svg(box,h); const ring=css('--ring'); const lw=w<560?78:96;
  PAL.forEach((r,i)=>{ const y=i*rowH+4; const tot=sum(r.c.map(c=>c[2]))||1; let x=lw; const Wd=w-lw-4;
    txt(s,lw-10,y+17,r.p,{'text-anchor':'end',style:'fill:var(--ink);font-size:12px'}); txt(s,lw-10,y+31,`${fmt(tot)} ${plural(tot, ['слово', 'слова', 'слов'])}`,{'text-anchor':'end',style:'fill:var(--muted);font-size:10.5px'});
    r.c.forEach(([name,hex,n])=>{ const ww=Wd*n/tot; if(ww<0.5) return; const k=hasWord(name);
      const rc=el('rect',{x:x+.5,y,width:Math.max(.5,ww-1),height:rowH-10,fill:hex,stroke:ring,'stroke-width':.8,class:k?'clickable':'','data-tip':`${PER[i]} · ${esc(name)}: ${n} (${fmt1(100*n/tot)}%)${k?'<br>нажмите — слово в словоискателе':''}`},s);
      if(k) rc.addEventListener('click',()=>openW(name));
      if(ww>=58) txt(s,x+ww/2,y+(rowH-10)/2+4,cutS(name,Math.floor(ww/7.2)),{'text-anchor':'middle',style:`pointer-events:none;font-size:11.5px;fill:${lum(hex)>0.42?'#1d1a17':'#f4f1ea'}`});
      x+=ww; }); }); }, $('#c-palette'));

/* ================= V.1 «Круг Гари»: сеть ================= */
const NETD = EX.net, NN = NETD.nodes, NE = NETD.edges, NC = NETD.clusters;
const NT = {per:-1, cl:-1, sel:null, hov:null, N:null};
const TXP = PER.map(p=>RU_OWN.filter(a=>a.year&&a.year>=+p.slice(0,4)&&a.year<=+p.slice(-4)).length);
const ntCount = n => NT.per>=0 ? n.per[NT.per] : n.n;
const clCol = c => c<0 ? css('--neutral-bar') : css('--g'+(c+1));
(function(){ const top=NN.slice().sort((a,b)=>b.n-a.n); const E=NE.slice().sort((a,b)=>b[2]-a[2])[0]; const big=NC.slice().sort((a,b)=>b.n-a.n)[0];
  $('#t-net').textContent=`Люди, которых Гари называет хотя бы в ${NETD.min_books} ${plural(NETD.min_books,['книге','книгах'])}: исторические лица, писатели, художники, герои мифов и книг — ${NN.length} ${plural(NN.length, ['имя', 'имени', 'имён'])}. Имена стоят по кругу, цвет — круг имён, которые чаще стоят рядом. Лента между двумя именами значит, что они встречаются в одном абзаце; чем шире лента, тем чаще. Длина дуги — сколько у имени таких общих абзацев. Выберите период или круг, найдите имя — откроется карточка с цитатами.`;
  $('#f-krug').textContent=`Чаще всех у Гари назван ${top[0].name} — в ${top[0].n} ${plural(top[0].n, ['книге', 'книгах', 'книгах'])} из ${RU_OWN.length}; за ним ${top.slice(1,6).map(r=>`${r.name} (${r.n})`).join(', ')}. Имена складываются в ${NC.length} ${plural(NC.length, ['круг', 'круга', 'кругов'])}; самый большой — ${big.names.join(', ')} и ещё ${big.n-big.names.length}. Чаще всего рядом стоят ${NN[E[0]].name} и ${NN[E[1]].name}: в ${E[2]} ${plural(E[2], ['абзаце', 'абзацах', 'абзацах'])}.`; })();
function ntPer(i){ NT.per=i; ntApply(); }
periodBtns($('#pp-per'),NT.per,ntPer);
(function(){ const g=$('#pp-clusters'); const mk=(i,l)=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.setAttribute('aria-pressed',String(i===NT.cl));
  b.innerHTML=(i>=0?`<i style="background:var(--g${i+1})"></i>`:'')+esc(l); b.addEventListener('click',()=>{ NT.cl=(NT.cl===i&&i>=0)?-1:i; ntApply(); }); g.appendChild(b); };
  mk(-1,'все круги'); NC.forEach((c,i)=>mk(i,c.names.join(' · ')+' ('+c.n+')')); })();
/* хордовая диаграмма связей: имена по кругу (сгруппированы по кругам имён), ленты — общие абзацы/строфы.
   chordNet(box, nodes, edges, {pick(i|null), hover(i|null)}) → {apply({foc, sel, on(i), tip(i)})} */
function chordNet(box, NOD, EDG, o){
  const Wd=box.clientWidth||800, mob=innerWidth<600, h=mob?Wd+60:Math.round(Math.min(Wd,760)); const [s,w]=svg(box,h);
  const fs=mob?10.5:11.5, th=mob?8:11, cx=w/2, cy=h/2, R=Math.min(w,h-(mob?60:0))/2-(mob?54:92), N=NOD.length, TAU=2*Math.PI;
  const P=(a,r)=>[cx+r*Math.cos(a),cy+r*Math.sin(a)], f1=v=>v.toFixed(1);
  // связи сети + у каждого имени его ближайшие соседи (nb): иначе у редких имён остаётся одна лента
  const EM=new Map(), key=(i,j)=>i<j?i+'_'+j:j+'_'+i; EDG.forEach(([i,j,wt])=>EM.set(key(i,j),[Math.min(i,j),Math.max(i,j),wt]));
  NOD.forEach((n,i)=>(n.nb||[]).forEach(([j,wt])=>{ if(j!==i&&!EM.has(key(i,j))) EM.set(key(i,j),[Math.min(i,j),Math.max(i,j),wt]); }));
  const E2=[...EM.values()];
  const adj=NOD.map(()=>[]); E2.forEach(([i,j,wt])=>{ adj[i].push([j,wt]); adj[j].push([i,wt]); });
  const str=adj.map(a=>a.reduce((t,[,wt])=>t+wt,0)), wOf=i=>Math.max(str[i],1);
  const cls=[...new Set(NOD.map(n=>n.cl))].sort((a,b)=>(a<0)-(b<0)||a-b);
  const order=[]; cls.forEach(c=>NOD.map((_,i)=>i).filter(i=>NOD[i].cl===c).sort((a,b)=>wOf(b)-wOf(a)||NOD[b].n-NOD[a].n).forEach(i=>order.push(i)));
  const gap=cls.length>1?0.03:0, span=TAU-gap*cls.length, tot=order.reduce((t,i)=>t+wOf(i),0);
  const a0=[], a1=[], ang=[]; let a=-Math.PI/2, prev=null;
  order.forEach(i=>{ if(prev!==null&&NOD[i].cl!==prev) a+=gap; prev=NOD[i].cl; const d=span*wOf(i)/tot; a0[i]=a; a1[i]=a+d; ang[i]=a+d/2; a+=d; });
  const dA=(x,y)=>Math.atan2(Math.sin(x-y),Math.cos(x-y));
  const gR=el('g',{},s), gA=el('g',{},s), gL=el('g',{},s);
  // ленты: у каждого имени свой отрезок дуги на каждую связь, по порядку соседей вокруг круга
  const slot={}; NOD.forEach((_,i)=>{ let c=a0[i]; const k=(a1[i]-a0[i])/wOf(i);
    adj[i].slice().sort((p,q)=>dA(ang[q[0]],ang[i])-dA(ang[p[0]],ang[i])).forEach(([j,wt])=>{ slot[i+'_'+j]=[c,c+wt*k]; c+=wt*k; }); });
  const Ri=R-1, arcTo=(x,y)=>`A${f1(Ri)},${f1(Ri)} 0 0 1 ${f1(x)},${f1(y)}`;
  const ribs=E2.map(([i,j,wt])=>{ const [p0,p1]=slot[i+'_'+j], [q0,q1]=slot[j+'_'+i];
    const A0=P(p0,Ri),A1=P(p1,Ri),B0=P(q0,Ri),B1=P(q1,Ri);
    const d=`M${f1(A0[0])},${f1(A0[1])}${arcTo(...A1)}Q${f1(cx)},${f1(cy)} ${f1(B0[0])},${f1(B0[1])}${arcTo(...B1)}Q${f1(cx)},${f1(cy)} ${f1(A0[0])},${f1(A0[1])}Z`;
    return {i,j,wt,p:el('path',{d},gR)}; });
  const arcs=NOD.map((n,i)=>{ const b=Math.max(a1[i]-.0025,a0[i]+.002), big=b-a0[i]>Math.PI?1:0;
    const [x0,y0]=P(a0[i],R),[x1,y1]=P(b,R),[x2,y2]=P(b,R+th),[x3,y3]=P(a0[i],R+th);
    const p=el('path',{d:`M${f1(x0)},${f1(y0)}A${f1(R)},${f1(R)} 0 ${big} 1 ${f1(x1)},${f1(y1)}L${f1(x2)},${f1(y2)}A${f1(R+th)},${f1(R+th)} 0 ${big} 0 ${f1(x3)},${f1(y3)}Z`,
      class:'clickable',tabindex:0,role:'button','aria-label':n.name},gA);
    p.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); o.pick(i); } });
    p.addEventListener('pointerenter',e=>{ if(e.pointerType==='mouse') o.hover(i); }); p.addEventListener('pointerleave',e=>{ if(e.pointerType==='mouse') o.hover(null); });
    return p; });
  // нажатие: по дуге или рядом с кругом — ближайшее имя по углу; в середине круга — снять выбор
  s.addEventListener('click',e=>{ const bb=s.getBoundingClientRect(), k=w/bb.width, x=(e.clientX-bb.left)*k-cx, y=(e.clientY-bb.top)*k-cy, r=Math.hypot(x,y);
    if(r<R*.72){ o.pick(null); return; } const t=Math.atan2(y,x); let best=null, bd=9;
    order.forEach(i=>{ const d=Math.max(0,Math.abs(dA(t,ang[i]))-(a1[i]-a0[i])/2); if(d<bd){ bd=d; best=i; } });
    o.pick(best); });
  const col=c=>c<0?css('--neutral-bar'):css('--g'+(c+1));
  const LBL='font-family:var(--f-body);pointer-events:none;paint-order:stroke;stroke-width:3px;stroke:'+css('--surface')+`;font-size:${fs}px`;
  function apply({foc,sel,on,tip}){
    const nb=new Set(); if(foc!=null){ nb.add(foc); adj[foc].forEach(([j])=>nb.add(j)); }
    ribs.forEach(r=>{ const both=on(r.i)&&on(r.j), isF=foc!=null&&(r.i===foc||r.j===foc);
      const c=isF?NOD[r.i===foc?r.j:r.i].cl:(NOD[r.i].n>=NOD[r.j].n?NOD[r.i].cl:NOD[r.j].cl);
      r.p.setAttribute('fill',col(c)); r.p.style.opacity=!both?.03:(foc==null?.42:(isF?.85:.04)); if(isF) gR.appendChild(r.p); });
    arcs.forEach((p,i)=>{ p.setAttribute('fill',col(NOD[i].cl)); p.style.opacity=!on(i)?.15:(foc!=null&&!nb.has(i)?.3:1);
      p.setAttribute('stroke',i===sel?css('--ink'):'none'); p.setAttribute('stroke-width',1.5); p.setAttribute('data-tip',tip(i)); });
    // подписи: сначала выбранное имя и его соседи, потом самые связанные; на телефоне при выборе — только соседи
    gL.innerHTML=''; const shown=[], minGap=(fs+1)/(R+th);
    const pri=i=>(i===foc?2e9:0)+(nb.has(i)?1e9:0)+wOf(i);
    order.slice().sort((x,y)=>pri(y)-pri(x)).forEach(i=>{ if(!on(i)&&i!==foc) return; if(foc!=null&&mob&&!nb.has(i)) return;
      if(shown.some(t=>Math.abs(dA(t,ang[i]))<minGap)) return; shown.push(ang[i]);
      const t=ang[i], left=Math.cos(t)<0, [x,y]=P(t,R+th+5);
      const dx=Math.cos(t), dy=Math.sin(t), room=Math.min(dx>.01?(w-x)/dx:dx<-.01?x/-dx:1e9, dy>.01?(h-y)/dy:dy<-.01?y/-dy:1e9)-4;
      let nm=NOD[i].name; const maxc=Math.floor(room/(fs*.56)); if(nm.length>maxc) nm=maxc>3?nm.slice(0,maxc-1)+'…':'';
      if(!nm) return; const deg=t*180/Math.PI;
      const tx=txt(gL,f1(x),f1(y),nm,{'text-anchor':left?'end':'start','dominant-baseline':'middle',transform:`rotate(${f1(left?deg+180:deg)} ${f1(x)} ${f1(y)})`,style:LBL});
      tx.style.fill=css('--ink'); tx.style.fontWeight=i===foc?'700':'400'; tx.style.opacity=foc!=null&&!nb.has(i)?.35:1; });
  }
  return {apply};
}
function drawNet(){
  NT.N=chordNet($('#c-net'),NN,NE,{pick:i=>{ NT.sel=(i==null||NT.sel===i)?null:i; ntApply(); if(NT.sel!=null&&matchMedia('(max-width:999px)').matches) nearScroll($('#pp-card')); },hover:i=>{ NT.hov=i; ntApply(); }});
  ntApply();
}
function ntApply(){
  document.querySelectorAll('#pp-per button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===NT.per)));
  document.querySelectorAll('#pp-clusters button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===NT.cl)));
  if(NT.N){ const foc=NT.hov!=null?NT.hov:NT.sel;
    NT.N.apply({foc,sel:NT.sel,on:i=>ntCount(NN[i])>0&&(NT.cl<0||NN[i].cl===NT.cl),tip:i=>`<b>${esc(NN[i].name)}</b><br>${NT.per>=0?PER[NT.per]+': ':''}в ${ntCount(NN[i])} ${plural(ntCount(NN[i]), ['книге', 'книгах', 'книгах'])}${NT.per>=0?'':', '+NN[i].np+' '+plural(NN[i].np, ['абзац', 'абзаца', 'абзацев'])}<br>нажмите, чтобы открыть карточку`}); }
  ntCard();
}
function ntCard(){
  const host=$('#pp-card'); const n=NT.sel!=null?NN[NT.sel]:null;
  if(!n){ const top=NN.slice().sort((a,b)=>b.n-a.n).slice(0,10);
    host.innerHTML=`<div class="eyebrow">Карточка</div><div class="ttl">Выберите имя</div><p class="note">Нажмите на имя на круге или найдите человека по имени. Например:</p><div class="chips">${top.map(x=>`<button type="button" class="chip" data-nm="${esc(x.name)}">${esc(x.name)}</button>`).join('')}</div>`;
    host.querySelectorAll('[data-nm]').forEach(b=>b.addEventListener('click',()=>ntSelectByName(b.dataset.nm))); return; }
  const nbs=(n.nb||[]).map(([j,w])=>({label:`${NN[j].name} · ${w}`,fn:()=>{ NT.sel=j; ntApply(); }}));
  const rates=n.per.map((v,i)=>TXP[i]?100*v/TXP[i]:0); const peak=rates.indexOf(Math.max(...rates));
  const ys=n.books.map(([b])=>A[b].year).filter(Boolean); const yrs=ys.length?(Math.min(...ys)===Math.max(...ys)?String(ys[0]):`${Math.min(...ys)}–${Math.max(...ys)}`):'—';
  entityCard(host,{eyebrow:'Круг Гари',title:n.name,meta:`круг: ${esc(n.cl>=0?NC[n.cl].names.join(' · '):'вне кругов')} · чаще всего в ${PER[peak]}`,
    tiles:[[fmt(n.n),plural(n.n, ['книга', 'книги', 'книг'])],[fmt(n.np),plural(n.np, ['абзац', 'абзаца', 'абзацев'])],[yrs,'годы книг']],
    sparks:`<h4>Доля книг периода, где назван, %</h4>${sparkSVG(rates,{unit:'%',dec:0,tips:rates.map((v,i)=>`${PER[i]}: ${n.per[i]} из ${TXP[i]} ${plural(TXP[i],['книги','книг'])}`)})}`,
    chips:nbs,chipsTitle:'Чаще всего рядом (общих абзацев)',
    body:`<h4>В каких книгах (абзацев с именем)</h4><div class="mini3"><span class="h" style="text-align:left">книга</span><span class="h">год</span><span class="h">абзацев</span>${n.books.map(([b,k])=>`<span>${bookBtn(b)}</span><span class="n">${A[b].year||'—'}</span><span class="n">${k}</span>`).join('')}</div>
      <h4>Из текстов</h4>${(n.ctx||[]).map(c=>`<blockquote>${hiWord(c.s,n.name)}<cite>${bookBtn(c.b)}, ${A[c.b].year||''}</cite></blockquote>`).join('')}${hasWord(n.name)?`<p><button type="button" class="btn" data-w="${esc(n.name)}">Открыть в словоискателе →</button></p>`:''}`}); }
function ntSelectByName(name){ const i=NN.findIndex(n=>n.name===name); if(i>=0){ NT.sel=i; ntApply(); } }
(function(){ const inp=$('#pp-find'), sug=$('#pp-sug');
  inp.addEventListener('input',()=>{ const q=norm(inp.value); sug.innerHTML=''; if(!q) return; const m=NN.filter(x=>norm(x.name).startsWith(q)).concat(NN.filter(x=>!norm(x.name).startsWith(q)&&norm(x.name).includes(q))).slice(0,8);
    m.forEach(x=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=x.name; b.addEventListener('click',()=>{ inp.value=x.name; sug.innerHTML=''; ntSelectByName(x.name); }); sug.appendChild(b); });
    if(m.length===1&&norm(m[0].name)===q) ntSelectByName(m[0].name); }); })();
chart(drawNet,$('#c-net'));

/* ================= I.3 хронология: карточка года ================= */
function yearCard(y,scroll){ const host=$('#yr-card'); const L=D.works.filter(w=>w.year===y);
  const ev=EVENTS.filter(e=>e[0]===y).map(e=>e[1]); const ruW=sum(L.filter(w=>w.ru!=null).map(w=>A[w.ru].words));
  entityCard(host,{eyebrow:'Год',title:String(y),meta:ev.length?esc(ev.join('; ')):'по году первой публикации',
    tiles:[[fmt(L.length),plural(L.length, ['произведение', 'произведения', 'произведений'])],[fmt(L.filter(w=>w.fr!=null).length),'есть во французском оригинале'],[fmt(ruW),plural(ruW,['слово в переводах','слова в переводах','слов в переводах'])]],
    body:L.length?`<h4>Произведения года — нажмите, чтобы открыть в атласе</h4><div class="mini3"><span class="h" style="text-align:left">книга</span><span class="h">подпись</span><span class="h">слов</span>${L.map(w=>{ const b=w.ru!=null?w.ru:w.fr; return `<span>${bookBtn(b)}${w.ru==null?' <span class="muted">фр.</span>':''}</span><span class="n">${esc(SIGN[w.sign]||'')}</span><span class="n">${fmt(A[b].words)}</span>`; }).join('')}</div>`:'<p class="note">В корпусе нет произведений этого года.</p>'});
  if(scroll) nearScroll(host); }
yearCard(1975,false);

/* ================= II.6 строение рядом ================= */
const CMP = [];
(function(){ const sel=$('#cmp-sel'); A.filter(a=>a.role==='own').slice().sort((a,b)=>(a.year||9999)-(b.year||9999)).forEach(a=>{ const o=document.createElement('option'); o.value=a.i; o.textContent=`${a.year||'—'} · ${cutS(T(a),46)}${a.lang==='fr'?' (фр.)':''}`; sel.appendChild(o); });
  $('#cmp-add').addEventListener('click',()=>cmpAdd(+sel.value));
  $('#cmp-clear').addEventListener('click',()=>{ CMP.length=0; cmpRender(); }); })();
function cmpAdd(i){ const k=CMP.indexOf(i); if(k>=0) CMP.splice(k,1); if(CMP.length>=4) CMP.shift(); CMP.push(i); cmpRender(); }
function cmpCanvas(host,a,wpx,mxs){ const cv=document.createElement('canvas'); host.appendChild(cv); const H=54, dpr=Math.min(2,devicePixelRatio||1);
  cv.width=wpx*dpr; cv.height=H*dpr; cv.style.width=wpx+'px'; cv.style.height=H+'px'; const c=cv.getContext('2d'); c.setTransform(dpr,0,0,dpr,0,0);
  const n=a.seq.length, bw=wpx/n; a.seq.forEach((v,i)=>{ if(a.seqk[i]==='2') return; const h=Math.max(1.5,(H-4)*Math.sqrt(Math.min(v,mxs)/mxs)); c.fillStyle=css(a.seqk[i]==='1'?'--mark':'--neutral-bar'); c.fillRect(i*bw,H-h,Math.max(.8,bw-.4),h); }); }
function cmpRender(){ const host=$('#cmp-list'); host.innerHTML='';
  if(!CMP.length){ host.innerHTML='<p class="note">Добавьте книги из списка или кнопкой «+ в „Строение рядом“» в карточке атласа.</p>'; return; }
  const cw=host.clientWidth||600; const mxs=250;
  CMP.slice().sort((x,y)=>(A[x].year||0)-(A[y].year||0)).forEach(i=>{ const a=A[i]; const row=document.createElement('div'); row.className='cmp-row';
    row.innerHTML=`<div class="h"><b>${bookBtn(i)}</b><span>${a.year||'—'} · ${esc(SIGN[a.sign]||'')} · ${fmt(a.words)} ${plural(a.words, ['слово', 'слова', 'слов'])} · ${fmt(a.paras)} ${plural(a.paras, ['абзац', 'абзаца', 'абзацев'])} · диалог ${fmt1(a.dlg)}% · фраза ${pn(a.sl_med,['слово','слова','слов'],1)}</span><button type="button" class="x" data-x="${i}" aria-label="убрать из сравнения" data-tip="убрать">✕</button></div>`;
    host.appendChild(row); cmpCanvas(row,a,cw,mxs); bindLinks(row);
    row.querySelector('[data-x]').addEventListener('click',()=>{ CMP.splice(CMP.indexOf(i),1); cmpRender(); }); }); }
(function(){ const pick=w=>A.findIndex(a=>a.work===w&&a.lang==='ru'&&a.role==='own');
  ["La Promesse de l'aube","La Danse de Gengis Cohn","Gros-Câlin","Les Cerfs-volants"].map(pick).filter(i=>i>=0).forEach(i=>CMP.push(i));
  chart(cmpRender,$('#cmp-list')); })();


/* ================= методика: новые разделы ================= */
$('#method').insertAdjacentHTML('beforeend',[
  `<b>Карта словаря</b> — ${pnr(WMD.length,['самое частое слово русских переводов','самых частых слова русских переводов','самых частых слов русских переводов'])} (без имён и служебных слов); окружение — соседи в пределах пяти значимых слов (существительные, прилагательные, глаголы) внутри абзаца, PPMI, сжатие до 100 измерений, расстановка t-SNE, ${pnr(EX.wgroups.length,['группа','группы','групп'])} k-средних. «Заметно больше в периоде» — не реже чем в 1,5 раза, чем в среднем, и не меньше 6 раз.`,
  `<b>Круг Гари</b> — имена, названные хотя бы в ${NETD.min_books} ${plural(NETD.min_books,['книге','книгах'])} (${NN.length} самых частых по числу книг). Связь — два имени в одном абзаце; круги — спектральная кластеризация, раскладка «островами» (как в «Бродском на просвет»). Исключены отдельные личные имена, места, названия и частицы через дефис; склеены написания («Голля» → «де Голль», «Рембрандта» → «Рембрандт» и т. п.) — полный список в <code>analysis/explore.py</code>.`,
  `<b>Цвета</b> — цветовые слова по заданному списку (в текстах нашлось ${new Set(PAL.flatMap(r=>r.c.map(c=>c[0]))).size}), только со строчной буквы (иначе «Белый» — фамилия); ширина отрезка — доля слова среди цветовых слов периода.`
].map(x=>`<li>${x}</li>`).join(''));
