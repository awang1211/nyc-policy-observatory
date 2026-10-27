// Run against the local server. Synthetic responses are intercepted in-browser only.
const fs=require('fs'),path=require('path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8000');await page.locator('.page-title').waitFor();
 for(const name of ['policy','equity','priorities']){
  await page.locator(`[data-page="${name}"]`).click();await page.locator('.page-title').waitFor();
  if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw Error('Desktop overflow');
  checks.push('Live empty-source page: '+name);
 }
 await page.selectOption('#backend','cube');await page.getByText('Data source unavailable',{exact:true}).waitFor();
 checks.push('Missing Cube binding produces explicit source error');
 await page.selectOption('#backend','local');await page.locator('.page-title').waitFor();
 await page.locator('[data-page="policy"]').click();
 await page.screenshot({path:path.resolve(__dirname,'../reports/dashboard.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.reload();await page.locator('.page-title').waitFor();
 if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw Error('Mobile overflow');
 checks.push('390px mobile layout without horizontal overflow');
 const snapshot=await (await page.request.get('http://127.0.0.1:8000/api/dashboard')).json();
 const metric=(period,borough,closed)=>({period,month:period==='study'?'2026-01':'2025-01',agency:'TEST',service:'Synthetic fixture',borough,community_district:'01 '+borough,requests:100,eligible_30d:100,closed_30d:closed,unresolved_asof:100-closed,invalid_closure:0,closed_observed:closed,closed_hours_sum:closed*24});
 snapshot.metrics=[metric('study','QUEENS',60),metric('baseline','QUEENS',90),metric('study','BRONX',90),metric('baseline','BRONX',80)];
 snapshot.source_status['311']='complete';snapshot.readiness='source_backed';
 snapshot.policies=[{policy_id:'test:1',title:'Synthetic fixture initiative',domain:'housing',agency:'TEST',verified_status:'announced',evidence_date:'2026-01-01'}];
 snapshot.policy_evidence=[{policy_id:'test:1',evidence_type:'announced',event_date:'2026-01-01',evidence_quote:'Synthetic test quotation, not official research evidence.',reviewer:'unit-test',source_url:'https://www.nyc.gov/synthetic-fixture'}];
 snapshot.policy_links=[{policy_id:'test:1',agency:'TEST',service:'Synthetic fixture'}];
 await page.route('**/api/dashboard',route=>route.fulfill({json:snapshot}));
 await page.setViewportSize({width:1440,height:1000});await page.reload();await page.locator('[data-policy]').waitFor();
 await page.locator('[data-policy]').click();await page.locator('dialog[open]').waitFor();await page.locator('#close').click();
 checks.push('Synthetic fixture: evidence drilldown opens and closes');
 await page.selectOption('#month','2026-01');await page.selectOption('#borough','QUEENS');
 await page.locator('[data-page="equity"]').click();
 if(!(await page.locator('.kpis').innerText()).includes('60%'))throw Error('Filtered closure rate incorrect');
 if(!(await page.locator('#scope').innerText()).includes('2025-01'))throw Error('Seasonal baseline label incorrect');
 checks.push('Synthetic fixture: filters retain matched baseline and correct rate');
 await page.locator('[data-page="priorities"]').click();await page.selectOption('#queue-scope','flagged');
 if(await page.locator('#queue tbody tr').count()!==1)throw Error('Expected one investigative flag');
 await page.locator('#threshold').fill('40');if(await page.locator('#queue tbody tr').count()!==0)throw Error('Threshold did not recompute');
 await page.locator('#threshold').fill('10');await page.locator('[data-priority]').click();await page.locator('dialog[open]').waitFor();await page.locator('#close').click();
 const download=page.waitForEvent('download');await page.locator('#export-queue').click();await download;
 checks.push('Synthetic fixture: queue thresholds, drilldown and filtered export');
 if(errors.length)throw Error(errors.join(';'));
 fs.writeFileSync(path.resolve(__dirname,'../reports/browser-validation.json'),JSON.stringify({passed:true,checks,javascript_errors:errors,qualification:'Browser software validation only; synthetic fixtures never persisted as research data.'},null,2)+'\n');
 console.log(checks.join('\n'));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
