(function(){
var d=document,root=d.documentElement;
if(!root.classList.contains('m'))return;
window.__hdm=1;
if(!('IntersectionObserver' in window)){root.classList.remove('m');return;}
function $(s,c){return [].slice.call((c||d).querySelectorAll(s));}
var fine=matchMedia('(hover:hover) and (pointer:fine)').matches;

/* Headings: split into the lines they actually wrap to, each rising through its own mask, then put back. */
function lines(h){
  var orig=h.innerHTML,words=[];
  (function walk(n,wrap){[].slice.call(n.childNodes).forEach(function(c){
    if(c.nodeType===3){c.textContent.split(/\s+/).forEach(function(t){if(!t)return;
      var s=d.createElement('span');s.textContent=t;s.style.display='inline-block';var node=s;
      if(wrap){node=wrap.cloneNode(false);node.appendChild(s);}words.push({node:node,s:s});});}
    else if(c.nodeType===1&&c.tagName!=='BR'){walk(c,c);}
  });})(h,null);
  if(!words.length)return;
  h.textContent='';
  words.forEach(function(w,i){h.appendChild(w.node);if(i<words.length-1)h.appendChild(d.createTextNode(' '));});
  /* a word starts a new row only when it sits half a line lower: words inside an <em> with its own line-height
     measure a few pixels off on the same line */
  var rows=[],top=null,half=parseFloat(getComputedStyle(h).fontSize)/2;
  words.forEach(function(w){var t=w.s.offsetTop;if(top===null||Math.abs(t-top)>half){rows.push([]);top=t;}
    rows[rows.length-1].push(w.node);});
  h.textContent='';
  rows.forEach(function(r,i){var m=d.createElement('span');m.className='ln';var l=d.createElement('span');
    l.className='li';l.style.transitionDelay=(i*120)+'ms';
    r.forEach(function(n,j){l.appendChild(n);if(j<r.length-1)l.appendChild(d.createTextNode(' '));});
    m.appendChild(l);h.appendChild(m);});
  h.setAttribute('data-hl','');
  h._done=function(){setTimeout(function(){h.innerHTML=orig;h.classList.add('hl-done');h.removeAttribute('data-hl');},rows.length*120+1200);};
}

/* The Results panel's figures count up to exactly the text the page shows. */
function count(el){
  var t=el.textContent.trim(),m=t.match(/^(\D*?)(\d[\d,]*(?:\.\d+)?)(.*)$/);
  if(!m)return;
  var pre=m[1],raw=m[2],suf=m[3],end=parseFloat(raw.replace(/,/g,'')),dec=(raw.split('.')[1]||'').length,
      fmt={minimumFractionDigits:dec,maximumFractionDigits:dec,useGrouping:raw.indexOf(',')>-1},t0=null;
  el.style.minWidth=el.getBoundingClientRect().width+'px';
  el.textContent=pre+(0).toLocaleString('en-US',fmt)+suf;
  function step(ts){if(t0===null)t0=ts;var p=Math.min(1,(ts-t0)/1400),e=1-Math.pow(1-p,3);
    el.textContent=p<1?pre+(end*e).toLocaleString('en-US',fmt)+suf:t;
    if(p<1)requestAnimationFrame(step);}
  requestAnimationFrame(step);
}

var io=new IntersectionObserver(function(es){es.forEach(function(en){if(!en.isIntersecting)return;
  var el=en.target;io.unobserve(el);el.classList.add('in');
  if(el.hasAttribute('data-rv'))setTimeout(function(){el.style.transitionDelay='';},1600);
  if(el._done)el._done();
  if(el.hasAttribute('data-ct'))setTimeout(function(){count(el);},150);
});},{rootMargin:'0px 0px -8% 0px',threshold:.12});
function watch(el){io.observe(el);}

/* Headings split once the web fonts are in, so line breaks are measured in the real face. The first-screen heading
   waits at most a second (site.css holds it for 1.3s on its own, so it never depends on this script); the hero's
   other parts rise by CSS alone. */
function fontsIn(ms){return d.fonts&&d.fonts.ready?Promise.race([d.fonts.ready,new Promise(function(r){setTimeout(r,ms);})]):Promise.resolve();}
var first=$('.hero h1,.doc h1');
fontsIn(1000).then(function(){first.forEach(function(h){lines(h);if(h.hasAttribute('data-hl'))watch(h);else h.classList.add('hl-done');});});
var heads=$('.band-head h2,.panel-head h2,.platform h2,.about h2,.cta h2,.offer h2');
fontsIn(2500).then(function(){heads.forEach(function(h){if(h.getBoundingClientRect().top<innerHeight*.9){return;}lines(h);watch(h);});});

/* Cards and steps rise as they arrive; running copy, kickers, notes and the footer simply sit there
   (Charles, 11/08/2026: the architect's signature set). */
var groups=['.figure','.service','.work-card','.system','.step','.facts li','.gets li','.scorecard','.how li',
  '.lead-form','.doc-panel section'];
var seen=[];
groups.forEach(function(sel){$(sel).forEach(function(el){
  if(seen.indexOf(el)>-1||el.closest('.hero')||el.closest('h1,h2'))return;seen.push(el);
  var sib=el.parentNode?[].slice.call(el.parentNode.children).filter(function(x){return x.matches(sel);}):[];
  el.style.transitionDelay=Math.min(sib.indexOf(el),6)*90+'ms';el.setAttribute('data-rv','');watch(el);});});
$('.steps').forEach(watch);
$('.figure .v').forEach(function(el){
  if(/\d/.test(el.textContent)){el.setAttribute('data-ct','');watch(el);}});

var top=d.querySelector('.top');
if(top){var on=function(){top.classList.toggle('scrolled',scrollY>8);};on();addEventListener('scroll',on,{passive:true});}

/* Animations that would otherwise run forever stop while they're off screen. */
var loop=new IntersectionObserver(function(es){es.forEach(function(en){
  en.target.classList.toggle('still',!en.isIntersecting);});});
$('.diagram-svg,.cta').forEach(function(el){el.classList.add('still');loop.observe(el);});

/* Depth on pointer: cards tilt toward the cursor in 3D and a soft light follows it (mouse and trackpad only). */
if(fine){
  $('.hero-stack,.work-card').forEach(function(el){
    var max=el.classList.contains('hero-stack')?9:6;el.classList.add('tilt');
    el.addEventListener('pointermove',function(e){var r=el.getBoundingClientRect(),
      x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
      el.style.setProperty('--tx',(x*max).toFixed(2)+'deg');el.style.setProperty('--ty',(-y*max).toFixed(2)+'deg');
      el.style.setProperty('--lx',((x+.5)*100).toFixed(1)+'%');el.style.setProperty('--ly',((y+.5)*100).toFixed(1)+'%');
      el.classList.add('tilting');});
    el.addEventListener('pointerleave',function(){['--tx','--ty','--lx','--ly'].forEach(function(p){
      el.style.removeProperty(p);});el.classList.remove('tilting');});
  });

  /* Parallax: a slight drift through the translate property, so it adds to any transform. All reads, then all
     writes, once per frame. Mouse and trackpad only. */
  var par=$('.hero-card,.cover-ico,.diagram-svg').map(function(el){
    return {el:el,y:0,k:el.classList.contains('cover-ico')?.12:el.classList.contains('hero-card')?.05:.04};});
  var queued=false;
  var drift=function(){queued=false;var vh=innerHeight,rs=par.map(function(p){return p.el.getBoundingClientRect();});
    par.forEach(function(p,i){var r=rs[i];if(r.bottom<-300||r.top>vh+300)return;
      var c=(r.top-p.y)+r.height/2-vh/2;p.y=-c*p.k;p.el.style.translate='0 '+p.y.toFixed(1)+'px';});};
  var ask=function(){if(!queued){queued=true;requestAnimationFrame(drift);}};
  drift();addEventListener('scroll',ask,{passive:true});addEventListener('resize',ask);
}

/* Smooth, inertial scrolling (Lenis, after spykercars.com), loaded after everything above so nothing waits on it.
   Anchor links still land under the header. */
var ls=d.createElement('script');
ls.src='https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js';
ls.integrity='sha384-B2WBjDzEjJpYvhmi2UyEn7rektqkf5suS6sNoyyrf0EBAwBHdkiXxIlU0V5Ru2ed';
ls.crossOrigin='anonymous';
ls.onload=function(){
  if(!window.Lenis)return;
  var lenis=new Lenis({lerp:.09});root.style.scrollBehavior='auto';
  var raf=function(t){lenis.raf(t);requestAnimationFrame(raf);};requestAnimationFrame(raf);
  var here=function(p){return p.replace(/index\.html$/,'');};
  d.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href*="#"]');if(!a)return;
    if(a.origin!==location.origin||here(a.pathname)!==here(location.pathname))return;
    var id=a.hash;if(id.length<2)return;var tg=d.getElementById(id.slice(1));if(!tg)return;
    e.preventDefault();lenis.scrollTo(tg,{offset:-88});history.pushState(null,'',id);
    if(id==='#main')tg.focus({preventScroll:true});
    var m=a.closest('details');if(m)m.removeAttribute('open');});
};
d.head.appendChild(ls);
})();
