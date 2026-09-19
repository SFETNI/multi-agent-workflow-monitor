"use strict";
(() => {
 const D=window.PUBLIC_SNAPSHOT,P=window.PRESENTATION;
 const names=['Command Center','Agent map','Inspector','Hand-offs and activity','Workstream overview','Sessions and usage','Activity and debugging','Workflow & Trace'];
 const allowed={root:['schema_version','title','subtitle','disclosure','summary','agents','workstreams','edges','activity','sessions','host'],summary:['active_agents','monitored_agents','human_actions','blockers','freshness'],agent:['id','role','kind','status','workstream','working','responsibilities'],workstream:['id','record_id','status'],edge:['id','from','to','kind','active','action'],activity:['actor_id','workstream','type','age','preview','detail'],session:['agent_id','treatment','value','unit','percent','storage','growth'],host:['load_1m','load_5m','load_15m','memory_free','disk_free','cpu_count','uptime','gpu_memory']};
 const treatmentLabel=value=>value==='Limit ?'?'Limit unknown':value;
 const colors={observed:'#3fe07a',waiting:'#5aa9ff',stale:'#9aa4b2','human-action':'#f2b90c',blocked:'#ff6161',unknown:'#9aa4b2',external:'#b388ff'};
 const replay=D.disclosure.startsWith('Recorded');
 const state={tab:1,selected:'A-01',edge:'',filter:'both',motion:true,fullscreen:false,fit:false,handoffs:true};
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const $=(q,root=document)=>root.querySelector(q),$$=(q,root=document)=>[...root.querySelectorAll(q)];
 function exact(value,keys){if(!value||Array.isArray(value)||typeof value!=='object'||Object.keys(value).sort().join('|')!==[...keys].sort().join('|'))throw Error('schema');}
 function validate(){
  const rootKeys=Object.keys(D),optional=['model_usage','workflow_graph'];
  if(allowed.root.some(k=>!rootKeys.includes(k))||rootKeys.some(k=>!allowed.root.includes(k)&&!optional.includes(k)))throw Error('schema');
  exact(D.summary,allowed.summary);exact(D.host,allowed.host);
  if(![1,2].includes(D.schema_version)||D.schema_version===1&&optional.some(k=>k in D))throw Error('schema');
  for(const [key,kind] of [['agents','agent'],['workstreams','workstream'],['edges','edge'],['activity','activity'],['sessions','session']]){if(!Array.isArray(D[key]))throw Error('schema');D[key].forEach(v=>exact(v,allowed[kind]));}
  const ids=D.agents.map(a=>a.id);
  if(ids.length!==7||new Set(ids).size!==7||ids.some(id=>!P.positions[id]))throw Error('schema');
  D.agents.forEach(a=>{if(!P.icons[a.kind]||!colors[a.status]||typeof a.working!=='boolean'||!Array.isArray(a.responsibilities))throw Error('schema');});
  if(D.sessions.length!==5||new Set(D.sessions.map(s=>s.agent_id)).size!==5)throw Error('schema');
  D.sessions.forEach(s=>{if(!ids.includes(s.agent_id)||!(s.percent===null||(Number.isFinite(s.percent)&&s.percent>=0&&s.percent<=100&&['Measured','Configured','Stale','Illustrative'].includes(s.treatment))))throw Error('schema');if(s.treatment==='Limit ?'&&s.percent!==null)throw Error('schema');});
  D.edges.forEach(e=>{if(!ids.includes(e.from)||!ids.includes(e.to))throw Error('schema');});
  D.activity.forEach(a=>{if(!ids.includes(a.actor_id))throw Error('schema');});
  if(D.model_usage&&(!D.model_usage.windows||!D.model_usage.tracked_total||!Array.isArray(D.model_usage.agents)))throw Error('schema');
  if(D.workflow_graph&&(!D.workflow_graph.manifest||!Array.isArray(D.workflow_graph.events)||!D.workflow_graph.run))throw Error('schema');
 }
 function avatar(a){const i=P.identity[a.id];return `<span class="ap-avatar" style="--identity:${i.ring};--fill:${i.fill};--ink:${i.icon}">${P.slot_icons?.[a.id]||P.icons[a.kind]}</span>`;}
 function agent(id){return D.agents.find(a=>a.id===id);}
 function node(a){
  const i=P.identity[a.id],pos=P.positions[a.id],hub=a.kind==='orchestrator',owner=a.kind==='human',record=a.kind==='record';
  const classes=['av-node',hub?'av-hub av-A-01':'',owner?'av-human av-H-01':'',a.kind==='consultant'?'av-human av-external':'',record?'av-log':'',a.working?'av-live av-pulse':''].join(' ');
  const label=owner?`<span class="av-label"><span class="av-name">${esc(a.role)}</span><span class="av-H-01-actions"><span class="owner-id">H-01</span>${a.responsibilities.map(x=>`<span>${esc(x)}</span>`).join('')}</span></span>`:`<span class="av-label"><span class="av-name">${esc(a.id)}</span><span class="av-role">${esc(a.role)}</span></span>`;
  const motion=a.working?'<span class="av-halo" aria-hidden="true"></span><span class="av-activity-arc" aria-hidden="true"></span><span class="av-task-cue"><span class="av-task-dot"></span>ON TASK</span>':'';
  return `<button type="button" class="${classes}" data-node="${a.id}" data-lane="${esc(a.workstream||'')}" aria-pressed="false" aria-label="${esc(a.id+' '+a.role+' '+a.status)}" style="--x:${pos[0]}%;--y:${pos[1]}%;--ring:${record?i.ring:colors[a.status]};--identity:${i.ring};--fill:${i.fill};--ink:${i.icon};--sweep-delay:0s">${motion}<span class="av-face">${P.slot_icons?.[a.id]||P.icons[a.kind]}</span>${a.status==='blocked'?'<span class="av-warning" aria-label="Reported blocker">!</span>':''}${label}</button>`;
 }
 function legend(){const entries=[['Observed process','observed',''],['Waiting','waiting',''],['Owner action','human-action',''],['Blocked','blocked',''],['Idle / unknown','unknown','outline'],['External','external','dashed']];return `<aside class="av-legend" aria-label="Map legend"><div class="av-legend-title">MAP KEY</div>${entries.map(([label,key,style])=>`<div class="av-key"><span class="av-dot ${style}" style="--key:${colors[key]}"></span>${label}</div>`).join('')}<div class="av-key"><span class="av-line"></span>Handoff</div><div class="av-key"><span class="av-line dashed"></span>Consultation</div></aside>`;}
 function beam(){return `<svg class="av-sweep" aria-hidden="true" viewBox="0 0 100 100" preserveAspectRatio="none"><defs><linearGradient id="av-beam-axis" x1="50%" y1="40%" x2="112%" y2="40%"><stop offset="0%" stop-color="#f7fbff" stop-opacity=".58"/><stop offset="45%" stop-color="#bce5ff" stop-opacity=".26"/><stop offset="100%" stop-color="#8dccff" stop-opacity="0"/></linearGradient><radialGradient id="av-supervision-glow" cx="50%" cy="45%" r="60%"><stop offset="0%" stop-color="#8fd0ff" stop-opacity=".18"/><stop offset="65%" stop-color="#58aefe" stop-opacity=".08"/><stop offset="100%" stop-color="#58aefe" stop-opacity="0"/></radialGradient></defs><ellipse class="av-supervision-halo" cx="50" cy="64" rx="47" ry="36" fill="url(#av-supervision-glow)"/><g class="beacon-alignment"><g class="av-beam-rotor"><path class="av-beam-falloff" d="M50 40 L112 12 Q119 40 112 68 Z"/><path class="av-beam-cone" d="M50 40 L111 19 Q117 40 111 61 Z"/><path class="av-beam-trail" d="M50 40 L103 61 Q107 75 96 81 Z"/><line class="av-beam-axis" x1="50" y1="40" x2="112" y2="40"/></g></g></svg>`;}
 function topology(){
  const standing=[['H-01','A-01'],['A-01','A-04'],['A-01','A-05'],['H-01','X-01']].map(([a,b])=>`<path class="${b==='X-01'?'consult':'standing'}" data-from="${a}" data-to="${b}" stroke="#7794b0"/>`).join('');
  const flows=D.edges.filter(e=>e.kind==='handoff'||e.kind==='review').map(e=>`<path class="av-flow" data-edge-id="${esc(e.id)}" data-from="${e.from}" data-to="${e.to}" style="stroke:${agent(e.to).workstream==='Workstream-01'?'#2bb3a0':'#d4a017'}" marker-end="url(#av-arrow)"/>`).join('');
  const active=D.edges.find(e=>e.active&&e.action),capsule=active?`<span class="av-edge-capsule" data-edge-label="${active.id}" style="--edge-color:#2bb3a0">${esc(active.action)}</span>`:'';
  const records=D.workstreams.map(w=>({id:w.record_id,kind:'record',role:'Workstream Record',status:'unknown',working:false,workstream:w.id,responsibilities:[]}));
  return `<section class="av-root"><header class="av-heading"><div><h2 class="av-title">Agent topology</h2><p class="av-subtitle">Responsibilities, observed sessions and recorded handoffs</p></div><span class="av-tag">READ ONLY</span></header><div class="av-body">${legend()}<div class="av-stage"><div class="av-orbit" data-lane="Workstream-01"></div><div class="av-orbit right" data-lane="Workstream-02"></div>${beam()}<svg class="av-edges" aria-hidden="true"><defs><marker id="av-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="context-stroke"/></marker></defs>${standing}${flows}</svg>${capsule}<div class="av-lane" data-lane="Workstream-01">Workstream-01</div><div class="av-lane right" data-lane="Workstream-02">Workstream-02</div>${[...D.agents,...records].map(node).join('')}</div></div><div class="av-selection-note" aria-live="polite">Select a participant to highlight it. Full evidence stays in Inspector.</div><footer class="av-note">Solid halo = observed process or job presence. Pulse = approved working activity. Responsibility markers remain static.</footer></section>`;
 }
 function recent(){return `<section class="ap-activity"><h2>Recent activity</h2><p class="ap-caption">Source order retained. Recorded replay ages.</p><div class="ap-events">${D.activity.length?D.activity.map((r,n)=>`<article class="ap-event"><div class="ap-event-head">${avatar(agent(r.actor_id))}<div><div class="ap-event-name">${r.actor_id}</div><div class="ap-event-meta"><span class="ap-lane">${esc(r.workstream)}</span><span class="ap-kind">${esc(r.type)}</span><time class="ap-time">${esc(r.age)}</time></div></div></div><p class="ap-event-text">${esc(r.preview)}</p><details><summary>Source details</summary><p>${esc(r.preview+'\n'+r.detail)}</p><button class="action event-open" data-event="${n}">Open in Inspector</button></details></article>`).join(''):'<p class="ap-empty">No recent activity recorded.</p>'}</div></section>`;}
 function sessions(){return `<section class="ap-context"><div class="ap-context-heading">Session context</div><div class="ap-context-grid">${D.sessions.map(s=>`<article class="ap-context-card" tabindex="0" role="button" data-session="${s.agent_id}" aria-label="Inspect ${s.agent_id} context and storage"><div class="ap-context-top"><span class="ap-context-agent">${avatar(agent(s.agent_id))}<span>${s.agent_id}</span></span><span class="ap-treatment${s.treatment==='Stale'?' ap-stale-badge':''}">${esc(treatmentLabel(s.treatment))}</span></div><div class="ap-context-value">${esc(s.value)}</div><div class="ap-track">${s.percent===null?'':`<div class="ap-fill" style="width:${s.percent}%"></div>`}</div><div class="ap-context-word">${esc(s.unit)}</div><div class="ap-context-meta ap-scratch">Session storage${s.storage==='Not measured'?' &middot;':''} <strong>${esc(s.storage)}</strong>${s.growth?`<span class="ap-growth">${esc(s.growth)}</span>`:''}</div></article>`).join('')}</div></section>`;}
 const hostEntries=[['load_1m','load avg 1m','gauge'],['load_5m','load avg 5m','gauge'],['load_15m','load avg 15m','gauge'],['memory_free','mem free','memory'],['disk_free','disk free','disk'],['cpu_count','CPU count','cpu'],['uptime','uptime','clock'],['gpu_memory','GPU mem used, total','gpu']];
 function host(){return `<div class="host-strip">${hostEntries.map(([k,label,icon])=>`<span class="hs-item">${P.host_icons[icon]}<span><span class="hs-value">${esc(D.host[k]||'Not measured')}</span><span class="hs-label">${label}</span></span></span>`).join('')}<span class="hs-observed">${replay?'Approved replay measurements':esc(D.summary.freshness)}</span></div>`;}
 function header(){return `<div class="am-header"><span class="metric"><strong class="n">${D.summary.active_agents}/${D.summary.monitored_agents}</strong><span class="k">Observed</span></span><span class="metric"><strong class="n">${D.summary.human_actions}</strong><span class="k">Owner action</span></span><span class="metric"><strong class="n">${D.summary.blockers}</strong><span class="k">Blocked</span></span><span class="fresh">${esc(D.summary.freshness)}</span></div><div class="telemetry"><strong>${replay?'Recorded snapshot':'Local snapshot'}</strong><small>${replay?'Public replay  -  ':''}${esc(D.summary.freshness)}</small></div>`;}
 function controls(){return `<div class="controls"><label><input id="fit" type="checkbox">Fit view</label><label><input id="full" type="checkbox" role="switch">Fullscreen</label><label class="filter">Workstream filter<select id="filter"><option value="both">Both workstreams</option><option>Workstream-01</option><option>Workstream-02</option></select></label><label><input id="handoffs" type="checkbox" checked>Show recent hand-offs</label><label><input id="motion" type="checkbox" aria-describedby="motion-status">Activity animation <span id="motion-status" class="motion-status" role="status" aria-live="polite"></span></label></div>`;}
 function table(head,rows){return `<div class="table-wrap"><table><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v??'Not measured')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
 function panel(title,body){return `<section class="panel"><h2>${esc(title)}</h2>${body}</section>`;}
 function shortTokens(value){if(value===null||value===undefined)return 'Unknown';if(value>=1e9)return (value/1e9).toFixed(2).replace(/0+$/,'').replace(/\.$/,'')+'B';if(value>=1e6)return (value/1e6).toFixed(1).replace(/\.0$/,'')+'M';if(value>=1e3)return (value/1e3).toFixed(1).replace(/\.0$/,'')+'k';return String(value);}
 function moneyRange(row){if(row.value_low===null||row.value_high===null)return 'Unknown';const low='$'+Number(row.value_low).toLocaleString(undefined,{maximumFractionDigits:0});const high='$'+Number(row.value_high).toLocaleString(undefined,{maximumFractionDigits:0});return row.value_low===row.value_high?low:low+' - '+high;}
 function usageTeaser(){
  if(!D.model_usage)return '';
  const u=D.model_usage,w=u.windows['7d'],input=w.input_tokens+w.cached_input_tokens,share=input?100*w.cached_input_tokens/input:0;
  return '<section class="mu-teaser"><div><span>MODEL USAGE</span><strong>'+shortTokens(w.observed_tokens)+'</strong><small>last 7 days</small></div><div><span>API-EQUIVALENT VALUE</span><strong>'+moneyRange(w)+'</strong><small>indicative only</small></div><div><span>CACHED SHARE</span><strong>'+share.toFixed(1)+'%</strong><small>of input</small></div></section>';
 }
 function usagePanel(windowKey){
  if(!D.model_usage)return panel('Model Usage & API Value','<p>Not measured</p>');
  const u=D.model_usage,key=windowKey||'7d',w=u.windows[key],input=w.input_tokens+w.cached_input_tokens,share=input?100*w.cached_input_tokens/input:0;
  const windows=['24h','7d','30d'].map(k=>'<button type="button" class="mu-window'+(k===key?' active':'')+'" data-window="'+k+'">'+k.replace('d',' d')+'</button>').join('');
  const cards=[
   ['LAST '+key.toUpperCase(),shortTokens(w.observed_tokens)+' tokens','observed usage'],
   ['TRACKED TOTAL',shortTokens(u.tracked_total.observed_tokens)+' tokens','registered history'],
   ['API-EQUIVALENT VALUE',moneyRange(w),'indicative only'],
   ['CACHED SHARE',share.toFixed(1)+'%','of input']
  ].map(r=>'<article class="mu-summary"><span>'+r[0]+'</span><strong>'+r[1]+'</strong><small>'+r[2]+'</small></article>').join('');
  const agents=u.agents.map(a=>'<article class="mu-agent"><div><strong>'+esc(a.agent_id)+'</strong><span>'+esc(a.model||'Unknown model')+'</span></div><dl><dt>7d</dt><dd>'+shortTokens(a.tokens_7d)+'</dd><dt>Tracked</dt><dd>'+shortTokens(a.tracked_tokens)+'</dd><dt>Share</dt><dd>'+(a.share_percent>0&&a.share_percent<1?'&lt;1%':Math.round(a.share_percent)+'%')+'</dd></dl><div class="mu-bar"><i style="width:'+Math.min(100,a.share_percent)+'%"></i></div><small>'+esc(a.valuation_quality)+' valuation</small></article>').join('');
  const c=u.coverage;
  const details='<details class="panel mu-details"><summary>Usage evidence and coverage</summary>'+table(['Coverage','Value'],[['Included registered sources',c.included_registered_sources],['Excluded unmapped sessions',c.excluded_unmapped_sessions],['Conflicting events excluded',c.conflicting_events_excluded],['Unknown-model events',c.unknown_model_events]])+'<p>API-equivalent values are indicative estimates calculated from reviewed public API rates. They are not subscription charges or invoices.</p></details>';
  return '<section id="usage-panel" class="mu-root"><header><div><h2>Model Usage & API Value</h2><p>Historical usage, separate from current Session Context</p></div><div class="mu-windows" aria-label="Usage window">'+windows+'</div></header><div class="mu-grid">'+cards+'</div><div class="mu-agents">'+agents+'</div><p class="mu-disclaimer">Indicative public API-equivalent value. Not subscription or billed cost.</p>'+details+'</section>';
 }
 function workflowObservation(wf,id){
  const n=wf.manifest.nodes.find(n=>n.node_id===id),events=wf.events.filter(e=>e.node_id===id),last=events[events.length-1];
  if(!n)return '';
  const paused=last?.event==='human_interrupt',status=last?.status||'Not observed';
  return '<span>NODE INSPECTION</span><strong>'+esc(n.label)+'</strong><div class="wf-state">'+esc(status)+'</div><p>'+(paused?'Waiting for lab decision. None pending for the author.':last?esc(last.event.replaceAll('_',' ')):'No event recorded for this node.')+'</p><dl><dt>Run route</dt><dd>'+esc(wf.run.selected_route||'Not recorded')+'</dd><dt>Checkpoint</dt><dd>'+(last?.checkpointed?'Saved': 'Not recorded')+'</dd><dt>Observation</dt><dd>'+esc(last?.at_utc.slice(11,19)||'Not observed')+'</dd></dl><small>Observational only / no execution controls</small>';
 }
 function workflowPanel(){
  if(!D.workflow_graph)return panel('Workflow & Trace','<p>Not configured</p>');
  const wf=D.workflow_graph,m=wf.manifest,r=wf.run,visited=new Set(r.visited),routes=new Set(r.selected_routes||[]);
  const current=m.nodes.find(n=>n.label===r.current_node)?.node_id||m.nodes[0].node_id;
  const summary=[['RUN STATE',r.state],['CURRENT NODE',r.current_node],['LAB RETRY ATTEMPTS',r.retries],['SELECTED ROUTE',r.selected_route||'None']].map(x=>'<article><span>'+x[0]+'</span><strong>'+esc(x[1])+'</strong></article>').join('');
  const edgeLabels=[];
  const edges=m.edges.map(e=>{
   const a=m.nodes.find(n=>n.node_id===e.from),b=m.nodes.find(n=>n.node_id===e.to),selected=visited.has(e.from)&&visited.has(e.to)&&(e.condition===null||routes.has(e.condition)),reverse=m.edges.some(other=>other.from===e.to&&other.to===e.from);
   const cls=selected?'selected':'possible';
   let shape,tx=(a.x+b.x)/2,ty=(a.y+b.y)/2-3;
   if(reverse){
    const lift=a.x<b.x?-48:48,ax=a.x*10,ay=a.y*3.6,bx=b.x*10,by=b.y*3.6;
    shape='<path class="'+cls+'" d="M '+ax+' '+ay+' Q '+((ax+bx)/2)+' '+((ay+by)/2+lift)+' '+bx+' '+by+'"></path>';
    ty=(a.y+b.y)/2+lift/7.2+(lift<0?-4:5);
   }else shape='<line class="'+cls+'" x1="'+a.x+'%" y1="'+a.y+'%" x2="'+b.x+'%" y2="'+b.y+'%"></line>';
   if(e.condition)edgeLabels.push('<span class="wf-edge-label '+cls+'" style="left:'+tx+'%;top:'+ty+'%">'+esc(e.condition)+'</span>');
   return shape;
  }).join('');
  const nodes=m.nodes.map(n=>'<button type="button" aria-pressed="'+(n.node_id===current)+'" class="wf-node '+(visited.has(n.node_id)?'visited ':'')+(n.node_id===current?'current':'')+'" style="--x:'+n.x+'%;--y:'+n.y+'%" data-workflow-node="'+n.node_id+'"><small>'+esc(n.kind.replace('_',' '))+'</small><span>'+esc(n.label)+'</span></button>').join('');
  const timeline=r.timeline.map((t,i)=>{const tone=t.event.includes('human')?'human':t.event.includes('retry')?'retry':t.event.includes('route')?'route':'task';return '<li class="wf-event-'+tone+'"><b>'+String(i+1).padStart(2,'0')+'</b><strong>'+esc(t.node)+'</strong><time>'+esc(t.at.slice(11,19))+'</time><span>'+esc(t.event)+(wf.events[i]?.route?' / '+esc(wf.events[i].route):'')+(t.attempt?' / attempt '+t.attempt:'')+(wf.events[i]?.checkpointed?' / checkpoint saved':'')+'</span></li>';}).join('');
  const legend=[['Node','one workflow step'],['Parallel branches','fan-out'],['Join','branches converge'],['Conditional route','accept / revise'],['Human gate','interrupt + checkpoint'],['Semantic trace','ordered observations']].map(x=>'<div><strong>'+x[0]+'</strong><span>'+x[1]+'</span></div>').join('');
  const raw='<details class="panel wf-raw"><summary>Raw normalized events</summary><pre>'+esc(JSON.stringify(wf.events,null,2))+'</pre></details>';
  return '<section class="wf-root"><header><div><span class="wf-badge">SYNTHETIC LAB</span><h2>Workflow & Trace</h2><p>Illustrates graph-style workflow mechanics. Synthetic example, not a real user/project workflow.</p></div><span class="wf-readonly">OBSERVATIONAL ONLY</span></header><div class="wf-summary">'+summary+'</div><div class="wf-layout"><div class="wf-graph"><svg viewBox="0 0 1000 360" preserveAspectRatio="none" aria-hidden="true">'+edges+'</svg>'+edgeLabels.join('')+nodes+'<div class="wf-graph-key">Solid: selected route <span>Dashed: other paths</span></div></div><aside class="wf-inspector" aria-live="polite">'+workflowObservation(wf,current)+'</aside></div><div class="wf-mapping" aria-label="Graph-style workflow concepts">'+legend+'</div><section class="wf-timeline"><h3>Semantic timeline <small>Recorded sequence / UTC</small></h3><ol>'+timeline+'</ol></section>'+raw+'</section>';
 }
 function eventsTable(){return table(['Actor','Workstream','Type',replay?'Recorded age':'Source age','Activity'],D.activity.map(r=>[r.actor_id,r.workstream,r.type,r.age,r.preview]));}
 function observedTable(){return table(['Agent','Role','Workstream','Status','Working'],D.agents.filter(a=>a.id.startsWith('A')).map(a=>[a.id,a.role,a.workstream||'Both',a.status,a.working?'Observed':'No approved activity']));}
 function workstreams(){return `<div class="two-col">${D.workstreams.map(w=>panel(w.id,`<p><span class="badge">${esc(w.status)}</span></p><p>Record: <strong>${w.record_id}</strong></p><p class="muted">Stage: Not measured</p>${table(['Agent','Role','Status'],D.agents.filter(a=>a.workstream===w.id).map(a=>[a.id,a.role,a.status]))}<details><summary>${replay?'Recorded':'Source'} activity</summary>${table(['Actor','Entry'],D.activity.filter(a=>a.workstream===w.id).map(a=>[a.actor_id,a.detail]))}</details>`)).join('')}</div>`;}
 function inspectorShell(){return `<div class="inspector-controls"><label>Participant<select id="participant">${D.agents.map(a=>`<option value="${a.id}">${esc(a.id+'  -  '+a.role)}</option>`).join('')}</select></label><label>Edge<select id="edge-select"><option value="">No edge selected</option>${D.edges.map(e=>`<option value="${e.id}">${e.from} -> ${e.to}</option>`).join('')}</select></label></div><div id="inspector-main"></div><div id="inspector-event"></div><details class="panel"><summary>Roster</summary><label><input id="running-first" type="checkbox"> Running first</label><div id="roster"></div></details><details class="panel"><summary>Recent hand-offs</summary>${eventsTable()}</details><details class="panel"><summary>Evidence and rules</summary><p>Observed activity and recorded workflow state are independent. Unknown measured limits never become percentages. Illustrative percentages are display examples only. Missing measurements remain Not measured.</p></details>`;}
 function renderInspector(){const a=agent(state.selected)||agent('A-01'),s=D.sessions.find(x=>x.agent_id===a.id),e=D.edges.find(x=>x.id===state.edge);
  $('#participant').value=a.id;$('#edge-select').value=state.edge;
  const facts=[['Identity',a.id],['Role',a.role],['Status',a.status],['Workstream',a.workstream||'Across workstreams'],['Working activity',a.working?'Approved observed activity':'Not measured'],['Context',s?s.value:'Not measured'],['Context limit',s?.treatment==='Illustrative'?'Not verified (illustrative percentage)':s?.percent!==null&&s?'Approved for recorded percentage':'Not verified'],['Session storage',s?.storage||'Not measured'],['24 h growth','Not measured'],['3 day growth',s?.growth||'Not measured'],['Measurement age',s?.treatment==='Illustrative'?'Not sampled':D.summary.freshness]];
  $('#inspector-main').innerHTML=panel(a.id+'  -  '+a.role,`<table class="facts">${facts.map(([k,v])=>`<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join('')}</table><details><summary>Context evidence</summary><p>${s?.treatment==='Illustrative'?'Illustrative display value only; not an observed context measurement. Effective limit not verified.':esc(treatmentLabel(s?.treatment||'Not measured'))+(replay?'. Values are retained from the approved replay.':'. Values come from the configured local snapshot.')}</p></details>`)+(e?panel('Selected edge',table(['From','To','Type','Action'],[[e.from,e.to,e.kind,e.action||'Standing relationship']])):'');
  renderRoster();
 }
 function renderRoster(){const rows=[...D.agents];if($('#running-first')?.checked)rows.sort((a,b)=>Number(b.working)-Number(a.working));$('#roster').innerHTML=table(['Agent','Role','Status'],rows.map(a=>[a.id,a.role,a.status]));}
 function switchTab(n){state.tab=n;$$('[role=tab]').forEach((b,i)=>{b.setAttribute('aria-selected',String(i===n));b.tabIndex=i===n?0:-1;});$$('[role=tabpanel]').forEach((v,i)=>v.hidden=i!==n);if(n===2)renderInspector();if(n===1)requestAnimationFrame(redraw);}
 let redraw=()=>{};
 try{
  validate();
  $('#tabs').innerHTML=names.map((name,i)=>`<button role="tab" id="tab-${i}" aria-controls="view-${i}" aria-selected="${i===1}" tabindex="${i===1?0:-1}" data-tab="${i}"><p>${name}</p></button>`).join('');
  const overview=`<h2 class="section-title">At a glance</h2><div class="six-col">${[['Workstream-01','Unknown'],['Workstream-02','Unknown'],['Owner action',D.summary.human_actions],['Observed sessions',D.summary.active_agents+'/'+D.summary.monitored_agents],['Usage history',D.model_usage?shortTokens(D.model_usage.windows['7d'].observed_tokens):'Not measured'],['Blockers',D.summary.blockers]].map(([k,v])=>`<section class="panel"><span class="muted">${k}</span><div class="big">${v}</div></section>`).join('')}</div>${usageTeaser()}<h2 class="section-title">Workstream summaries</h2>${workstreams()}${panel('Next actions',eventsTable())}`;
  const content=[header()+overview,header()+controls()+`<div class="map-panels">${topology()}${recent()}</div>`+sessions()+host(),inspectorShell(),header()+panel(replay?'Last hand-offs per workstream (RECORDED)':'Last hand-offs per workstream',eventsTable())+panel('Observed activity per agent',observedTable()),header()+workstreams()+panel('Waiting on owner',table(['Actor','Request'],D.activity.filter(r=>r.type==='decision').map(r=>[r.actor_id,r.detail]))),header()+panel('Observed sessions',observedTable())+panel('Host',host())+sessions()+panel('Context and storage measurements',table(['Agent','Value','Treatment','Session storage','Growth'],D.sessions.map(s=>[s.agent_id,s.value,treatmentLabel(s.treatment),s.storage,s.growth||'Not measured'])))+usagePanel(),header()+panel(replay?'Last recorded entries per workstream':'Last source entries per workstream',eventsTable())+panel(replay?'Replay diagnostics':'Local diagnostics',table(['Check','State'],[['Data',replay?'Approved static snapshot':'Configured local snapshot'],['Collection',replay?'Recorded replay':'Local observation'],['Network connection','None'],['Live error measurement','Not measured']]))+`<details class="panel"><summary>Public snapshot details</summary><pre>${esc(JSON.stringify(D,null,2))}</pre></details>`,header()+workflowPanel()];
  $('#views').innerHTML=content.map((c,i)=>`<section role="tabpanel" id="view-${i}" aria-labelledby="tab-${i}" ${i===1?'':'hidden'}>${c}</section>`).join('');
  const root=$('.av-root'),stage=$('.av-stage'),rotor=$('.av-beam-rotor');
  document.documentElement.style.setProperty('--map-height',P.normal_height+'px');
  redraw=window.installGeometry(root);
  rotor.style.transformOrigin='0 0';rotor.style.transformBox='view-box';
  function alignBeacon(){const b=$('.av-lighthouse-beacon').getBoundingClientRect(),s=stage.getBoundingClientRect();if(s.height>0){const x=(b.left+b.width/2-s.left)/s.width*100,y=(b.top+b.height/2-s.top)/s.height*100;$('.beacon-alignment').setAttribute('transform',`translate(${x-50} ${y-40})`);}}
  new ResizeObserver(alignBeacon).observe(stage);
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let motionChoice=null;
  function applyMotion(){
   state.motion=motionChoice===null?!reduced.matches:motionChoice;
   const explicitMotion=reduced.matches&&motionChoice===true;
   root.classList.toggle('av-paused',!state.motion);
   root.classList.toggle('motion-static',reduced.matches&&!explicitMotion);
   root.classList.toggle('motion-override',explicitMotion);
   $('#motion').checked=state.motion;
   $('#motion-status').textContent=state.motion?'Running':(reduced.matches&&motionChoice===null?'Reduced motion':'Paused');
   $('#motion-status').dataset.state=state.motion?'running':'static';
   $('#motion').title=reduced.matches&&!explicitMotion?'Your browser requests reduced motion. Select Activity animation to enable motion for this preview.':'Pause or resume motion for this preview.';
  }
  reduced.addEventListener('change',applyMotion);applyMotion();
  let last=null,elapsed=0;
  function animate(now){if(last!==null&&state.motion&&state.tab===1)elapsed+=Math.min(now-last,100);last=now;const angle=elapsed/12000*360;rotor.setAttribute('transform',`rotate(${angle%360} 50 40)`);rotor.dataset.angle=String(angle);requestAnimationFrame(animate);}
  requestAnimationFrame(animate);
 if(!replay){$('.replay-badge').textContent='LOCAL OBSERVATION';$$('.ap-caption').forEach(n=>n.textContent='Source order retained. Source-provided ages.');}
  function selection(id){state.selected=id;$$('.av-node').forEach(n=>n.setAttribute('aria-pressed',String(n.dataset.node===id)));const a=agent(id);$('.av-selection-note').textContent=a?`${a.id}  -  ${a.role}  -  ${a.status}. Open Inspector for details.`:`${id}  -  Workstream Record`;}
  $$('[data-tab]').forEach(b=>b.addEventListener('click',()=>switchTab(Number(b.dataset.tab))));
  $('#tabs').addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?names.length-1:(state.tab+(e.key==='ArrowRight'?1:names.length-1))%names.length;switchTab(n);$('#tab-'+n).focus();}});
  function wireUsage(){$$('.mu-window').forEach(b=>b.addEventListener('click',()=>{const root=$('#usage-panel');if(root){root.outerHTML=usagePanel(b.dataset.window);wireUsage();}}));}wireUsage();
  $$('[data-workflow-node]').forEach(n=>n.addEventListener('click',()=>{$('.wf-inspector').innerHTML=workflowObservation(D.workflow_graph,n.dataset.workflowNode);$$('[data-workflow-node]').forEach(b=>b.setAttribute('aria-pressed',String(b===n)));}));
  $$('.av-node').forEach(n=>n.addEventListener('click',()=>selection(n.dataset.node)));
  $$('[data-session]').forEach(n=>{const open=()=>{state.selected=n.dataset.session;switchTab(2);};n.addEventListener('click',open);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}});});
  $$('[data-event]').forEach(b=>b.addEventListener('click',()=>{const r=D.activity[Number(b.dataset.event)];state.selected=r.actor_id;switchTab(2);$('#inspector-event').innerHTML=panel('Complete recorded entry',`<p class="detail-text">${esc(r.preview+'\n'+r.detail)}</p>`);}));
  $('#participant').addEventListener('change',e=>{selection(e.target.value);renderInspector();});$('#edge-select').addEventListener('change',e=>{state.edge=e.target.value;$$('.av-flow').forEach(p=>p.classList.toggle('selected-edge',p.dataset.edgeId===state.edge));renderInspector();});$('#running-first').addEventListener('change',renderRoster);
  function size(){document.documentElement.style.setProperty('--map-height',(state.fit||state.fullscreen?P.fit_height:P.normal_height)+'px');document.body.classList.toggle('fullscreen',state.fullscreen);requestAnimationFrame(()=>{redraw();alignBeacon();});}
  $('#fit').addEventListener('change',e=>{state.fit=e.target.checked;size();});$('#full').addEventListener('change',e=>{state.fullscreen=e.target.checked;size();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.fullscreen){state.fullscreen=false;$('#full').checked=false;size();}});
  $('#motion').addEventListener('change',e=>{motionChoice=e.target.checked;applyMotion();});
  $('#filter').addEventListener('change',e=>{state.filter=e.target.value;$$('[data-lane]',root).forEach(n=>n.classList.toggle('av-dim',state.filter!=='both'&&n.dataset.lane!==''&&n.dataset.lane!==state.filter));$$('.av-flow').forEach(p=>{const to=agent(p.dataset.to);p.style.opacity=state.filter!=='both'&&to.workstream!==state.filter?'.2':'.92';});});
  $('#handoffs').addEventListener('change',e=>{state.handoffs=e.target.checked;$$('.av-flow,.av-edge-capsule').forEach(n=>n.style.display=state.handoffs?'':'none');});
 }catch(_error){$('#views').replaceChildren();$('#tabs').replaceChildren();$('#safe-error').hidden=false;}
})();
