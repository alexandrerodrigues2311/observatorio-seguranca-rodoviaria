const {chromium}=require('C:/Users/alexandre.rodrigues/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
const BASE=process.env.PAINEL_URL||'http://127.0.0.1:8773';
(async()=>{
 fs.mkdirSync('qa',{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1512,height:1050},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto(BASE,{waitUntil:'networkidle'});
 await page.waitForFunction(()=>window.PAINEL_READY===true,{timeout:20000});
 await page.screenshot({path:'qa/panorama.png',fullPage:true});
 const results={title:await page.title(),total:await page.locator('#hero-number').innerText(),tabs:[],checks:{}};
 for(const id of ['teoria','territorio','padroes','exposicao','modelos','auditoria','metodo','laboratorio']){
  await page.locator(`[data-page="${id}"]`).click();await page.waitForTimeout(650);
  results.tabs.push({id,active:await page.locator('#'+id).isVisible(),charts:await page.locator('#'+id+' svg').count()});
  await page.screenshot({path:`qa/${id}.png`,fullPage:true});
 }
 await page.locator('[data-page="teoria"]').click();await page.waitForTimeout(300);results.checks.theoryFiltersEnabled=!(await page.locator('#year').isDisabled());await page.selectOption('#year','2024');await page.waitForTimeout(150);results.checks.theoryContext=(await page.locator('#theory-context').innerText()).includes('2024');
 await page.locator('[data-page="visao"]').click();await page.waitForTimeout(200);results.checks.openingInsights=await page.locator('#opening-insights .finding').count()===3;results.checks.donutVisibleNumbers=(await page.locator('#severity-values').innerText()).includes('%');results.checks.trendNoRedundantAxis=await page.evaluate(()=>charts.trend.getOption().graphic.length>0||charts.trend.getOption().yAxis[0].show===false);
 await page.locator('[data-page="padroes"]').click();await page.waitForTimeout(200);await page.selectOption('#multi-outcome','Com mortes');results.checks.multinomialTable=(await page.locator('#multi-terms').innerText()).includes('RRR');results.checks.chartComments=await page.locator('#padroes .chart-commentary').count()>=4;
 await page.locator('[data-page="territorio"]').click();await page.waitForTimeout(200);await page.selectOption('#map-layer','network');await page.selectOption('#map-corridor','MG|40');await page.waitForTimeout(350);results.checks.corridorZoom=await page.evaluate(()=>charts.map.getOption().geo[0].zoom>1);results.checks.stateLabels=await page.evaluate(()=>charts.map.getOption().geo[0].label.show===true);await page.evaluate(()=>charts.map.dispatchAction({type:'showTip',seriesIndex:1,dataIndex:0}));await page.waitForTimeout(200);results.checks.mapTooltip=(await page.locator('#map').innerText()).includes('SNV');await page.screenshot({path:'qa/mapa-identificacao.png',fullPage:true});
 await page.locator('[data-page="visao"]').click();await page.waitForTimeout(100);await page.selectOption('#year','2024');await page.selectOption('#uf',{label:'MG'});await page.waitForTimeout(450);
 results.filtered=await page.locator('#scope').innerText();results.filteredKpis=await page.locator('#kpis').innerText();
 results.checks.filterWorking=results.filtered.includes('MG')&&results.filtered.includes('2024');
 const downloadPromise=page.waitForEvent('download');await page.locator('#export').click();const download=await downloadPromise;await download.saveAs('qa/recorte.csv');
 results.checks.csvExport=fs.statSync('qa/recorte.csv').size>100;
 await page.locator('[data-page="territorio"]').click();await page.fill('#segment-search','BR-040');results.tableSearch=await page.locator('#table-info').innerText();
 await page.locator('#reset').click();await page.fill('#segment-search','');
 await page.locator('[data-page="modelos"]').click();
 const svgPromise=page.waitForEvent('download');await page.locator('[data-chart="forest"]').click();const sv=await svgPromise;await sv.saveAs('qa/forest.svg');results.checks.svgExport=fs.readFileSync('qa/forest.svg','utf8').includes('<svg');
 await page.locator('[data-page="exposicao"]').click();await page.selectOption('#expo-year','2024');await page.selectOption('#expo-uf','MG');results.checks.exposureFilter=(await page.locator('#expo-kpis').innerText()).length>30;await page.locator('[data-page="territorio"]').click();await page.selectOption('#map-layer','network');await page.waitForTimeout(600);results.checks.roadTraces=(await page.locator('#map-subtitle').innerText()).includes('SNV');await page.selectOption('#map-layer','admin');await page.waitForTimeout(500);await page.screenshot({path:'qa/rodovias.png',fullPage:true});await page.locator('[data-page="modelos"]').click();await page.waitForFunction(()=>document.querySelector('#modelos').classList.contains('active')&&document.querySelector('#year').disabled);results.checks.fixedFilters=await page.locator('#year').isDisabled();
 await page.setViewportSize({width:390,height:844});await page.locator('[data-page="visao"]').click();await page.waitForTimeout(500);await page.screenshot({path:'qa/mobile.png',fullPage:true});
 results.checks.noMobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2);
 for(const url of ['exports/relatorio-analitico.html','exports/figura-modelo.svg','exports/diagnostico-snv-202604A.csv','exports/protocolo-governanca.html','exports/catalogo-governanca.csv','exports/registro-extensoes.json','exports/viabilidade-protocolo.json','exports/modelo-multinomial.csv','data/interpretacoes.json']){let r=await page.request.get(BASE+'/'+url);results.checks[url]=r.status()===200}
 results.errors=errors;fs.writeFileSync('qa/browser-results.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));
 await browser.close();if(errors.length||Object.values(results.checks).some(v=>!v))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
