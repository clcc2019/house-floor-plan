(function(){
  const overlay=document.getElementById('viewer-overlay');
  if(!overlay) return;
  const container=overlay.querySelector('.viewer-container');
  const content=overlay.querySelector('.viewer-content');
  const title=overlay.querySelector('.viewer-title');
  const zoomInfo=overlay.querySelector('.viewer-zoom-info');

  let scale=1, tx=0, ty=0, dragging=false, lastX=0, lastY=0;
  const MIN_SCALE=0.2, MAX_SCALE=8;

  function setTransform(animate){
    if(!animate) content.classList.add('no-transition');
    else content.classList.remove('no-transition');
    content.style.transform=`translate(${tx}px,${ty}px) scale(${scale})`;
    showZoom();
  }

  function showZoom(){
    zoomInfo.textContent=Math.round(scale*100)+'%';
    zoomInfo.classList.add('visible');
    clearTimeout(showZoom._t);
    showZoom._t=setTimeout(()=>zoomInfo.classList.remove('visible'),1200);
  }

  function fitToView(){
    const cw=container.clientWidth, ch=container.clientHeight;
    const el=content.firstElementChild;
    if(!el) return;
    const ew=el.getBoundingClientRect().width/scale||el.clientWidth||cw;
    const eh=el.getBoundingClientRect().height/scale||el.clientHeight||ch;
    const nw=el.naturalWidth||el.scrollWidth||ew;
    const nh=el.naturalHeight||el.scrollHeight||eh;
    scale=Math.min(cw*0.95/nw, ch*0.95/nh, 1);
    tx=(cw-nw*scale)/2;
    ty=(ch-nh*scale)/2;
    setTransform(true);
  }

  function open(src, alt, isSvg){
    content.innerHTML='';
    if(isSvg){
      const obj=document.createElement('object');
      obj.type='image/svg+xml';
      obj.data=src;
      obj.style.width='100%';
      obj.style.height='auto';
      obj.addEventListener('load',()=>setTimeout(fitToView,50));
      content.appendChild(obj);
    }else{
      const img=document.createElement('img');
      img.src=src;
      img.alt=alt||'';
      img.addEventListener('load',fitToView);
      content.appendChild(img);
    }
    title.textContent=alt||'';
    overlay.classList.add('active');
    document.body.style.overflow='hidden';
    scale=1;tx=0;ty=0;
  }

  function close(){
    overlay.classList.remove('active');
    document.body.style.overflow='';
    content.innerHTML='';
  }

  overlay.querySelector('.btn-close').addEventListener('click',close);
  overlay.querySelector('.btn-fit').addEventListener('click',fitToView);
  overlay.querySelector('.btn-zin').addEventListener('click',()=>{
    scale=Math.min(scale*1.3,MAX_SCALE);
    const cw=container.clientWidth/2, ch=container.clientHeight/2;
    tx=cw-(cw-tx)*1.3; ty=ch-(ch-ty)*1.3;
    setTransform(true);
  });
  overlay.querySelector('.btn-zout').addEventListener('click',()=>{
    scale=Math.max(scale/1.3,MIN_SCALE);
    const cw=container.clientWidth/2, ch=container.clientHeight/2;
    tx=cw-(cw-tx)/1.3; ty=ch-(ch-ty)/1.3;
    setTransform(true);
  });
  overlay.querySelector('.btn-one').addEventListener('click',()=>{
    const cw=container.clientWidth, ch=container.clientHeight;
    const el=content.firstElementChild;
    const nw=el?.naturalWidth||el?.scrollWidth||cw;
    const nh=el?.naturalHeight||el?.scrollHeight||ch;
    scale=1; tx=(cw-nw)/2; ty=(ch-nh)/2;
    setTransform(true);
  });

  container.addEventListener('wheel',(e)=>{
    e.preventDefault();
    const rect=container.getBoundingClientRect();
    const mx=e.clientX-rect.left, my=e.clientY-rect.top;
    const factor=e.deltaY<0?1.15:1/1.15;
    const ns=Math.max(MIN_SCALE,Math.min(scale*factor,MAX_SCALE));
    const ratio=ns/scale;
    tx=mx-(mx-tx)*ratio; ty=my-(my-ty)*ratio;
    scale=ns;
    setTransform(false);
  },{passive:false});

  container.addEventListener('pointerdown',(e)=>{
    if(e.button!==0) return;
    dragging=true; lastX=e.clientX; lastY=e.clientY;
    container.classList.add('dragging');
    container.setPointerCapture(e.pointerId);
  });
  container.addEventListener('pointermove',(e)=>{
    if(!dragging) return;
    tx+=e.clientX-lastX; ty+=e.clientY-lastY;
    lastX=e.clientX; lastY=e.clientY;
    setTransform(false);
  });
  container.addEventListener('pointerup',()=>{
    dragging=false; container.classList.remove('dragging');
  });

  container.addEventListener('dblclick',(e)=>{
    const rect=container.getBoundingClientRect();
    const mx=e.clientX-rect.left, my=e.clientY-rect.top;
    const ns=scale<1.5?Math.min(scale*2.5,MAX_SCALE):1;
    if(ns===1){ fitToView(); return; }
    const ratio=ns/scale;
    tx=mx-(mx-tx)*ratio; ty=my-(my-ty)*ratio;
    scale=ns;
    setTransform(true);
  });

  document.addEventListener('keydown',(e)=>{
    if(!overlay.classList.contains('active')) return;
    if(e.key==='Escape') close();
    if(e.key==='+' || e.key==='=') overlay.querySelector('.btn-zin').click();
    if(e.key==='-') overlay.querySelector('.btn-zout').click();
    if(e.key==='0') fitToView();
    if(e.key==='1') overlay.querySelector('.btn-one').click();
  });

  document.querySelectorAll('[data-viewer]').forEach(el=>{
    el.addEventListener('click',()=>{
      const src=el.dataset.viewerSrc||el.querySelector('img,object')?.src||'';
      const svgSrc=el.dataset.viewerSvg||'';
      const alt=el.dataset.viewerAlt||el.querySelector('img')?.alt||'';
      if(svgSrc){ open(svgSrc,alt,true); }
      else{ open(src,alt,false); }
    });
  });

  const obs=new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');obs.unobserve(e.target)}});
  },{threshold:0.08});
  document.querySelectorAll('.fade-in').forEach(el=>obs.observe(el));
})();
