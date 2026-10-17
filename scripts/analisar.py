"""Análises de registros PRF, auditoria e inferência condicional reproduzíveis.
Não estima sub-registro nem efeitos causais. Sem dependência de statsmodels.
"""
from pathlib import Path
import json, zipfile, io, datetime, hashlib, unicodedata, re, math, csv
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.optimize import minimize
from scipy.stats import rankdata, t as student_t

ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data'; OUT=ROOT/'dist'/'data'
OUT.mkdir(parents=True,exist_ok=True); (ROOT/'dist'/'exports').mkdir(exist_ok=True)
def write(name,obj):
    text=json.dumps(obj,ensure_ascii=False,separators=(',',':'),allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x))
    (OUT/(name+'.json')).write_text(text,encoding='utf8')
    (OUT/(name+'.js')).write_text('window.'+name.upper()+'='+text+';',encoding='utf8')
def norm(x):return ''.join(c for c in unicodedata.normalize('NFKD',str(x)) if not unicodedata.combining(c)).lower().strip()
def readcsv(p):
    for enc in ['utf-8-sig','cp1252','latin1']:
        if hasattr(p,'seek'):p.seek(0)
        try:return pd.read_csv(p,sep=';',encoding=enc,low_memory=False)
        except UnicodeDecodeError:continue
def num(s):return pd.to_numeric(s.astype(str).str.replace(',','.',regex=False),errors='coerce')
frames=[]; audit=[]
for y in range(2022,2026):
    p=RAW/f'prf{y}.zip';z=zipfile.ZipFile(p);b=z.read(next(n for n in z.namelist() if n.endswith('.csv')))
    d=readcsv(io.BytesIO(b));d['ano']=y
    du=int(d.duplicated('id').sum());conflict=d[d.duplicated('id',keep=False)].groupby('id').apply(lambda g:len(g.drop_duplicates())>1,include_groups=False)
    badids=conflict[conflict].index
    d=d[~d.id.isin(badids)].drop_duplicates('id').copy()
    d['date']=pd.to_datetime(d.data_inversa,format='mixed',dayfirst=True,errors='coerce')
    for c in ['mortos','feridos_graves','feridos_leves','feridos','pessoas','ilesos','ignorados','veiculos','br','km','latitude','longitude']:
        d[c]=num(d[c])
    for c in ['tipo_pista','uso_solo','classificacao_acidente','tipo_acidente','condicao_metereologica','causa_acidente']:
        d[c]=d[c].fillna('Não informado').astype(str)
    d['fatal']=(d.mortos>0).astype(int)
    d['gravidade']=np.select([d.mortos>0,d.feridos>0,(d.mortos==0)&(d.feridos==0)],['Fatal','Com feridos','Sem vítimas'],default='Indeterminada')
    d['hora']=pd.to_numeric(d.horario.astype(str).str[:2],errors='coerce')
    d['mes']=d.date.dt.month.fillna(0).astype(int);d['semana']=d.date.dt.dayofweek.fillna(-1).astype(int)
    d['km10']=(np.floor(d.km/10)*10).where(d.km.between(0,2000),-1).fillna(-1).astype(int)
    loc=d.br.between(1,999)&d.km.between(0,2000)&d.uf.isin('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split())
    coord=d.latitude.between(-34,6)&d.longitude.between(-74,-34)
    d['loc_ok']=loc;d['coord_ok']=coord
    declared=d.classificacao_acidente.map(norm)
    mismatch=((declared=='com vitimas fatais')&(d.mortos==0))|((declared=='sem vitimas')&((d.mortos>0)|(d.feridos>0)))|((declared=='com vitimas feridas')&(d.mortos>0))
    row=dict(ano=y,linhas_brutas=len(pd.read_csv(io.BytesIO(b),sep=';',encoding='latin1',usecols=['id'])),ocorrencias=len(d),duplicados=du,ids_conflitantes=len(badids),mortos=int(d.mortos.sum()),feridos_graves=int(d.feridos_graves.sum()),feridos_leves=int(d.feridos_leves.sum()),sinistros_fatais=int(d.fatal.sum()),sem_vitimas=int((d.gravidade=='Sem vítimas').sum()),classificacao_ausente=int((declared=='nao informado').sum()),classificacao_divergente=int(mismatch.sum()),localizacao_invalida=int((~loc).sum()),coordenada_invalida=int((~coord).sum()),data_invalida=int(d.date.isna().sum()),ano_divergente=int((d.date.dt.year!=y).sum()),contagem_vitimas_divergente=int((d.pessoas!=d[['mortos','feridos_leves','feridos_graves','ilesos','ignorados']].sum(axis=1)).sum()))
    audit.append(row);frames.append(d);print('PRF',row,flush=True)
D=pd.concat(frames,ignore_index=True)
D.to_pickle(RAW/'prf-limpa.pkl')
write('auditoria',audit)
summary=D.groupby('ano').agg(ocorrencias=('id','size'),mortos=('mortos','sum'),feridos_graves=('feridos_graves','sum'),feridos_leves=('feridos_leves','sum'),fatais=('fatal','sum')).reset_index()
write('resumo',summary.to_dict('records'))

# Dicionários e registros compactos, sem identificadores pessoais.
cats={c:sorted(D[c].unique().tolist()) for c in ['uf','tipo_pista','uso_solo','tipo_acidente','gravidade','condicao_metereologica']}
maps={c:{v:i for i,v in enumerate(vals)} for c,vals in cats.items()}
columns=['ano','uf','br','km10','mes','hora','semana','tipo_pista','uso_solo','tipo_acidente','gravidade','mortos','feridos_graves','feridos_leves','condicao_metereologica']
compact=D[columns].copy()
for c in cats:compact[c]=compact[c].map(maps[c])
compact['hora']=compact.hora.fillna(-1)
compact['br']=compact.br.fillna(-1)
arr=compact.fillna(0).astype(int).values.tolist()
write('registros',dict(columns=columns,cats=cats,rows=arr))

# Centro aproximado dos intervalos de quilometragem somente a partir de coordenadas plausíveis.
geo=D[D.loc_ok&D.coord_ok].groupby(['uf','br','km10']).agg(lat=('latitude','median'),lon=('longitude','median'),n=('id','size')).reset_index()
write('centros',[[r.uf,int(r.br),int(r.km10),round(r.lon,4),round(r.lat,4),int(r.n)] for r in geo.itertuples()])
if (RAW/'brasil-ufs.geojson').exists():
    g=json.loads((RAW/'brasil-ufs.geojson').read_text(encoding='utf8'));write('malha',g)

# Modelo logístico: probabilidade condicional de fatalidade em um sinistro REGISTRADO.
M=D[D.mortos.notna()&D.tipo_pista.isin(['Simples','Dupla','Múltipla'])&D.uso_solo.isin(['Sim','Não'])&D.hora.between(0,23)&D.uf.isin(cats['uf'])&D.br.between(1,999)].copy()
M['noite']=(M.hora.ge(18)|M.hora.lt(6)).astype(int);M['urbano']=(M.uso_solo=='Sim').astype(int)
M['dupla']=(M.tipo_pista=='Dupla').astype(int);M['multipla']=(M.tipo_pista=='Múltipla').astype(int)
M['chuva']=M.condicao_metereologica.map(norm).str.contains('chuva').astype(int)
M['fim_semana']=M.semana.isin([5,6]).astype(int)
M['cluster']=M.uf+'-'+M.br.astype(int).astype(str)
basecols=['noite','urbano','dupla','multipla','chuva','fim_semana']
def design(d,year=True):
    x=d[basecols].astype(float).copy()
    for uf in cats['uf'][1:]:x['UF_'+uf]=(d.uf==uf).astype(float)
    if year:
        for y in [2023,2024,2025]:x['Ano_'+str(y)]=(d.ano==y).astype(float)
    x.insert(0,'Intercepto',1.0);return x
def fit(d,year=True):
    # Agrupar perfis idênticos mantém a verossimilhança binomial e reduz o custo.
    keys=basecols+['uf','ano','cluster'];agg=d.groupby(keys,observed=True).agg(n=('fatal','size'),s=('fatal','sum')).reset_index()
    xf=design(agg,year);X=xf.values;N=agg.n.values;Y=agg.s.values
    def fun(b):
        eta=X@b;return float(np.sum(N*np.logaddexp(0,eta)-Y*eta)),X.T@(N*expit(eta)-Y)
    b0=np.zeros(X.shape[1]);b0[0]=math.log(Y.sum()/(N.sum()-Y.sum()))
    opt=minimize(fun,b0,jac=True,method='BFGS',options={'gtol':1e-6,'maxiter':400})
    b=opt.x;p=expit(X@b);H=X.T@((N*p*(1-p))[:,None]*X);bread=np.linalg.pinv(H)
    scores=X*(Y-N*p)[:,None];sdf=pd.DataFrame(scores);sdf['cluster']=agg.cluster.values
    cluster_scores=sdf.groupby('cluster').sum().values;G=len(cluster_scores);n=int(N.sum());k=len(b)
    cov=bread@(cluster_scores.T@cluster_scores)@bread*(G/(G-1))*((n-1)/(n-k));se=np.sqrt(np.diag(cov));q=student_t.ppf(.975,G-1)
    results=[]
    for i,name in enumerate(xf.columns):
        results.append(dict(term=name,beta=float(b[i]),se=float(se[i]),odds_ratio=float(np.exp(b[i])),low=float(np.exp(b[i]-q*se[i])),high=float(np.exp(b[i]+q*se[i])),p=float(2*student_t.sf(abs(b[i]/se[i]),G-1))))
    return b,results,dict(n=n,clusters=G,iterations=int(opt.nit),converged=bool(np.max(np.abs(fun(b)[1]))<.01),max_gradient=float(np.max(np.abs(fun(b)[1]))),loglik=-float(fun(b)[0]),features=list(xf.columns))
b,terms,meta=fit(M)
train=M[M.ano<=2023];test=M[M.ano>=2024]
bt,_,mt=fit(train,False);pt=expit(design(test,False).values@bt);yt=test.fatal.values
auc=float((rankdata(pt)[yt==1].sum()-yt.sum()*(yt.sum()+1)/2)/(yt.sum()*(len(yt)-yt.sum())))
brier=float(np.mean((pt-yt)**2));base=float(train.fatal.mean());nullb=float(np.mean((base-yt)**2))
cal=[]
dec=pd.qcut(pt,10,labels=False,duplicates='drop')
for k in sorted(set(dec)):
    ix=dec==k;n=int(ix.sum());s=int(yt[ix].sum());p=s/n;z=1.96;den=1+z*z/n;center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    cal.append(dict(decile=int(k)+1,n=n,pred=float(pt[ix].mean()),obs=p,low=float(center-half),high=float(center+half)))
sens=M[M.classificacao_acidente!='Não informado'];bs,ts,ms=fit(sens)
model=dict(meta=meta,terms=terms,validation=dict(train_years=[2022,2023],test_years=[2024,2025],n_train=len(train),n_test=len(test),auc=auc,brier=brier,baseline_brier=nullb,calibration=cal),sensitivity=dict(label='Exclusão de classificação original ausente',n=len(sens),terms=[t for t in ts if t['term'] in basecols]),scope='Probabilidade de um sinistro registrado ter ao menos uma morte; sem interpretação causal e sem estimativa de risco por veículo-quilômetro.',exclusions=len(D)-len(M))
write('modelo',model)
pd.DataFrame(terms).to_csv(ROOT/'dist'/'exports'/'modelo-logistico.csv',index=False,encoding='utf-8-sig')
print('MODELO',meta,'AUC',auc,'BRIER',brier,flush=True)

# Persistência temporal: intervalos fixos de 10 km presentes em pelo menos um ano.
P=D[D.loc_ok].groupby(['uf','br','km10','ano']).agg(n=('id','size'),mortos=('mortos','sum'),graves=('feridos_graves','sum')).reset_index()
keys=P[['uf','br','km10']].drop_duplicates();panel=keys.merge(pd.DataFrame({'ano':[2022,2023,2024,2025]}),how='cross').merge(P,how='left').fillna(0)
early=panel[panel.ano<=2023].groupby(['uf','br','km10']).agg(n_pre=('n','sum'),m_pre=('mortos','sum'))
late=panel[panel.ano>=2024].groupby(['uf','br','km10']).agg(n_pos=('n','sum'),m_pos=('mortos','sum'))
rank=early.join(late).reset_index();rank['cluster']=rank.uf+'-'+rank.br.astype(int).astype(str)
cut=float(rank.m_pre.quantile(.8));rank['alto_pre']=rank.m_pre>=max(1,cut)
rho=float(rank[['m_pre','m_pos']].corr(method='spearman').iloc[0,1])
# Bootstrap por corredor UF-BR, preserva dependência entre intervalos do mesmo corredor.
rng=np.random.default_rng(20261017);cs=rank.cluster.unique();stats=[]
parts={k:g for k,g in rank.groupby('cluster')}
for _ in range(500):
    sample=pd.concat([parts[k] for k in rng.choice(cs,len(cs),replace=True)],ignore_index=True)
    stats.append(float(sample[['m_pre','m_pos']].corr(method='spearman').iloc[0,1]))
persist=dict(n_segments=len(rank),n_clusters=len(cs),rho=rho,rho_low=float(np.quantile(stats,.025)),rho_high=float(np.quantile(stats,.975)),bootstrap=500,seed=20261017,cut_mortes_pre=max(1,cut),universe='Intervalos UF–BR de 10 km com pelo menos uma ocorrência entre 2022 e 2025; não representa toda a malha nem identifica trechos sem registro em todo o período.',rows=rank[['uf','br','km10','n_pre','m_pre','n_pos','m_pos','alto_pre']].values.tolist())
write('persistencia',persist)
rank.to_csv(ROOT/'dist'/'exports'/'persistencia-intervalos-10km.csv',index=False,encoding='utf-8-sig')
summary.to_csv(ROOT/'dist'/'exports'/'indicadores-anuais.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(audit).to_csv(ROOT/'dist'/'exports'/'auditoria-prf.csv',index=False,encoding='utf-8-sig')

# Auditoria objetiva das bases ANTT realmente baixadas, sem confundir cadastro atual com histórico.
inventory=[];traffic=[]
selected=json.loads((RAW/'antt-selecao.json').read_text(encoding='utf8')) if (RAW/'antt-selecao.json').exists() else []
for fname,url in selected:
    p=RAW/fname
    if not p.exists():continue
    try:
        malformed=0
        try:a=readcsv(p)
        except pd.errors.ParserError:
            raw=p.read_bytes()
            try:text=raw.decode('utf-8-sig')
            except UnicodeDecodeError:text=raw.decode('latin1')
            rr=list(csv.reader(io.StringIO(text),delimiter=';'));header=rr[0]
            valid=[r for r in rr[1:] if len(r)==len(header)];malformed=len(rr)-1-len(valid)
            a=pd.DataFrame(valid,columns=header).replace('',np.nan)
        dates={}
        for c in a:
            if any(t in c.lower() for t in ['data','mes_ano','ano_']):
                vals=a[c].dropna().astype(str);dates[c]=dict(preenchidos=len(vals),exemplos=vals.head(3).tolist())
        inventory.append(dict(file=fname,url=url,rows=len(a),malformed_rows=malformed,columns=list(a.columns),missing={c:int(a[c].isna().sum()) for c in a},dates=dates,concessionarias=int(a.concessionaria.nunique()) if 'concessionaria' in a else None))
        if 'volume-trafego-praca-pedagio' in fname:
            datecol=next((c for c in ['mes_ano','data','mes'] if c in a),None)
            volcol=next((c for c in ['volume_total','volume'] if c in a),None)
            if datecol and volcol:
                a['date']=pd.to_datetime(a[datecol],dayfirst=True,format='mixed',errors='coerce');a['volume']=num(a[volcol]);a['ano']=a.date.dt.year;a['mes']=a.date.dt.month
                a=a[a.ano.between(2022,2025)]
                for (conc,year,month),g in a.groupby(['concessionaria','ano','mes']):traffic.append(dict(concessionaria=conc,ano=int(year),mes=int(month),volume=float(g.volume.sum()),pracas=int(g.praca.nunique()) if 'praca' in g else None,source=fname))
    except Exception as e:inventory.append(dict(file=fname,url=url,error=str(e)))
write('inventario',inventory);write('trafego',traffic)
write('metadados',dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),period=[2022,2025],n=len(D),pipeline_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),libraries=dict(pandas=pd.__version__,numpy=np.__version__),seed=20261017))
print('CONCLUIDO',len(D),'registros',len(geo),'centros',flush=True)
