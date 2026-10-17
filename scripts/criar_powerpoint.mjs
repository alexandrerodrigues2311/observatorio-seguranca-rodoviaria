import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const {Presentation,PresentationFile}=await import(process.env.ARTIFACT_TOOL_MODULE||'@oai/artifact-tool');
const SKILL=process.env.PRESENTATION_SKILL_DIR;if(!SKILL)throw new Error('Defina PRESENTATION_SKILL_DIR para o runtime de apresentações.');
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const R=path.resolve('.'),build=path.join(R,'.presentation-build'),out=path.join(R,'.presentation-build/final-v2/apresentacao-qualificacao-fumec.pptx');
await fs.mkdir(build,{recursive:true});await fs.mkdir(path.dirname(out),{recursive:true});await fs.mkdir(path.join(build,'previews'),{recursive:true});
const data=JSON.parse(await fs.readFile(path.join(R,'dist/apresentacao/conteudo.json'),'utf8'));
const P=Presentation.create({slideSize:{width:1280,height:720}}),FONT='Arial';
const palette={paper:'#F6F2EC',ink:'#302B29',red:'#A33B32',amber:'#B77A16',line:'#D4C5B7',muted:'#75665C',dark:'#292525',cream:'#DFC6B1'};
function rect(s,x,y,w,h,fill){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}})}
function text(s,str,x,y,w,h,size=24,color=palette.ink,bold=false){let z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});z.text=str;z.text.style={typeface:FONT,fontSize:size,color,bold};z.text.insets=0;return z}
function table(s,values,timeline=false){let cols=values[0].length,rows=values.length;let widths=timeline?[480,...Array(12).fill(52)]:cols===3?[320,405,419]:Array(cols).fill(1144/cols);let height=timeline?rows*43:Math.min(350,rows*58);let t=s.tables.add({rows,columns:cols,left:68,top:248,width:1144,height,columnWidths:widths,values});for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){let cell=t.getCell(r,c);cell.text.style={typeface:FONT,fontSize:timeline?(c===0?16:16):20,color:r===0?palette.red:palette.ink,bold:r===0};cell.fill=timeline&&r>0&&c>0&&values[r][c]?palette.red:palette.paper;if(timeline&&r>0&&c>0&&values[r][c])cell.text.style={typeface:FONT,fontSize:16,color:'#FFFFFF',bold:true};cell.text.insets=timeline?5:10;}t.borders.assign({fill:palette.line,width:.5,style:'solid'});return t;}
try{
for(let i=0;i<data.slides.length;i++){
 let d=data.slides[i],s=P.slides.add(),dark=['statement','closing'].includes(d.kind),fg=dark?palette.paper:palette.ink;s.background.fill=dark?palette.dark:palette.paper;
 if(d.kind==='cover'){
  s.background.fill=palette.dark;s.images.add({blob:new Uint8Array(await fs.readFile(path.join(R,'dist/assets/rodovia-abertura.png'))),contentType:'image/png',fit:'cover',position:{left:760,top:0,width:520,height:720},crop:{left:0.5,top:0,right:0,bottom:0},alt:'Ilustração de ocorrência rodoviária'});
  rect(s,68,46,178,98,'#FFFFFF');s.images.add({blob:new Uint8Array(await fs.readFile(path.join(R,'dist/assets/fumec-logo.png'))),contentType:'image/png',fit:'contain',position:{left:74,top:50,width:166,height:90},alt:'Logo Universidade FUMEC enviado pelo usuário'});
  text(s,'DOUTORADO EM ADMINISTRAÇÃO',68,171,655,26,15,palette.cream,true);text(s,d.title,68,224,665,150,66,'#FFFFFF',true);text(s,d.subtitle,68,365,650,103,31,palette.cream);
  text(s,'Débora Cristina Coutinho Vilas Bôas\nOrientadora: Profa. Dra. Suzana Rodrigues',68,500,665,76,20,'#FFFFFF');text(s,'27 de outubro de 2026 · 15h\nQualificação do projeto · roteiro de 20 minutos',68,621,650,55,17,palette.cream);
 }else{
  text(s,d.group.toUpperCase(),68,48,1120,30,14,dark?'#DFB56C':palette.red,true);text(s,d.title,68,100,1144,108,d.title.length>72?40:45,fg,true);text(s,d.subtitle,68,208,1144,64,22,dark?palette.cream:palette.muted);
  if(d.kind==='statement'){
   text(s,d.quote,68,285,1144,115,d.quote.length<20?76:38,'#E4B972',true);let n=d.columns.length,w=(1144-36*(n-1))/n;for(let j=0;j<n;j++){let x=68+j*(w+36);text(s,d.columns[j].heading,x,420,w,42,28,fg,true);text(s,d.columns[j].body,x,472,w,113,23,fg);}
  }else if(d.kind==='data'){table(s,d.rows)}else if(d.kind==='timeline'){table(s,[['Atividade · 2026 → 2027',...d.months],...d.timeline.map(r=>r.map((x,j)=>j===0?x:x?'●':''))],true)}else if(d.kind==='chart'){
   let chart=s.charts.add('bar',{position:{left:68,top:280,width:740,height:314},categories:d.categories,series:[{name:d.chartLabel,values:d.values,fill:palette.red}],barOptions:{direction:'column',grouping:'clustered',gapWidth:100},hasLegend:false,dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:20,fill:palette.ink},numberFormatCode:'#,##0'},xAxis:{textStyle:{fontSize:20,fill:palette.muted},majorGridlines:{fill:'none',width:0}},yAxis:{min:0,max:7000,visible:false,majorGridlines:{fill:'none',width:0}},chartFill:'none',plotAreaFill:'none'});applyPresentationChartFont(chart,{fontFamily:FONT});text(s,d.stat,860,325,330,110,76,palette.red,true);text(s,d.takeaway,860,447,330,100,26,palette.ink);
  }else if(d.columns){let n=d.columns.length,w=(1144-36*(n-1))/n;for(let j=0;j<n;j++){let x=68+j*(w+36);text(s,d.columns[j].heading,x,310,w,80,28,fg,true);text(s,d.columns[j].body,x,405,w,175,24,fg);if(j<n-1)rect(s,x+w+16,310,1,265,dark?'#6A5144':palette.line)}}
  rect(s,68,632,1144,1,dark?'#6A5144':palette.line);text(s,d.bottom||'',68,649,1144,48,16,dark?palette.cream:'#735E50');
 }
 text(s,String(i+1).padStart(2,'0'),1214,27,36,24,15,d.kind==='cover'?'#FFFFFF':'#AD9D8E');s.speakerNotes.text='TEMPO SUGERIDO: '+d.seconds+' segundos.\n\n'+d.notes;
 console.log('Slide',i+1,'criado');
}
await (await PresentationFile.exportPptx(P)).save(path.join(build,'candidate.pptx'));
console.log('Rascunho PPTX exportado');
// PNG previews use the same authored editable objects.
for(let i=0;i<P.slides.items.length;i++){try{let blob=await P.export({slide:P.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(build,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));console.log('Render',i+1)}catch(e){console.log('Render indisponível',i+1,e.message);throw e}}
const result=await finalizePresentation({workspaceDir:R,candidatePath:path.join(build,'candidate.pptx'),finalPath:out,pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...data.slides.flatMap((d,i)=>['data','timeline'].includes(d.kind)?['--require-native-table-slide',String(i+1)]:[])],explicitTotalSlideCount:18,requiredNativeTableOwnerSlides:data.slides.flatMap((d,i)=>['data','timeline'].includes(d.kind)?[i+1]:[]),requiredNativeChartOwnerSlides:data.slides.flatMap((d,i)=>d.kind==='chart'?[i+1]:[]),materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validacao-pptx.json')});console.log(JSON.stringify(result));


}catch(e){console.error(e.message);process.exitCode=1}
