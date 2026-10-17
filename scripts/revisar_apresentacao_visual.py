"""Apresentação visual revisada: cenas comuns à web e ao PowerPoint."""
from pathlib import Path
import json,math,textwrap,html
R=Path(__file__).resolve().parents[1];D=R/'dist';A=D/'apresentacao';old=json.loads((A/'conteudo.json').read_text(encoding='utf-8'));ml=json.loads((D/'data/aprendizado.json').read_text(encoding='utf-8'))
P={'bg':'#F6F2EC','ink':'#272726','red':'#A33B32','amber':'#C38A32','muted':'#72695F','line':'#D9CFC2','dark':'#202423','soft':'#E9DFD2','white':'#FFFFFF','green':'#526A5C'}
slides=[];ops=[]
def text(t,x,y,w,size=25,color=None,bold=False):
 lines=[]
 for para in t.split('\n'):lines+=textwrap.wrap(para,width=max(6,int(w/(size*(.57 if bold else .51)))),break_long_words=False,break_on_hyphens=False) or ['']
 op=dict(kind='text',text=t,lines=lines,x=x,y=y,w=w,h=len(lines)*size*1.24+5,size=size,color=color or P['ink'],bold=bold);ops.append(op);return op

def rect(x,y,w,h,fill,stroke=None,r=0):ops.append(dict(kind='rect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke or 'none',r=r))
def circle(x,y,r,fill,stroke=None):ops.append(dict(kind='circle',x=x,y=y,r=r,fill=fill,stroke=stroke or 'none'))
def line(x1,y1,x2,y2,color=None,width=2):ops.append(dict(kind='line',x1=x1,y1=y1,x2=x2,y2=y2,color=color or P['line'],width=width))
def arrow(x1,y1,x2,y2,color=None):
 col=color or P['red'];line(x1,y1,x2,y2,col,3)
 if abs(y2-y1)<1:
  sign=1 if x2<x1 else -1;line(x2+10*sign,y2-7,x2,y2,col,3);line(x2+10*sign,y2+7,x2,y2,col,3)
 elif y2>y1:line(x2-7,y2-10,x2,y2,col,3);line(x2+7,y2-10,x2,y2,col,3)
 else:line(x2-7,y2+10,x2,y2,col,3);line(x2+7,y2+10,x2,y2,col,3)
def image(file,x,y,w,h,fit='cover'):ops.append(dict(kind='image',file=file,x=x,y=y,w=w,h=h,fit=fit))
def begin(title,group,seconds,dark=False,subtitle=''):
 global ops
 ops=[];slides.append(dict(title=title,group=group,seconds=seconds,background=P['dark'] if dark else P['bg'],ops=ops,notes='',subtitle=subtitle));text(group.upper(),58,30,1120,14,P['amber'] if dark else P['red'],True);text(title,58,79,1164,43,P['white'] if dark else P['ink'],True)
 if subtitle:text(subtitle,58,199,1164,23,P['soft'] if dark else P['muted'])
def note(s,source=''):
 slides[-1]['notes']=s+'\n\nFontes: '+source

def foot(s,dark=False):line(58,649,1222,649,'#665F55' if dark else P['line'],1);text(s,58,665,1150,15,P['soft'] if dark else P['muted'])
def node(x,y,w,h,title,body='',dark=False):
 rect(x,y,w,h,P['dark'] if dark else P['white'],P['line']);heading=text(title,x+18,y+14,w-36,26,P['white'] if dark else P['red'],True)
 if body:text(body,x+18,y+max(61,heading['h']+20),w-36,22,P['soft'] if dark else P['ink'])
def car(x,y,col=None):
 col=col or P['ink'];rect(x,y+20,80,32,col,r=5);rect(x+17,y,44,28,col,r=5);rect(x+23,y+5,30,17,P['bg']);circle(x+18,y+52,9,col);circle(x+65,y+52,9,col)
def camera(x,y):rect(x,y,72,44,P['ink'],r=5);circle(x+37,y+21,15,P['bg']);circle(x+37,y+21,7,P['amber']);line(x+30,y+45,x+30,y+82,P['ink'],5);line(x+2,y+83,x+58,y+83,P['ink'],5)
def document(x,y):
 rect(x,y,60,78,P['white'],P['ink']);
 for j in range(4):line(x+10,y+16+j*13,x+49,y+16+j*13,P['red'] if j==0 else P['muted'],3)
# Map assets use the same Mercator formula as the corrected dashboard; uniform scale.
geo=json.loads((D/'data/malha.json').read_text(encoding='utf-8'));roads=json.loads((D/'data/rodovias.json').read_text(encoding='utf-8'))
def proj(p):return (p[0]*math.pi/180,-math.log(math.tan(math.pi/4+p[1]*math.pi/360)))
def polygons(f):
 g=f['geometry'];return [r for poly in (g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]) for r in poly]
def map_asset(file,bounds=None):
 pts=[proj(p) for f in geo['features'] for ring in polygons(f) for p in ring]
 if bounds:pt=[proj([bounds[0],bounds[1]]),proj([bounds[2],bounds[3]])];x0,x1=sorted([p[0] for p in pt]);y0,y1=sorted([p[1] for p in pt])
 else:x0=min(p[0] for p in pts);x1=max(p[0] for p in pts);y0=min(p[1] for p in pts);y1=max(p[1] for p in pts)
 W,H=700,540;scale=min((W-35)/(x1-x0),(H-35)/(y1-y0));ox=(W-scale*(x1-x0))/2;oy=(H-scale*(y1-y0))/2
 def xy(p):x,y=proj(p);return(ox+(x-x0)*scale,oy+(y-y0)*scale)
 def path(points):return ' '.join(('M' if i==0 else 'L')+f'{x:.2f},{y:.2f}' for i,(x,y) in enumerate(map(xy,points)))
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="{P["bg"]}"/><defs><clipPath id="clip"><rect width="700" height="540"/></clipPath></defs><g clip-path="url(#clip)">'
 for f in geo['features']:
  mg=str(f['properties'].get('codarea'))=='31';svg+=f'<path d="'+''.join(path(r)+'Z' for r in polygons(f))+f'" fill="{P["soft"] if mg else "#EAE6DE"}" stroke="#FFFFFF" stroke-width="1.4"/>'
 for r in roads:
  if bounds and r['uf']!='MG':continue
  for ln in r['lines']:
   sample=ln[::max(1,len(ln)//22)]
   if sample[-1]!=ln[-1]:sample.append(ln[-1])
   svg+=f'<path d="{path(sample)}" fill="none" stroke="{P["red"] if r["br"]==40 else "#ADA69B"}" stroke-width="{2.2 if r["br"]==40 else .35}"/>'
 if bounds:
  svg+='<text x="390" y="90" font-family="Arial" font-size="24" font-weight="bold" fill="#A33B32">MG · BR-040</text>'
 svg+='</g></svg>';(D/'assets'/file).write_text(svg,encoding='utf-8')
map_asset('mapa-apresentacao-br.svg');map_asset('mapa-apresentacao-mg.svg',[-52,-14,-39,-24])
# 1 Full-bleed photographic composition, not an image separated from the subject.
begin('O que o Estado vê','Qualificação do projeto',35,dark=True);ops.clear();image('assets/rodovia-abertura.png',0,0,1280,720);rect(0,0,1280,720,'#101514/68');rect(0,0,750,720,'#101514/65');rect(58,35,182,98,'#FFFFFF');image('assets/fumec-logo.png',64,41,170,86,'contain');text('DOUTORADO EM ADMINISTRAÇÃO',58,159,700,17,P['soft'],True);text('O que o\nEstado vê',58,221,775,82,P['white'],True);text('Escolhas de governança e visibilidade\nnas rodovias federais',62,445,730,31,P['white']);text('Débora Cristina Coutinho Vilas Bôas\nOrientadora Profa. Dra. Suzana Rodrigues',62,558,800,22,P['soft']);text('27 OUT 2026 · 15H    |    20 MINUTOS',62,665,1000,18,P['white'],True)
note('Apresente o projeto de Débora Cristina Coutinho Vilas Bôas, orientado por Suzana Rodrigues na Universidade FUMEC. A agenda informada é 27 de outubro de 2026 às 15h. O roteiro principal tem 14 slides e dura 20 minutos; os dois apêndices são opcionais. Diferencie o desenho original das extensões do laboratório.','Projeto, capa e resumo. Imagem de fundo ilustrativa gerada por IA, sem associação a um evento real.')
# 2 Visual contrast on one observation pipeline.
begin('O número observado mistura risco e capacidade de registrar','Problema de pesquisa',70,subtitle='Como comparar arranjos quando o próprio registro pode variar entre eles?')
rect(80,307,1120,14,'#D7C8B7');car(105,278);car(235,278);camera(405,270);arrow(500,315,610,315);document(654,275);arrow(745,315,845,315);text('INDICADOR\nPUBLICADO',891,279,292,30,P['red'],True)
text('Ocorrência real',84,401,295,28,P['ink'],True);text('Tráfego, infraestrutura\ne condições de circulação',84,448,310,25);text('Observação',430,401,290,28,P['ink'],True);text('Instrumentos, atendimento\ne rotinas de registro',430,448,335,25);text('Comparação',877,401,300,28,P['ink'],True);text('Segurança e registro\nprecisam ser distinguidos',877,448,310,25)
foot('Mais registros são compatíveis com mais risco, melhor observação ou ambos.');note('O mesmo número registrado pode refletir maior risco, mais circulação ou melhor capacidade de observar. A pergunta institucional é como comparar resultados quando obrigações e instrumentos produzem informação com cobertura diferente. Esses mecanismos concorrentes precisam ser distinguidos. Não se afirma que toda diferença decorra de detecção.','Projeto, seções 1.2 e 2.4. Diagrama de mecanismos concorrentes, sem proporções empíricas presumidas.')
# 3 Thesis modeled, not only a quotation.
begin('A tese liga a produção da informação à resposta pública','Tese defendida · seção 1.5',70,dark=True,subtitle='A governança condiciona o que pode ser conhecido e o que pode ser feito.')
for x,title,body in [(58,'Governança','Obrigações\nrecursos\nresponsáveis'),(361,'Conhecer','Monitorar\nregistrar\nvincular'),(664,'Agir','Priorizar\nexecutar\navaliar'),(967,'Resultado','Danos\nrecorrência\naprendizagem')]:node(x,305,254,224,title,body,True)
for x in [312,615,918]:arrow(x,415,x+39,415,P['amber'])
line(1094,556,1094,585,P['amber'],2);line(185,585,1094,585,P['amber'],2);arrow(185,585,185,548,P['amber']);foot('Proposição a demonstrar: reconhecer o risco não assegura uma resposta efetiva.',True);note('A tese da seção 1.5 trata a produção da informação como parte da governança e distingue reconhecer o risco de agir sobre ele. A formulação é uma proposição a demonstrar. A persistência das perdas, sem documentos sobre obrigações, decisões e execução, não comprova falha do PDCA. A avaliação deve considerar ações reais insuficientes e explicações concorrentes.','Projeto, seção 1.5. Síntese e modelo visual interpretativo; não representa um efeito causal já estimado.')
# 4 More theory, as an explicit explanatory architecture.
begin('A teoria articula legibilidade, regulação e valor público','Arquitetura teórica do projeto',110)
node(58,227,355,212,'Legibilidade','Scott (1998)\nCadastros e categorias\ntornam problemas governáveis.');node(462,227,355,212,'Arranjos e instrumentos','Peters e Pierre; Baldwin et al.\nContratos e monitoramento\nestruturam a coordenação.');node(866,227,355,212,'Mensuração e uso','Espeland e Stevens; Power\nComparar e tornar auditável\nnão garante equivalência.');arrow(416,335,451,335);arrow(820,335,855,335)
rect(58,484,1164,119,P['dark']);text('POR QUE ISSO IMPORTA?',80,500,345,19,P['amber'],True);text('Perdas não reconhecidas e respostas incompletas afetam o valor público.',80,538,1080,26,P['white'],True);foot('Moore (1995) e Bozeman (2002) · a relação entre indicadores e ação é parte do problema institucional.')
note('A tese usa Scott como teoria de base. A governança regulatória situa a coordenação por regras, contratos, monitoramento e sanções nos arranjos híbridos. Espeland e Stevens discutem a comensuração; Power separa auditabilidade de desempenho substantivo. Bevan e Hood, Moynihan e Kroll ajudam a situar a produção e o uso de indicadores. Moore e Bozeman dão a consequência normativa: as perdas que não entram na representação do problema podem ficar fora das prioridades. Não confundir indicador de custo com medida integral de valor público. A originalidade pretendida é conectar essas contribuições no nível do arranjo e do trecho, em vez de apenas renomear capacidade informacional. Transição: qual construto faz essa conexão?','Projeto, seções 2.1, 2.2 e 2.7. Autores conforme o referencial da proposta.')
# 5 Formative construct, three dimensions and boundaries.
begin('VGPR mede condições de ver, não qualidade da segurança','Conceito proposto pela autora',110,subtitle='Capacidade de observar e registrar com vínculo ao local, à data e ao responsável.')
for x,lab,body in [(58,'Instrumentos','Equipamentos e rotinas\nAnteriores ao sinistro'),(462,'Vinculação','Trecho · ano · responsável\nAnteriores ao sinistro'),(866,'Cobertura','Parcela efetivamente registrada\nValidação a demonstrar')]:
 node(x,284,355,191,lab,body)
text('CONSTRUTO FORMATIVO',60,514,465,20,P['red'],True);text('Dimensões diferentes não exigem um índice único.',60,549,700,27,P['ink'],True);text('Transparência divulga.\nAccountability cobra.\nVGPR trata da observação anterior.',850,505,370,23)
foot('Instrumentos e vinculação entram como medidas principais; cobertura exige validação independente.')
note('A definição e a separação das dimensões estão nas seções 2.3 e 4.5. Instrumentos e vinculação são anteriores ao sinistro; cobertura é uma dimensão resultante e critério de validação. O projeto classifica o conceito como formativo e evita um índice composto principal. A contribuição proposta é analisar a unidade em que a política acontece e exigir atribuição a um responsável. Isso o distingue, em intenção, de transparência, accountability e capacidade estatal. O desafio empírico permanece: a razão registrado/esperado e a probabilidade de zero de um modelo não identificam sozinhas a cobertura real. A apresentação preserva essa diferença entre definição teórica e mensuração identificada.','Projeto, seção 2.3, Quadro 1, seção 4.5; Diamantopoulos e Winklhofer (2001), conforme citado pela autora.')
# 6 Four hypotheses, plus a visual separation of occurrence and observation.
begin('As proposições precisam distinguir detecção, risco e resposta','Modelo conceitual · P1 a P4',100)
for y,p,title,body in [(235,'P1','Variação da visibilidade','Instrumentos e vinculação diferem entre arranjos.'),(327,'P2','Gradiente de gravidade','Associação com o registro varia por desfecho.'),(419,'P3','Mudança de prioridades','Baixa visibilidade pode alterar o diagnóstico de críticos.'),(511,'P4','Resposta ao risco conhecido','Persistência deve ser confrontada com intervenções documentadas.')]:
 circle(90,y+25,26,P['red']);text(p,71,y+8,60,23,P['white'],True);text(title,144,y,475,27,P['ink'],True);text(body,658,y+3,560,25)
foot('P2 e P3 exigem evidência que separe observação de ocorrência. P4 exige reconstruir a resposta.')
note('P1 propõe diferenças de instrumentos e vinculação por arranjo, jurisdição e instrumentação. P2 propõe associação mais forte da visibilidade com sinistros leves do que fatais; sua interpretação exige considerar que infraestrutura e atendimento também podem alterar gravidade. P3 liga visibilidade, perdas não registradas e mudança das prioridades. Resíduos e zeros, isoladamente, não comprovam perdas ocultas; é necessária triangulação ou um desenho de identificação. P4 confronta persistência com resposta registrada e verificação. As quatro proposições devem ter critérios de refutação e explicar como lidar com informações indisponíveis.','Projeto, seção 3.2. A redação visual sintetiza as proposições, sem apresentá-las como resultados confirmados.')
# 7 PDCA with evidence responsibilities, a genuine model.
begin('O PDCA vira uma trilha de evidências da resposta','Do risco conhecido à ação verificável',90)
for x,y,lab,body in [(125,240,'Planejar','Diagnóstico e prioridade'),(775,240,'Executar','Obra ou medida entregue'),(775,448,'Verificar','Resultado e comparação'),(125,448,'Agir','Correção e nova decisão')]:node(x,y,380,128,lab,body)
arrow(520,300,757,300);arrow(965,379,965,432);line(505,509,758,509,P['red'],3);arrow(758,509,519,509);arrow(315,433,315,380)
text('RESPONSÁVEL + DATA + DOCUMENTO',402,400,580,19,P['red'],True);foot('Norma não prova execução; documento não localizado não prova ausência de ação.')
note('O ciclo organiza a coleta documental, mas não explica sozinho por que a resposta acontece ou falha. Para cada etapa, localizar um documento datado e um responsável: diagnóstico e plano, ordem de serviço e recebimento, avaliação do resultado e decisão de revisão. A hipótese de não resposta exige confrontar o dever de agir, a disponibilidade de recursos, o que foi de fato executado e sua temporalidade. Persistência pode coexistir com intervenção insuficiente. Uma falha de coordenação é diferente de cumprimento formal sem resultado. O desenho original usa fontes públicas e pedidos via LAI.','Projeto, seções 2.5, 3.3 e 4.6; Deming (1986), conforme a proposta. Explicações complementares de desacoplamento pertencem à agenda de aprofundamento.')
# 8 Data pipeline with large numbers, no dense table.
begin('A base já permite testar padrões e associações','Extensão independente · fontes preservadas',80)
for x,name,desc in [(58,'PRF','Ocorrências\n2022–2025'),(365,'PNCT','Tráfego modelado\n2022–2025'),(672,'SNV','Malha e trechos\n202604A'),(979,'ANTT','Instrumentos\ne investimentos')]:
 document(x+90,239);text(name,x,339,245,32,P['red'],True);text(desc,x,388,245,26)
line(170,470,170,495);line(170,495,1100,495);line(1100,470,1100,495);text('UF + BR + km + período → auditoria → painel reproduzível',123,526,1080,30,P['ink'],True);foot('278.103 sinistros · 23.274 mortes · 26 fontes originais preservadas com SHA-256')
note('O laboratório integrou registros PRF, exposição modelada PNCT e referências cadastrais SNV e ANTT. Os arquivos são preservados com manifesto e hash. Cada fonte tem unidade e período próprios: ocorrências não são pessoas, VMD é modelado e cadastro atual não reconstrói operação histórica. O notebook permite verificar as regras e os cálculos.','Fontes oficiais e manifestos do laboratório. Universo PRF 2022–2025; exposição modelada e malha cadastral com escopos próprios.')
# 9 The map is data, not decoration.
begin('A atribuição institucional começa no trecho e no período','Unidade territorial e rastreabilidade',70)
image('assets/mapa-apresentacao-br.svg',20,211,540,416,'contain');image('assets/mapa-apresentacao-mg.svg',602,214,640,410,'contain');arrow(523,415,588,415);text('Brasil · malha federal',75,593,455,22,P['ink'],True);text('Exemplo de localização · MG / BR-040',652,593,557,22,P['red'],True);foot('Limites IBGE e traçados SNV · Mercator com escala uniforme · geometria de 2026, sem regime histórico inferido')
note('O mapa usa limites públicos do IBGE e traçado oficial do SNV. A mesma transformação Mercator é aplicada a polígonos e rodovias, com escala uniforme, evitando estiramento independente. A BR-040 está destacada apenas como exemplo de localização, não como seleção definitiva de caso ou ranking de risco. A atribuição institucional exige compatibilizar km, limite e vigência. Um cadastro de 2026 não pode ser aplicado automaticamente a todos os anos. O mapa ilustra a infraestrutura necessária para vincular contratos, registros e intervenções à unidade analítica.','IBGE malhas; SNV 202604A e scripts de geometria do laboratório. Projeção cartográfica registrada no material.')
# 10 Analysis visual families, not a catalogue of algorithms.
begin('Cada pergunta tem unidade, teste e limite próprios','Estratégia analítica',90)
for x,num,title,body in [(58,'01','Gravidade','Logística e multinomial\nBoosting de classificação\nOcorrências registradas'),(462,'02','Contagens','NB2 e boosting Poisson\nExposição em veículos-km\nSegmentos-ano'),(866,'03','Perfis e casos','Persistência e agrupamento\nEstabilidade e comparação\nTrechos e episódios')]:
 circle(x+35,274,30,P['red']);text(num,x+15,255,65,26,P['white'],True);text(title,x,339,360,32,P['ink'],True);text(body,x,407,355,27)
rect(58,558,1164,58,P['dark']);text('Treino 2022–2023 → teste 2024–2025 + teste em corredores reservados',78,573,1120,24,P['white'],True);foot('Os modelos preditivos não identificam governança causal. Fonte independente é necessária para validar detecção.')
note('O núcleo estatístico já inclui logística de fatalidade condicional ao registro, NB2 com offset de exposição e multinomial de gravidade máxima. A extensão de ML compara boosting, regressão Poisson ponderada por exposição e KMeans descritivo. Os preditores não incluem contagens de vítimas na classificação. O tipo de sinistro é conhecido após o evento, portanto não é previsão de acidente antes de ocorrer. Dois candidatos por tarefa são escolhidos em 2022→2023 antes do teste 2024–2025. A reserva por corredor também é excluída da seleção. Os grupos são formados em 2022–2023; incluem taxas iniciais e não medem qualidade da governança.','Scripts estatísticos e aprendizado_maquina.py; documentação oficial do scikit-learn citada no notebook.')
# 11 Quantitative evidence including ML, with an editable native chart.
begin('Há ganho preditivo modesto, com limites substantivos','Extensão executada · teste temporal',100)
ops.append(dict(kind='chart',x=62,y=251,w=665,h=302,categories=['Taxa constante','NB2','Boosting'],values=[round(ml['regression']['reference']['poisson_deviance'],3),round(ml['regression']['nb2_reference']['mean_poisson_deviance'],3),round(ml['regression']['model']['poisson_deviance'],3)],label='Desvio Poisson · menor é melhor'))
text('3,4%',796,266,400,78,P['red'],True);text('redução do desvio\nfrente ao NB2',800,363,382,29);line(796,456,1210,456);text('Classificação fatal',800,477,400,25,P['ink'],True);text('Sensibilidade '+str(round(ml['classifier']['calibrated']['recall'][3]*100,1)).replace('.',',')+'%\npela maior probabilidade',800,524,400,26);text('Desvio Poisson · contagens de mortes registradas',84,583,650,20,P['muted']);foot('Log loss da gravidade melhora pouco; a classificação não está validada para decisão operacional.')
note('Na regressão, os valores de desvio Poisson são aproximadamente 1,855 para taxa constante, 1,599 para NB2 e 1,545 para boosting, no mesmo teste com 9.859 segmentos-ano. A redução frente ao NB2 é cerca de 3,4%; não se afirma significância inferencial desse ganho. Na classificação, log loss melhora de 1,074 do multinomial para 1,065, mas a identificação fatal por argmax permanece baixa, cerca de 3,8%. A acurácia continua dominada pelos leves. É importante reportar calibração, AP e sensibilidade, e não vender o modelo como um classificador forte. Os testes espacial-temporais e referências completas estão no relatório.','dist/data/aprendizado.json; multinomial.json e exposicao.json. Valores calculados pelo pipeline reproduzível.')
# 12 The actual theoretical payoff, beyond prediction.
begin('A contribuição exige explicar como o indicador é produzido','O que a análise acrescenta à compreensão da teoria',80,dark=True)
for x,n,title,body in [(58,'1','Mensuração','A comparação muda com\nexposição, universo e controles.'),(462,'2','Seleção de casos','Dois perfis estáveis ajudam\na procurar episódios comparáveis.'),(866,'3','Mecanismo','O passo decisivo é vincular\nobservação, obrigação e resposta.')]:
 text(n,x,250,100,77,P['amber'],True);text(title,x,359,360,30,P['white'],True);text(body,x,421,355,27,P['soft'])
foot('A extensão prepara testes do mecanismo. Não confirma, por si só, VGPR, detecção ou falha de governança.',True)
note('O avanço não é o uso de um algoritmo mais complexo. É tornar verificável a relação entre o registro e as condições institucionais que o produziram. A exposição modelada e as sensibilidades mostram por que números isolados podem sustentar leituras distintas. Os agrupamentos selecionam candidatos documentais: são perfis estáveis no universo inicial, não classes naturais ou notas de gestão. A ligação teórica precisa mostrar se instrumentos e vinculação tornam a informação comparável, se isso chega às prioridades e como a responsabilidade e os recursos alteram a resposta. Ganhos preditivos modestos não invalidam a pergunta institucional, mas também não a respondem.','Projeto, seção 1.6 e referencial; resultados e limites do laboratório.')
# 13 Feasibility as a three-column decision rather than long prose.
begin('A evidência disponível delimita o que já pode ser afirmado','Viabilidade e próximos testes',105)
for x,col,title,items in [(58,P['green'],'Executado',['Auditoria e exposição','Gravidade e contagens','Persistência e perfis','Teste temporal e espacial']),(462,P['amber'],'Parcial',['Capacidade instrumental','Candidatos documentais','Comparabilidade cadastral','Explicações concorrentes']),(866,P['red'],'A reconstruir',['Operação histórica','Obrigações vigentes','Alerta → decisão → obra','Cobertura independente'])]:
 rect(x,259,355,7,col);text(title,x,290,355,34,col,True)
 for j,it in enumerate(items):circle(x+6,370+j*55,4,col);text(it,x+22,350+j*55,333,25)
foot('Prioridade para a tese: históricos por trecho e evidências documentais que permitam confirmar ou refutar o mecanismo.')
note('A proposta é promissora, mas a evidência quantitativa disponível ainda não demonstra a contribuição institucional. Podemos testar padrões e associações e escolher casos. Cadastros de SAT, CFTV e radares foram preservados e contados, mas não informam integralmente operação passada. Planos, execução e conclusões têm campos que exigem unidades, versões e validação do objeto. Para P4, reconstruir alertas, obrigações, decisões e intervenções, inclusive a hipótese de ação real insuficiente. Para detecção, confrontar fontes e sua dependência. A ausência de um documento acessível não comprova que uma ação não ocorreu.','Matriz de viabilidade e operacionalização de governança; fontes ANTT/DNIT e projeto, seções 3 e 4.')
# 14 Timeline synthesis, full original is an optional appendix.
begin('O cronograma deve fechar a cadeia entre dados e mecanismo','Plano de trabalho · síntese do Quadro 8',90)
phases=[('Out–Dez/26','Auditoria e revisão',58),('Jan–Mar/27','Diagnóstico e documentos',354),('Abr–Jun/27','Modelos e persistência',650),('Jul–Set/27','Validação e redação',946)]
for lab,body,x in phases:
 circle(x+115,315,27,P['red']);text(lab,x,251,262,29,P['red'],True);text(body,x,374,264,27,P['ink'],True)
for x in [200,496,792]:arrow(x,315,x+242,315)
rect(58,498,1164,110,P['dark']);text('O teste final deve unir informação, intervenção e resultado.',82,519,1116,32,P['white'],True);text('O cronograma integral está nos dois slides de apêndice.',82,566,1116,22,P['soft']);foot('A agenda informada é 27/out/2026 às 15h; o Quadro 8 prevê qualificação em nov–dez. Divergência a harmonizar.')
note('Esta é uma síntese narrativa, não uma substituição do calendário original. A auditoria, revisão e qualificação aparecem no fim de 2026; diagnóstico e documentos avançam no primeiro trimestre de 2027; os modelos, gradiente de gravidade e persistência ocupam os meses seguintes; validação, redação, artigos e revisão se sobrepõem no fim do cronograma. O Quadro 8 completo está nos dois apêndices, com todas as atividades e meses originais. A divergência da data de qualificação é explicitada. Feche retomando a tese: compreender governança exige conectar a produção da informação à resposta, e o laboratório torna essa agenda mais verificável.','Projeto, Quadro 8. Agrupamento de fases apenas para exposição em 20 minutos; datas exatas nos apêndices.')
# Exact original schedule, optional; not part of the 20 minute route.
raw=json.loads((R/'dist/apresentacao/cronograma-original.json').read_text(encoding='utf-8'))
for i,rs in enumerate([raw[2:9],raw[9:]]):
 begin('Cronograma integral '+str(i+1)+'/2','Apêndice · consulta durante a discussão',0)
 ops.append(dict(kind='table',x=58,y=231,w=1164,h=356,rows=[['Atividade','Out','Nov','Dez','Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set']]+[[r[0]]+['●' if c else '' for c in r[1:]] for r in rs],widths=[480]+[57]*12))
 foot('2026: out–dez · 2027: jan–set. Fonte: Quadro 8 do projeto; qualificação nov–dez mantida como na fonte.')
 note('Apêndice opcional, fora do tempo de 20 minutos. Preserva a posição de cada marcação nas células originais do Quadro 8, para consulta da banca.','Projeto, seção 6, Quadro 8. Agenda informada pelo avaliador: 27/out/2026 às 15h.')
assert sum(s['seconds'] for s in slides)==1200
for i,s in enumerate(slides):
 s['index']=i+1;s['appendix']=i>=14
 # Small page marker is part of each scene, not a separate UI panel.
 s['ops'].append(dict(kind='text',text=str(i+1).zfill(2),lines=[str(i+1).zfill(2)],x=1192,y=28,w=40,h=25,size=15,color=P['soft'] if s['background']==P['dark'] else P['muted'],bold=False))
meta={k:v for k,v in old.items() if k!='slides'};meta.update(slides=slides,main_slide_count=14,total_slides=16,revision='Revisão visual integral e arquitetura teórica explícita',duration_seconds=1200)
(A/'conteudo.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');(A/'conteudo.js').write_text('window.DECK='+json.dumps(meta,ensure_ascii=False)+';',encoding='utf-8');print('14 slides principais + 2 apêndices; 20 minutos; cenas visuais compartilhadas')
