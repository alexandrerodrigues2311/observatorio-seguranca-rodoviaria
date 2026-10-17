"""Figuras vetoriais, relatório, manifesto e verificações de consistência."""
from pathlib import Path
import json,hashlib,datetime,html,zipfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
R=Path(__file__).resolve().parents[1];OUT=R/'dist'/'data';EXP=R/'dist'/'exports'
def load(n):return json.loads((OUT/(n+'.json')).read_text(encoding='utf8'))
def table(df):return df.to_html(index=False,border=0,float_format=lambda x:f'{x:.4f}')
src=load('fontes');(OUT/'fontes.js').write_text('window.FONTES='+json.dumps(src,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
model=load('modelo');p=load('persistencia');q=load('auditoria');snv=load('snv');summary=load('resumo');D=pd.read_pickle(R/'data'/'prf-limpa.pkl')
checks={
 'total_ocorrencias':len(D)==sum(x['ocorrencias'] for x in q)==278103,
 'ids_unicos_por_ano':not D.duplicated(['ano','id']).any(),
 'anos_consistentes':bool((D.date.dt.year==D.ano).all()),
 'vitimas_nao_negativas':bool((D[['mortos','feridos_graves','feridos_leves']]>=0).all().all()),
 'totais_anuais_preservados':all(int(D[D.ano==a['ano']].mortos.sum())==a['mortos'] for a in q),
 'pareamento_contabilizado':all(sum(m['n'] for m in snv['match'] if m['ano']==a['ano'])==a['ocorrencias'] for a in q),
 'convergencia_logistica':model['meta']['converged'],
 'intervalos_coerentes':all(t['low']<=t['odds_ratio']<=t['high'] for t in model['terms']),
 'auc_valida':0<=model['validation']['auc']<=1,
 'bootstrap_intervalo_coerente':p['rho_low']<=p['rho']<=p['rho_high'],
 'catalogo_snv':snv['n']==7664,
 'amostra_modelo_contabilizada':model['meta']['n']+model['exclusions']==len(D),
 'arquivos_brutos_sha256':all(hashlib.sha256((R/'data'/a['file']).read_bytes()).hexdigest()==a['sha256'] for a in src if a.get('sha256')),
}
# Independência da agregação exibida no navegador em relação à tabela nacional.
rec=load('registros');arr=np.asarray(rec['rows'],dtype=np.int64)
checks['agregacao_painel']=len(arr)==len(D) and arr[:,11].sum()==D.mortos.sum() and arr[:,12].sum()==D.feridos_graves.sum()
for a in q:checks[f'total_painel_{a["ano"]}']=int((arr[:,0]==a['ano']).sum())==a['ocorrencias']
checks={k:bool(v) for k,v in checks.items()}
if not all(checks.values()):raise AssertionError(checks)
(OUT/'validacao.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#203744','text.color':'#203744','xtick.color':'#687984','ytick.color':'#203744','svg.fonttype':'none','figure.facecolor':'white','axes.facecolor':'white'})
terms={'noite':'18h–05h vs. 06h–17h','urbano':'Uso do solo urbano vs. não urbano','dupla':'Pista dupla vs. simples','multipla':'Pista múltipla vs. simples','chuva':'Chuva vs. demais condições','fim_semana':'Sábado/domingo vs. segunda–sexta'}
ts=[t for t in model['terms'] if t['term'] in terms]
fig,ax=plt.subplots(figsize=(9,4.9));fig.subplots_adjust(left=.43,bottom=.25,top=.80,right=.95)
y=np.arange(len(ts));v=np.array([t['odds_ratio'] for t in ts]);lo=np.array([t['low'] for t in ts]);hi=np.array([t['high'] for t in ts]);ax.errorbar(v,y,xerr=np.vstack([v-lo,hi-v]),fmt='o',color='#087e82',ecolor='#087e82',capsize=4,markersize=6,lw=1.8)
ax.set_yticks(y,[terms[t['term']] for t in ts]);ax.invert_yaxis();ax.set_xscale('log');ax.axvline(1,color='#adb8b3',ls='--',lw=1);ax.set_xlim(.4,2.6);ax.set_xticks([.5,1,2],['0,5','1','2']);ax.set_xlabel('Razão de chances ajustada (OR) e IC 95%');ax.grid(axis='x',alpha=.15)
fig.suptitle('Gravidade condicional dos sinistros registrados',x=.05,ha='left',fontsize=15,fontweight='bold',y=.96)
fig.text(.05,.87,f"PRF 2022–2025 · n = {model['meta']['n']:,} · {model['meta']['clusters']} grupos UF–BR",fontsize=10)
fig.text(.05,.06,'Ajustes por UF e ano. Covariância sanduíche agrupada por UF–BR; quantil t.\nAssociações condicionais ao registro, sem ajuste por exposição e sem interpretação causal.\nFonte: microdados oficiais PRF; elaboração independente. Coleta em 17/10/2026.',fontsize=8,color='#687984',linespacing=1.7)
for fmt in ['svg','png']:fig.savefig(EXP/f'figura-modelo.{fmt}',dpi=300)
plt.close(fig)
fig,ax=plt.subplots(figsize=(8.4,6));fig.subplots_adjust(left=.12,bottom=.24,top=.83,right=.94)
pr=np.array([[r[4],r[6]] for r in p['rows']]);ax.scatter(pr[:,0],pr[:,1],s=12,alpha=.18,c='#087e82',edgecolors='none',rasterized=False);ax.set_xlabel('Mortes registradas em 2022–2023');ax.set_ylabel('Mortes registradas em 2024–2025');ax.grid(alpha=.14)
fig.suptitle('Persistência espacial das mortes registradas',x=.05,ha='left',fontsize=15,fontweight='bold',y=.96)
fig.text(.05,.88,f"Intervalos de 10 km · Spearman ρ = {p['rho']:.3f} (IC 95% {p['rho_low']:.3f}–{p['rho_high']:.3f})",fontsize=10)
fig.text(.05,.055,f"Universo: {p['n_segments']:,} intervalos com ao menos um registro no período completo.\n500 reamostragens de corredores UF–BR; semente 20261017. Pontos podem se sobrepor.\nPersistência não identifica ausência de resposta institucional. Fonte: PRF; elaboração independente.",fontsize=8,color='#687984',linespacing=1.7)
for fmt in ['svg','png']:fig.savefig(EXP/f'figura-persistencia.{fmt}',dpi=300)
plt.close(fig)
v=model['validation'];fig,ax=plt.subplots(figsize=(6.8,5.6));fig.subplots_adjust(left=.13,bottom=.24,top=.8,right=.94)
cal=v['calibration'];xx=np.array([c['pred'] for c in cal]);yy=np.array([c['obs'] for c in cal]);ll=np.array([c['low'] for c in cal]);hh=np.array([c['high'] for c in cal]);ax.errorbar(xx,yy,yerr=[yy-ll,hh-yy],fmt='o',color='#087e82',capsize=3);ax.plot([0,.2],[0,.2],ls='--',c='#adb8b3',lw=1);ax.set_xlim(0,.2);ax.set_ylim(0,.2);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('Probabilidade prevista');ax.set_ylabel('Proporção observada');ax.grid(alpha=.15)
fig.suptitle('Validação temporal da gravidade condicional',x=.05,ha='left',fontsize=13,fontweight='bold',y=.96);fig.text(.05,.86,f"Treino 2022–2023 → teste 2024–2025 · AUC {v['auc']:.3f}",fontsize=10);fig.text(.05,.06,f"Decis do teste; IC binomial de Wilson. Modelo sem indicadores de ano.\nBrier {v['brier']:.4f}; referência constante do treino {v['baseline_brier']:.4f}.\nFonte: PRF; elaboração independente. Sem interpretação causal.",fontsize=8,color='#687984',linespacing=1.6)
for fmt in ['svg','png']:fig.savefig(EXP/f'figura-calibracao.{fmt}',dpi=300)
plt.close(fig)
conc=load('integracao');groups=pd.DataFrame(snv['groups']);match=sum(x['n'] for x in snv['match'] if x['snv_match']=='Único')
report=f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Relatório analítico de segurança rodoviária</title><style>body{{font:15px/1.7 Georgia,serif;color:#203744;max-width:1050px;margin:50px auto;padding:0 25px}}h1,h2,h3{{font-family:Arial,sans-serif}}h1{{font-size:33px;line-height:1.2}}h2{{font-size:22px;margin-top:35px}}table{{font:11px/1.5 Arial,sans-serif;border-collapse:collapse;width:100%;display:block;overflow:auto}}td,th{{padding:8px;border:1px solid #dce3e2;text-align:right}}th{{background:#edf2ee}}img{{max-width:100%}}.note{{padding:15px;background:#f8f1e7}}@media print{{body{{margin:0}}h2{{break-after:avoid}}img{{max-height:600px}}}}</style>
<h1>Registros, gravidade e persistência nas rodovias federais</h1><p>Relatório independente com dados oficiais coletados em 17 de outubro de 2026. Finalidade: exploração científica e preparação de avaliação acadêmica.</p>
<p class="note"><b>Escopo:</b> resultados condicionais aos registros PRF. Não se estima sub-registro, risco por veículo-quilômetro, efeito causal de concessão ou omissão institucional. O SNV 202604A é uma referência espacial retrospectiva.</p>
<h2>Base e resultados descritivos</h2><p>Foram analisadas {len(D):,} ocorrências de 2022 a 2025, com {int(D.mortos.sum()):,} mortes e {int(D.feridos_graves.sum()):,} feridos graves. Não foram encontrados IDs duplicados dentro de cada arquivo anual. Os totais refletem a versão baixada e podem divergir de publicações anteriores.</p>{table(pd.DataFrame(summary))}
<h2>Associações ajustadas com a gravidade</h2><p>Regressão logística por máxima verossimilhança, desfecho mortos &gt; 0, ajuste por seis características observáveis, UF e ano; {model['meta']['n']:,} ocorrências e {model['meta']['clusters']} grupos UF–BR. Covariância sanduíche agrupada, correção finita, quantil t. Foram excluídas {model['exclusions']} ocorrências por ausência ou inadequação dos campos necessários.</p><img src="figura-modelo.svg" alt="Razões de chances ajustadas e intervalos de confiança"><p>As associações não são efeitos de intervenção. Em particular, a estimativa para chuva não sustenta benefício protetivo: composição, exposição, velocidade e seleção dos registros não estão identificadas pelo modelo.</p>{table(pd.DataFrame(ts))}
<h2>Validação temporal</h2><p>Um modelo separado foi ajustado em 2022–2023, sem indicadores de ano, e aplicado a 2024–2025. Teste com {v['n_test']:,} ocorrências: AUC {v['auc']:.4f}; Brier {v['brier']:.5f}; Brier da referência constante calculada no treino {v['baseline_brier']:.5f}. Discriminação é moderada; não se trata de ferramenta validada para decisão operacional.</p><img src="figura-calibracao.svg" alt="Calibração temporal">
<h2>Persistência espacial</h2><p>Nos {p['n_segments']:,} intervalos UF–BR de 10 km com ao menos um registro no período completo, a correlação de Spearman entre as mortes de 2022–2023 e 2024–2025 foi {p['rho']:.4f}, IC 95% [{p['rho_low']:.4f}, {p['rho_high']:.4f}]. Intervalo percentílico de 500 reamostragens de corredores UF–BR; semente 20261017. O universo é condicionado à presença em ao menos um ano, inclusive no futuro em relação ao primeiro biênio, e não é um censo de toda a malha.</p><img src="figura-persistencia.svg" alt="Persistência de mortes por intervalo"><p>O resultado mostra associação temporal, sem demonstrar ausência de intervenção. Não houve avaliação de efeito antes e depois nem inferência de que o ciclo PDCA se interrompeu.</p>
<h2>Vinculação espacial e limites da comparação institucional</h2><p>O SNV 202604A contém {snv['n']:,} trechos. {match:,} de {len(D):,} ocorrências ({100*match/len(D):.2f}%) tiveram correspondência única em eixo principal por UF, BR e intervalo [início,fim). Os trechos não operacionais PLA/LEN, acessórios e jurisdições não federais foram retirados apenas do diagnóstico de zeros. A administração corresponde a 2026; não foi reconstruída retrospectivamente.</p>{table(groups)}<p>Os zeros são ausências de registros associados ao cadastro de referência. Não equivalem a sinistros ocultos nem são ajustados por tráfego. Também não representam reprodução exata da amostra preliminar da autora.</p>
<h2>Auditoria dos registros</h2>{table(pd.DataFrame(q))}<p>A divergência aritmética de pessoas sinaliza casos para investigação. Não houve imputação nem correção automática. A classificação de gravidade foi derivada de mortos e feridos; o campo textual original foi preservado na base limpa.</p>
<h2>Disponibilidade ANTT</h2><p>Foram inspecionados cadastros de equipamentos, concessões, investimentos e passagens em praças de pedágio. No cadastro de trechos, UF apareceu com códigos numéricos em vez de siglas; não foi presumida uma conversão. Os volumes de praça representam passagens e não foram usados como VMD por trecho ou como denominador para comparar gestão direta e concessões.</p>
<h2>Limitações e requisitos de aprofundamento</h2><ul><li>A integração PNCT acrescenta taxas sobre exposição modelada nos dois arranjos; a incerteza do VMD não está incorporada aos intervalos. Consulte a seção Exposição e os coeficientes NB2.</li><li>Sem histórico validado de equipamentos e administração: não se testa efeito da visibilidade ou da concessão.</li><li>Cadastro atual pode introduzir incompatibilidade temporal.</li><li>Correlação espacial entre rodovias distintas e fatores não observados podem permanecer.</li><li>ICs descritivos de Wilson não incorporam dependência espacial.</li><li>Bootstrap mede incerteza dentro do universo observado, sem corrigir seleção.</li><li>Ausência de registro de intervenção não foi usada como evidência de inação.</li></ul>
<h2>Reprodução e fontes</h2><p>Scripts coletar.py, analisar.py, integrar_snv.py e publicar_resultados.py; pandas, NumPy, SciPy, Matplotlib e pyshp. SHA-256 dos arquivos no manifesto. Datas, exclusões e testes preservados. A versão do script principal está identificada nos metadados.</p><p><a href="https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf">PRF</a> · <a href="https://www.gov.br/dnit/pt-br/assuntos/atlas-e-mapas/pnv-e-snv">SNV/DNIT</a> · <a href="https://dados.antt.gov.br/">ANTT</a> · <a href="https://servicodados.ibge.gov.br/api/docs/malhas?versao=3">IBGE</a></p></html>'''
# Complemento executado: exposição modelada e modelos NB2.
ex=json.loads((OUT/'exposicao.json').read_text(encoding='utf8')) if False else json.loads((R/'dist/data/exposicao.json').read_text(encoding='utf8'))
nbsection='<h2>Exposição PNCT e modelos de contagem NB2</h2><p>VMD dos dois sentidos × extensão estimada × dias do ano; taxas por 100 milhões de veículos-km. Universo federal principal pavimentado ou duplicado. O VMD 2025 usa julho/2024–junho/2025. A exposição é modelada e sua incerteza não entra nos ICs.</p>'+table(pd.DataFrame(ex['groups']))
for outcome,m in ex['models'].items():
 nbsection+='<h3>'+('Mortes' if outcome=='mortos' else 'Sinistros')+'</h3>'+table(pd.DataFrame(m['terms']).query("term in ['concessao','dupla','log_vmda','pesados_10pp','nao_simulavel']"))
nbsection+='<p>A associação para mortes perde evidência estatística na análise sem segmentos não simuláveis. A comparação bruta e a ajustada podem ter sentidos diferentes; não há identificação causal de qualidade da governança.</p><h3>Validação temporal NB2</h3>'+table(pd.DataFrame([ex['validation']]))
report=report.replace('<h2>Limitações e requisitos de aprofundamento</h2>',nbsection+'<h2>Limitações e requisitos de aprofundamento</h2>')
(EXP/'relatorio-analitico.html').write_text(report,encoding='utf8')
print('VALIDAÇÃO',json.dumps(checks,ensure_ascii=False),flush=True)
