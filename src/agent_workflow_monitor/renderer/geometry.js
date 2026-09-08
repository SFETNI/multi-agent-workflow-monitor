window.installGeometry = function(root){
const stage=root.querySelector(".av-stage"),svg=stage.querySelector(".av-edges");
 function redraw(){
  const rect=stage.getBoundingClientRect();svg.setAttribute('viewBox',`0 0 ${rect.width} ${rect.height}`);
  const radius=Math.min(rect.width*.205,rect.height*.285),cy=rect.height*.71;
  stage.querySelectorAll('.av-orbit').forEach(o=>{
   const cx=rect.width*(o.classList.contains('right')?.77:.23);
   Object.assign(o.style,{left:(cx-radius)+'px',top:(cy-radius)+'px',width:(radius*2)+'px',height:(radius*2)+'px'});
  });
  stage.querySelectorAll('.av-lane').forEach(n=>{n.style.top=(cy-radius)+'px'});
  svg.querySelectorAll('[data-from]').forEach(p=>{
   const a=stage.querySelector(`[data-node="${p.dataset.from}"]`),b=stage.querySelector(`[data-node="${p.dataset.to}"]`);
   if(!a||!b)return;
   const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();
   const ax=ar.left-rect.left+ar.width/2,ay=ar.top-rect.top+ar.height/2;
   const bx=br.left-rect.left+br.width/2,by=br.top-rect.top+br.height/2;
   const dx=bx-ax,dy=by-ay,d=Math.hypot(dx,dy)||1;
   const x1=ax+dx/d*(ar.width/2+10),y1=ay+dy/d*(ar.height/2+10);
   const x2=bx-dx/d*(br.width/2+13),y2=by-dy/d*(br.height/2+13);

   let bend=(p.dataset.from==='A-01'||p.dataset.to==='A-01')&&Math.abs(dx)>rect.width*.18? -rect.height*.11 : 0;
   if(p.dataset.from==='H-01'&&p.dataset.to==='X-01')bend=rect.height*.12;
   const cx=(x1+x2)/2,cy=(y1+y2)/2+bend;
   p.setAttribute('d',`M${x1},${y1} Q${cx},${cy} ${x2},${y2}`);
   const label=stage.querySelector(`[data-edge-label="${p.dataset.edgeId||''}"]`);
   if(label){
    const t=.64,u=1-t;
    label.style.left=(u*u*x1+2*u*t*cx+t*t*x2)+'px';
    label.style.top=(u*u*y1+2*u*t*cy+t*t*y2)+'px';
   }
  });
 }

new ResizeObserver(redraw).observe(stage);requestAnimationFrame(redraw);return redraw;};
