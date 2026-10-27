import {aggregate, groupCompare, rate, filterMetrics, escapeHTML as esc} from './metrics.js';
let data, page='policy';
const $=id=>document.getElementById(id);
const fmt=(n,d=0)=>n==null?'Unavailable':Number(n).toLocaleString('en-US',{maximumFractionDigits:d});
const pct=n=>n==null?'Unavailable':fmt(n*100,1)+'%';
const delta=n=>n==null?'Unavailable':(n>0?'+':'')+fmt(n,1)+' pp';
const empty=(title,detail)=>`<div class="empty"><span class="symbol" aria-hidden="true">◷</span><strong>${esc(title)}</strong><p>${esc(detail)}</p></div>`;
const kpi=(label,value,note)=>`<div class="kpi"><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div><div class="note">${esc(note)}</div></div>`;
const panel=(title,note,body)=>`<section class="panel"><h3>${esc(title)}</h3><p class="sub">${esc(note)}</p>${body}</section>`;
const title=(name,description,badge)=>`<div class="page-title"><div><h2>${name}</h2><p>${description}</p></div><span class="badge">${badge}</span></div>`;
const table=(heads,rows)=>`<div class="table-wrap"><table><thead><tr>${heads.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
function filters(){return Object.fromEntries(['month','borough','agency','service','district'].map(x=>[x,$(x).value]));}
function options(id,values){const select=$(id),old=select.value;select.replaceChildren(select.options[0]);for(const v of [...new Set(values.filter(Boolean))].sort()){const o=document.createElement('option');o.value=v;o.textContent=v;select.append(o);}select.value=[...select.options].some(o=>o.value===old)?old:'';}
function pairedBars(groups,metric='closure_30d_rate',isRate=true){
 if(!groups.length)return empty('Comparison unavailable','Load complete 311 records for the study and baseline years.');
 const values=groups.flatMap(r=>[r.study[metric],r.baseline[metric]]).filter(x=>x!=null),max=isRate?1:Math.max(...values,1);
 return '<div class="legend"><span><i></i>Study</span><span><i class="baseline"></i>Baseline</span></div><div class="bars">'+groups.map(r=>`<div class="bar-row"><div class="bar-label">${esc(r.label)}</div><div class="bar-pair">${['study','baseline'].map(p=>{let n=r[p][metric];return `<div class="bar-line"><div class="bar ${p==='baseline'?'baseline':''}" style="width:${n==null?0:Math.max(0,n/max*75)}%"></div><span>${isRate?pct(n):fmt(n)}</span></div>`;}).join('')}</div></div>`).join('')+'</div>';
}
function trend(rows){
 if(!rows.length)return empty('Monthly trend unavailable','Both years will appear on the same seasonal axis after data is loaded.');
 const groups=groupCompare(rows,r=>String((Number(r.month.slice(5))+2)%12).padStart(2,'0'));
 const months=['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep'];
 const w=620,h=250,left=50,right=20,top=20,bottom=40;
 const max=Math.max(1,...groups.flatMap(g=>[g.study.requests,g.baseline.requests]));
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Monthly request volume, study compared with baseline">`;
 for(let i=0;i<=4;i++){let y=top+(h-top-bottom)*i/4;svg+=`<line class="axis" x1="${left}" x2="${w-right}" y1="${y}" y2="${y}"/><text x="${left-8}" y="${y+4}" text-anchor="end">${fmt(max*(1-i/4))}</text>`;}
 for(const period of ['baseline','study']){
   let path='',last=-2;
   groups.sort((a,b)=>a.label.localeCompare(b.label)).forEach(g=>{const i=Number(g.label),x=left+i*(w-left-right)/11,y=h-bottom-g[period].requests/max*(h-top-bottom);if(g[period].requests){path+=(last===i-1?' L':' M')+x+','+y;last=i;svg+=`<circle cx="${x}" cy="${y}" r="3" fill="${period==='study'?'#007b73':'#5c7a96'}"><title>${period} ${months[i]}: ${fmt(g[period].requests)} requests</title></circle>`;}});
   svg+=`<path d="${path}" fill="none" stroke="${period==='study'?'#007b73':'#5c7a96'}" stroke-width="2"/>`;
 }
 months.forEach((m,i)=>svg+=`<text x="${left+i*(w-left-right)/11}" y="${h-12}" text-anchor="middle">${m}</text>`);
 return '<div class="legend"><span><i></i>Study</span><span><i class="baseline"></i>Baseline</span></div>'+svg+'</svg>';
}
function scopedPolicies(f){
 const linkedIds=f.service?new Set(data.policy_links.filter(l=>l.service===f.service&&(!f.agency||l.agency===f.agency)).map(l=>l.policy_id)):null;
 return data.policies.filter(p=>(!f.agency||p.agency===f.agency)&&(!linkedIds||linkedIds.has(p.policy_id))&&(!f.month||data.policy_evidence.some(e=>e.policy_id===p.policy_id&&e.event_date.startsWith(f.month))));
}
function policyView(rows,f){
 const policies=scopedPolicies(f),verified=policies.filter(p=>p.verified_status==='implementation_verified');
 const known=policies.length>0;
 let html=title('Policy responsiveness','Documented municipal initiatives, their public-service alignment, and the evidence for implementation.','Research question 01');
 html+='<div class="kpis">'+kpi('Verified policy registry',known?fmt(policies.length):'Unavailable','Reviewed records with a study-year policy event')+kpi('Implementation verified',known?fmt(verified.length):'Unavailable','Requires delivery evidence; enactment alone is insufficient')+kpi('Policy domains represented',known?fmt(new Set(policies.map(p=>p.domain)).size):'Unavailable','Breadth within the reviewed inventory')+kpi('Explicit service links',known?fmt(data.policy_links.filter(l=>policies.some(p=>p.policy_id===l.policy_id)).length):'Unavailable','Reviewed topical links; not effect estimates')+'</div>';
 const domainGroups=[...new Set(policies.map(p=>p.domain))].sort().map(d=>({label:d,study:{requests:policies.filter(p=>p.domain===d).length},baseline:{requests:0}}));
 let domains=domainGroups.length?'<div class="bars">'+domainGroups.map(g=>`<div class="bar-row"><div class="bar-label">${esc(g.label.replaceAll('_',' '))}</div><div class="bar-line"><div class="bar" style="width:${g.study.requests/Math.max(...domainGroups.map(x=>x.study.requests))*75}%"></div><span>${g.study.requests}</span></div></div>`).join('')+'</div>':empty('Policy inventory awaits verified sources','Legislative introductions and announcements enter a review queue. They become registry records only with official evidence and an explicit reviewer.');
 html+='<div class="grid">'+panel('Policy coverage by domain','Registry coverage does not establish completeness of all NYC initiatives.',domains)+panel('Reported service demand','Seasonally matched request volume. Borough and district filters apply to 311 records.',trend(rows))+'</div>';
 html+=panel('Policy registry','Geographic filters do not change this citywide registry. Month filters select policy evidence events; service filters use explicit reviewed links.',policies.length?table(['Initiative','Domain / agency','Verified stage','Evidence date'],policies.map(p=>`<tr><td><button data-policy="${esc(p.policy_id)}">${esc(p.title)}</button></td><td>${esc(p.domain)}<small>${esc(p.agency)}</small></td><td><span class="pill ${esc(p.verified_status)}">${esc(p.verified_status.replaceAll('_',' '))}</span></td><td>${esc(p.evidence_date)}</td></tr>`)):empty('No verified policies in this scope','Source access and registry review are required; this is not evidence that no policies exist.'));
 if(policies.length){
  const coverage=policies.map(p=>{const links=data.policy_links.filter(l=>l.policy_id===p.policy_id);const r=rows.filter(r=>links.some(l=>l.agency===r.agency&&l.service===r.service));return {p,study:aggregate(r.filter(r=>r.period==='study')),baseline:aggregate(r.filter(r=>r.period==='baseline')),links};});
  html+=panel('Policy-to-need alignment','Each row includes each linked request group once. Rows may overlap across policies and must not be summed.',table(['Initiative','Study requests','Baseline requests','30-day closure: study / baseline'],coverage.map(c=>`<tr><td>${esc(c.p.title)}<small>${c.links.length} reviewed links</small></td><td>${c.links.length?fmt(c.study.requests):'Unmapped'}</td><td>${c.links.length?fmt(c.baseline.requests):'Unmapped'}</td><td>${pct(c.study.closure_30d_rate)} / ${pct(c.baseline.closure_30d_rate)}</td></tr>`)));
 }
 return html;
}
function equityView(rows,f){
 const s=aggregate(rows.filter(r=>r.period==='study')),b=aggregate(rows.filter(r=>r.period==='baseline'));
 const groups=groupCompare(rows,r=>r.borough+' / '+r.community_district).sort((a,b)=>(a.study.closure_30d_rate??2)-(b.study.closure_30d_rate??2));
 const defined=groups.map(g=>g.study.closure_30d_rate).filter(x=>x!=null);
 let html=title('Neighborhood equity','Compare administrative closure performance within the same agency and service. Reported demand also reflects access to reporting.','Research question 02');
 html+='<div class="kpis">'+kpi('Study requests',rows.length?fmt(s.requests):'Unavailable','Full selected request cohort')+kpi('Closed within 30 days',pct(s.closure_30d_rate),'Matched mature cohort; baseline '+pct(b.closure_30d_rate))+kpi('Closure-rate change',s.closure_30d_rate!=null&&b.closure_30d_rate!=null?delta(100*(s.closure_30d_rate-b.closure_30d_rate)):'Unavailable','Percentage points versus matched baseline')+kpi('District rate range',defined.length>1?fmt((Math.max(...defined)-Math.min(...defined))*100,1)+' pp':'Unavailable','Unadjusted range; sensitive to service mix and small counts')+'</div>';
 html+='<div class="grid">'+panel('Community-district closure rates','Lowest observed study rates shown first, up to 12 districts. Mixed-service comparisons are descriptive.',pairedBars(groups.slice(0,12)))+panel('Borough demand and socioeconomic context','2024 ACS five-year estimates are borough context. Rates use the same population vintage for both years.',boroughContext(rows,f))+'</div>';
 html+=panel('Neighborhood comparison','Use counts to assess small samples. A missing comparison is not a zero rate.',groups.length?table(['Borough / district','Requests: study / baseline','Eligible: study / baseline','30-day rate: study / baseline','Change'],groups.map(g=>`<tr><td>${esc(g.label)}</td><td>${fmt(g.study.requests)} / ${fmt(g.baseline.requests)}</td><td>${fmt(g.study.eligible_30d)} / ${fmt(g.baseline.eligible_30d)}</td><td>${pct(g.study.closure_30d_rate)} / ${pct(g.baseline.closure_30d_rate)}</td><td>${g.study.closure_30d_rate!=null&&g.baseline.closure_30d_rate!=null?delta((g.study.closure_30d_rate-g.baseline.closure_30d_rate)*100):'Unavailable'}</td></tr>`)):empty('Neighborhood comparisons unavailable','Load both 311 years. Unknown district assignments will remain visible rather than being discarded.'));
 return html;
}
function boroughContext(rows,f){
 if(f.district)return empty('Borough context suppressed','A district filter cannot use a borough population as its neighborhood denominator. Clear the district filter to inspect borough context.');
 const soc=data.socioeconomic.filter(r=>!f.borough||r.borough===f.borough);
 if(!soc.length)return empty('Socioeconomic context unavailable','The ACS connector requests population, poverty counts and median household income for all five NYC boroughs.');
 const g=groupCompare(rows,r=>r.borough);
 return table(['Borough','Requests per 1,000: study / baseline','Poverty share','Median income'],soc.map(s=>{const v=g.find(g=>g.label===s.borough);return `<tr><td>${esc(s.borough)}<small>${esc(s.vintage)}</small></td><td>${v&&s.population?fmt(v.study.requests/s.population*1000,1)+' / '+fmt(v.baseline.requests/s.population*1000,1):'Unavailable'}</td><td>${pct(rate(s.poverty_count,s.poverty_universe))}</td><td>${s.median_household_income!=null?'$'+fmt(s.median_household_income):'Unavailable'}</td></tr>`;}));
}
function priorityView(rows){
 let html=title('Operational priorities','Identify agency–service–district combinations for investigation, with an explicit comparison and sample-size gate.','Investigation queue');
 html+='<div class="toolbar"><label>Minimum eligible per period<input id="min-n" type="number" value="30" min="1" max="100000"></label><label>Decline threshold (pp)<input id="threshold" type="number" value="10" min="0" max="100"></label><label>Show<select id="queue-scope"><option value="all">All combinations</option><option value="flagged">Flagged only</option></select></label><input class="search" id="search" placeholder="Find agency, service or district" aria-label="Search operational combinations"><button class="quiet" id="export-queue">Export filtered queue</button></div><div id="queue"></div>';
 html+=panel('Agency performance context','Fiscal-year MMR and agency indicators retain their actual periods and units; they are not study-year outcomes.',data.agency_performance.length?table(['Agency / indicator','Period','Value','Source'],data.agency_performance.filter(r=>!$('agency').value||r.agency===$('agency').value).map(r=>`<tr><td>${esc(r.agency)}<small>${esc(r.indicator)}</small></td><td>${esc(r.period_start)} – ${esc(r.period_end)} (exclusive)</td><td>${fmt(r.value,2)} ${esc(r.unit)}</td><td><a href="${esc(r.source_url)}" target="_blank" rel="noopener">Official record</a></td></tr>`)):empty('Agency indicators await source verification','The import contract preserves indicator identity, fiscal period, units, direction, and the official evidence quotation.'));
 return html;
}
let queueRows=[];
function updateQueue(rows){
 const min=Math.max(1,Number($('min-n').value)||30),threshold=Math.max(0,Number($('threshold').value)||0),search=$('search').value.toLowerCase();
 const groups=groupCompare(rows,r=>[r.agency,r.service,r.borough,r.community_district].join(' · '));
 queueRows=groups.filter(g=>g.study.requests>0).map(g=>{const change=g.study.closure_30d_rate!=null&&g.baseline.closure_30d_rate!=null?(g.study.closure_30d_rate-g.baseline.closure_30d_rate)*100:null;const enough=data.source_status['311']==='complete'&&g.study.eligible_30d>=min&&g.baseline.eligible_30d>=min;return {...g,change,flag:enough?(change!=null&&change<=-threshold?'review':'no threshold flag'):'insufficient coverage'};}).filter(g=>(!search||g.label.toLowerCase().includes(search))&&($('queue-scope').value!=='flagged'||g.flag==='review')).sort((a,b)=>(a.flag!=='review')-(b.flag!=='review')||(a.change??Infinity)-(b.change??Infinity));
 $('queue').innerHTML=panel('Investigation queue',`A flag requires a decline of at least ${threshold} percentage points and ${min} eligible requests in each period. No adjustment for multiple comparisons.`,queueRows.length?table(['Agency · service · borough · district','Requests: study / baseline','30-day rate: study / baseline','Change','Review status'],queueRows.map((g,i)=>`<tr><td><button data-priority="${i}">${esc(g.label)}</button></td><td>${fmt(g.study.requests)} / ${fmt(g.baseline.requests)}</td><td>${pct(g.study.closure_30d_rate)} / ${pct(g.baseline.closure_30d_rate)}</td><td>${delta(g.change)}</td><td><span class="pill ${g.flag==='review'?'review':''}">${esc(g.flag)}</span></td></tr>`)):empty('No combinations available in this scope','No operational ranking is produced from missing or synthetic observations.'));
 document.querySelectorAll('[data-priority]').forEach(el=>el.onclick=()=>{const g=queueRows[Number(el.dataset.priority)];openDetail(`<h2>${esc(g.label)}</h2><p>Next investigation: inspect request categorization, closure practices, service mix, staffing, repeated reports, missing geography, and corroborating agency records.</p><pre>${esc(JSON.stringify(g,null,2))}</pre>`);});
}
function openDetail(html){$('detail-content').innerHTML=html;$('detail').showModal();}
function render(){
 const f=filters(),rows=filterMetrics(data.metrics,f);
 $('scope').textContent=`Study: ${f.month||'October 2025–September 2026'} · Baseline: ${f.month?String(Number(f.month.slice(0,4))-1)+f.month.slice(4):'October 2024–September 2025'} · As of: ${data.as_of} · ${data.metric_backend}`;
 $('content').innerHTML=page==='policy'?policyView(rows,f):page==='equity'?equityView(rows,f):priorityView(rows);
 if(page==='priorities'){
  updateQueue(rows);for(const id of ['min-n','threshold','queue-scope','search'])$(id).oninput=()=>updateQueue(rows);
  $('export-queue').onclick=()=>downloadJSON(queueRows,'operational-priorities.json');
 }
 document.querySelectorAll('[data-policy]').forEach(el=>el.onclick=()=>{const p=data.policies.find(p=>p.policy_id===el.dataset.policy);const e=data.policy_evidence.filter(e=>e.policy_id===p.policy_id);openDetail(`<h2>${esc(p.title)}</h2><p>${esc(p.domain)} · ${esc(p.agency)}</p>`+e.map(r=>`<h3>${esc(r.evidence_type.replaceAll('_',' '))} · ${esc(r.event_date)}</h3><blockquote>${esc(r.evidence_quote)}</blockquote><p>Reviewed by ${esc(r.reviewer)} · <a href="${esc(r.source_url)}" target="_blank" rel="noopener">Official evidence</a></p>`).join(''));});
}
function downloadJSON(value,name){const u=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download=name;a.click();URL.revokeObjectURL(u);}
async function load(){
 try{
  const backend=$('backend').value;const response=await fetch('/api/dashboard'+(backend==='cube'?'?source=cube':''));if(!response.ok)throw Error('source unavailable');data=await response.json();
  $('status').className=data.readiness==='source_backed'?'ready':'';
  $('status').textContent=data.readiness==='source_backed'?'311 extraction complete. Policy inventory and agency evidence coverage must still be assessed separately.':'Source coverage incomplete — research results are unavailable or partial. Cube deployment, official-source access, and policy verification remain prerequisites.';
  options('month',data.metrics.filter(r=>r.period==='study').map(r=>r.month));
  options('borough',data.metrics.map(r=>r.borough));options('agency',[...data.metrics.map(r=>r.agency),...data.policies.map(p=>p.agency)]);
  options('service',data.metrics.map(r=>r.service));options('district',data.metrics.map(r=>r.community_district));
  $('sources').innerHTML=`<p>311: ${esc(data.source_status['311'])} · ACS: ${esc(data.source_status.acs)} · Legislative candidates: ${esc(data.source_status.legislation_candidates)}</p><p>30-day closure = closed within 720 elapsed hours ÷ eligible requests. Both periods use the study counterpart’s maturity. Invalid negative closure durations are excluded from that rate and retained in quality counts. Aggregate percentiles are deliberately unavailable.</p><ul>${data.limitations.map(l=>`<li>${esc(l)}</li>`).join('')}</ul><p>${data.artifacts.length} archived source responses. Download evidence for exact URLs, extraction runs, and SHA-256 hashes.</p>`;
  $('download').href='/api/dashboard'+(backend==='cube'?'?source=cube':'');render();
 }catch(e){$('status').textContent='Selected data source unavailable. Configure the Cube REST endpoint and server-side token, or generate a local export.';$('content').innerHTML=empty('Data source unavailable','No observations are displayed. Select a working source after resolving access.');}
}
for(const id of ['month','borough','agency','service','district'])$(id).onchange=()=>{if(data)render();};
$('backend').onchange=load;$('reset').onclick=()=>{for(const id of ['month','borough','agency','service','district'])$(id).value='';if(data)render();};
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{page=b.dataset.page;document.querySelectorAll('nav button').forEach(el=>el.removeAttribute('aria-current'));b.setAttribute('aria-current','page');if(data)render();});
$('close').onclick=()=>$('detail').close();load();
