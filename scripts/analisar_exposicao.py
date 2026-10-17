"""PRF–PNCT: integração anual e modelos de contagem com exposição modelada.
Esta análise não identifica efeitos causais nem sinistros não registrados.
"""
from pathlib import Path
import json,calendar,math,datetime
import pandas as pd,numpy as np
from scipy.special import gammaln,digamma
from scipy.optimize import minimize
from scipy.stats import t as student_t
R=Path(__file__).resolve().parents[1];O=R/'dist'/'data';D=pd.read_pickle(R/'data'/'prf-limpa.pkl')
def write(n,obj):
 t=json.dumps(obj,ensure_ascii=False,separators=(',',':'),allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x));(O/(n+'.json')).write_text(t,encoding='utf8');(O/(n+'.js')).write_text('window.'+n.upper()+'='+t+';',encoding='utf8')
panels=[];coverage=[]
for y in range(2022,2026):
 S=pd.read_csv(R/'data'/f'pnct-{y}-sheet2.csv');S.columns=S.columns.str.strip()
 for a,b in [('km_i_estim','vl_km_i_estim'),('km_f_estim','vl_km_f_estim'),('ext_estim','vl_ext_estim'),('classifica','classificação')]:
  if a in S:S=S.rename(columns={a:b})
 S['ano']=y;S['br']=pd.to_numeric(S.vl_br,errors='coerce');S['uf']=S.sg_uf
 S['vmda']=pd.to_numeric(S.VMDa_C,errors='coerce')+pd.to_numeric(S.VMDa_D,errors='coerce')
 S['ext']=pd.to_numeric(S.vl_km_f_estim,errors='coerce')-pd.to_numeric(S.vl_km_i_estim,errors='coerce')
 S['admin']=np.select([S.ds_tipo_ad.eq('Concessão Federal'),S.ds_tipo_ad.eq('Federal')],['Concessão no cadastro PNCT','Administração federal no cadastro PNCT'],default='Outros arranjos')
 S['concessao']=(S.ds_tipo_ad=='Concessão Federal').astype(int);S['dupla']=(S.ds_sup_fed=='DUP').astype(int)
 S['nao_simulavel']=S['classificação'].fillna('').str.contains('Não Simulável',case=False).astype(int)
 S['referencial']=S['classificação'].fillna('').eq('Referencial').astype(int)
 heavy=[f'{c}_{d}' for d in ['C','D'] for c in 'ABCDEFGH'];S['pesados']=S[heavy].apply(pd.to_numeric,errors='coerce').sum(axis=1)/S.vmda
 S['exposicao']=S.vmda*S.ext*(366 if calendar.isleap(y) else 365)
 S['eligible']=(S.sg_tipo_tr=='B')&(S.ds_jurisdi=='Federal')&S.ds_sup_fed.isin(['PAV','DUP'])&(S.ext>0)&(S.vmda>0)
 S=S[S.eligible].copy().reset_index(drop=True)
 E=D[D.ano==y].copy();E['pnct_idx']=-1;E['ambiguous']=False
 for (uf,br),g in E[E.loc_ok].groupby(['uf','br']):
  seg=S[(S.uf==uf)&(S.br==br)]
  if seg.empty:continue
  km=g.km.to_numpy();lo=seg.vl_km_i_estim.to_numpy();hi=seg.vl_km_f_estim.to_numpy();ma=(km[:,None]>=lo)&(km[:,None]<hi)
  end=km==hi.max()
  if end.any():ma[end,:]=(hi==hi.max())[None,:]
  unique=ma.sum(axis=1)==1;E.loc[g.index[unique],'pnct_idx']=seg.index.to_numpy()[ma[unique].argmax(axis=1)]
  E.loc[g.index[ma.sum(axis=1)>1],'ambiguous']=True
 agg=E[E.pnct_idx>=0].groupby('pnct_idx').agg(n=('id','size'),mortos=('mortos','sum'),fatais=('fatal','sum'),graves=('feridos_graves','sum'))
 S=S.join(agg).fillna({'n':0,'mortos':0,'fatais':0,'graves':0})
 S['cluster']=S.uf+'-'+S.br.astype(int).astype(str)
 S['log_vmd']=np.log(S.vmda/10000);S['pesados_10pp']=S.pesados/.1
 coverage.append(dict(ano=y,linhas_originais=int(len(pd.read_csv(R/'data'/f'pnct-{y}-sheet2.csv'))),segmentos_elegiveis=len(S),ocorrencias_prf=len(E),ocorrencias_vinculadas=int((E.pnct_idx>=0).sum()),ambiguous=int(E.ambiguous.sum()),mortos_vinculados=int(S.mortos.sum()),segmentos_sem_registro=int((S.n==0).sum()),exposicao=float(S.exposicao.sum()),vmda_min=float(S.vmda.min()),vmda_max=float(S.vmda.max()),versao_snv=sorted(S.versao_snv.unique().tolist())))
 panels.append(S)
 print('COBERTURA',coverage[-1],flush=True)
P=pd.concat(panels,ignore_index=True);P.to_pickle(R/'data'/'painel-pnct.pkl')
exportcols=['ano','ID','vl_codigo','uf','br','vl_km_i_estim','vl_km_f_estim','ext','vmda','exposicao','admin','ds_tipo_ad','ds_sup_fed','versao_snv','classificação','referencial','nao_simulavel','pesados','n','mortos','fatais','graves','cluster','concessao','dupla','log_vmd','pesados_10pp']
P[exportcols].to_csv(R/'dist'/'exports'/'painel-prf-pnct.csv',index=False,encoding='utf-8-sig')
UF=sorted(P.uf.unique());base=['concessao','dupla','log_vmd','pesados_10pp','nao_simulavel']
def design(d,year=True):
 X=d[base].astype(float).copy()
 for u in UF[1:]:X['UF_'+u]=(d.uf==u).astype(float)
 if year:
  for a in [2023,2024,2025]:
   if a in d.ano.unique():X['Ano_'+str(a)]=(d.ano==a).astype(float)
 X.insert(0,'Intercepto',1.);return X
def fit(d,outcome,year=True):
 xf=design(d,year);xf=xf[[c for c in xf if c=='Intercepto' or xf[c].nunique()>1]];X=xf.values;y=d[outcome].to_numpy(float);offset=np.log(d.exposicao.to_numpy()/1e8);k=X.shape[1]
 # Poisson para inicialização e diagnóstico, não assume equidispersão válida.
 def pf(b):
  eta=np.clip(offset+X@b,-30,30);mu=np.exp(eta);return float(np.sum(mu-y*eta)),X.T@(mu-y)
 init=np.zeros(k);init[0]=math.log((y.sum()+.1)/np.exp(offset).sum())
 po=minimize(pf,init,jac=True,method='BFGS',options={'maxiter':300,'gtol':1e-6});mu0=np.exp(offset+X@po.x)
 pearson=float(np.sum((y-mu0)**2/mu0)/(len(y)-k));llpois=float(np.sum(y*np.log(mu0)-mu0-gammaln(y+1)))
 def f(theta):
  b=theta[:-1];alpha=np.exp(theta[-1]);r=1/alpha;eta=np.clip(offset+X@b,-30,30);mu=np.exp(eta)
  ll=gammaln(y+r)-gammaln(r)-gammaln(y+1)+r*(np.log(r)-np.log(r+mu))+y*(eta-np.log(r+mu))
  sb=X.T@(r*(y-mu)/(r+mu))
  sr=digamma(y+r)-digamma(r)+np.log(r)+1-np.log(r+mu)-(r+y)/(r+mu)
  return -float(ll.sum()),-np.r_[sb,(-r*sr).sum()]
 theta=np.r_[po.x,np.log(max(.05,(np.var(y)-np.mean(y))/(np.mean(y)**2+.001)))]
 opt=minimize(f,theta,jac=True,method='BFGS',options={'maxiter':500,'gtol':1e-6});theta=opt.x;b=theta[:-1];alpha=float(np.exp(theta[-1]));r=1/alpha;mu=np.exp(offset+X@b)
 eps=1e-5;H=np.column_stack([(f(theta+np.eye(len(theta))[j]*eps)[1]-f(theta-np.eye(len(theta))[j]*eps)[1])/(2*eps) for j in range(len(theta))]);H=(H+H.T)/2
 sb=X*(r*(y-mu)/(r+mu))[:,None];sr=digamma(y+r)-digamma(r)+np.log(r)+1-np.log(r+mu)-(r+y)/(r+mu);scores=np.column_stack([sb,-r*sr]);sd=pd.DataFrame(scores);sd['cluster']=d.cluster.values;s=sd.groupby('cluster').sum().values;G=len(s);n=len(y);bread=np.linalg.pinv(H);cov=bread@(s.T@s)@bread*(G/(G-1))*((n-1)/(n-len(theta)));se=np.sqrt(np.maximum(np.diag(cov),0));q=student_t.ppf(.975,G-1)
 ts=[]
 for i,name in enumerate(xf.columns):ts.append(dict(term=name,beta=float(b[i]),se=float(se[i]),irr=float(np.exp(b[i])),low=float(np.exp(b[i]-q*se[i])),high=float(np.exp(b[i]+q*se[i])),p=float(2*student_t.sf(abs(b[i]/se[i]),G-1))))
 return dict(outcome=outcome,meta=dict(n=n,clusters=G,features=list(xf.columns),alpha=alpha,max_gradient=float(np.max(np.abs(f(theta)[1]))),converged=bool(np.max(np.abs(f(theta)[1]))<.02),loglik=-f(theta)[0],aic=2*len(theta)+2*f(theta)[0],poisson_aic=2*k-2*llpois,poisson_pearson=pearson),terms=ts),b
M=P[P.admin!='Outros arranjos'].copy()
models={}
for outcome in ['n','mortos']:
 mod,b=fit(M,outcome);models[outcome]=mod;print('NB2',outcome,mod['meta'],flush=True)
sens={}
for name,df in [('sem_2025',M[M.ano<2025]),('sem_nao_simulavel',M[M.nao_simulavel==0])]:
 mod,_=fit(df,'mortos');sens[name]=mod
# Avaliação preditiva temporal de contagens observadas, não de eventos ocultos.
train=M[M.ano<=2023];test=M[M.ano>=2024];hold,b=fit(train,'mortos',False);pred=np.exp(np.log(test.exposicao.to_numpy()/1e8)+design(test,False).reindex(columns=hold['meta']['features'],fill_value=0).values@b)
validation=dict(train_years=[2022,2023],test_years=[2024,2025],n_train=len(train),n_test=len(test),observed=float(test.mortos.sum()),predicted=float(pred.sum()),mae=float(np.mean(np.abs(pred-test.mortos))),mean_poisson_deviance=float(np.mean(2*(np.where(test.mortos>0,test.mortos*np.log(np.maximum(test.mortos,1)/pred),0)-test.mortos+pred))))
groups=[]
for (year,admin),g in P.groupby(['ano','admin']):
 groups.append(dict(ano=int(year),admin=admin,segmentos=len(g),sinistros=int(g.n.sum()),mortos=int(g.mortos.sum()),exposicao=float(g.exposicao.sum()),taxa_sinistros=float(1e8*g.n.sum()/g.exposicao.sum()),taxa_mortes=float(1e8*g.mortos.sum()/g.exposicao.sum()),zeros=int((g.n==0).sum())))
rows=P[['ano','uf','br','vl_km_i_estim','vl_km_f_estim','ext','vmda','exposicao','admin','n','mortos','graves','referencial','nao_simulavel','vl_codigo']].replace({np.nan:None}).values.tolist()
write('exposicao',dict(coverage=coverage,groups=groups,models=models,sensitivity=sens,validation=validation,rows=rows,columns=['ano','uf','br','km_i','km_f','ext','vmda','exposicao','admin','n','mortos','graves','referencial','nao_simulavel','codigo'],scope='Taxas sobre exposição modelada PNCT; classificação institucional do cadastro de cada planilha, não validação do regime vigente em cada data. Associações observacionais. VMD 2025 usa janela de julho/2024 a junho/2025, conforme nota técnica.',main_sample=len(M)))
for k,m in models.items():pd.DataFrame(m['terms']).to_csv(R/'dist'/'exports'/f'nb2-{k}.csv',index=False,encoding='utf-8-sig')
print('EXPOSIÇÃO CONCLUÍDA',len(P),'segmentos-ano',validation,flush=True)
