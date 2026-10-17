from pathlib import Path
import json,unicodedata
import numpy as np,pandas as pd
from scipy.special import logsumexp
from scipy.optimize import minimize
from scipy.stats import t
R=Path(__file__).resolve().parents[1];D=pd.read_pickle(R/'data/prf-limpa.pkl')
M=D[D.mortos.notna()&D.tipo_pista.isin(['Simples','Dupla','Múltipla'])&D.uso_solo.isin(['Sim','Não'])&D.hora.between(0,23)&D.br.between(1,999)].copy()
M['outcome']=np.select([M.mortos>0,M.feridos_graves>0,M.feridos_leves>0],[3,2,1],default=0)
M['noite']=(M.hora.ge(18)|M.hora.lt(6)).astype(int);M['urbano']=(M.uso_solo=='Sim').astype(int);M['dupla']=(M.tipo_pista=='Dupla').astype(int);M['multipla']=(M.tipo_pista=='Múltipla').astype(int)
M['chuva']=M.condicao_metereologica.str.lower().str.contains('chuva').astype(int);M['fim_semana']=M.semana.isin([5,6]).astype(int);M['cluster']=M.uf+'-'+M.br.astype(int).astype(str)
base=['noite','urbano','dupla','multipla','chuva','fim_semana'];ufs=sorted(M.uf.unique());top=M[M.ano<=2023].tipo_acidente.value_counts().head(6).index.tolist();M['tipo']=M.tipo_acidente.where(M.tipo_acidente.isin(top),'Outros tipos')
labels=['Sem vítimas','Somente feridos leves','Com feridos graves, sem mortes','Com mortes'];types=['Outros tipos']+top

def design(d,year=True,withtype=True):
 x=d[base].astype(float).copy()
 if withtype:
  for typ in top:x['Tipo: '+typ]=(d.tipo==typ).astype(float)
 for uf in ufs[1:]:x['UF_'+uf]=(d.uf==uf).astype(float)
 if year:
  for yr in [2023,2024,2025]:x['Ano_'+str(yr)]=(d.ano==yr).astype(float)
 x.insert(0,'Intercepto',1.);return x

def fit(d,year=True,withtype=True):
 keys=base+['uf','ano','cluster']+(['tipo'] if withtype else [])
 agg=d.groupby(keys+['outcome'],observed=True).size().unstack('outcome',fill_value=0).reindex(columns=range(4),fill_value=0).reset_index()
 xf=design(agg,year,withtype);X=xf.to_numpy();Y=agg[list(range(4))].to_numpy();N=Y.sum(axis=1);n=N.sum();k=X.shape[1]
 def fun(theta):
  B=theta.reshape(3,k);eta=np.column_stack([np.zeros(len(X)),X@B.T]);lp=eta-logsumexp(eta,axis=1,keepdims=True);p=np.exp(lp)
  return -float((Y*lp).sum()/n),((N[:,None]*p[:,1:]-Y[:,1:]).T@X/n).ravel()
 b=np.zeros((3,k));tot=Y.sum(axis=0);b[:,0]=np.log(tot[1:]/tot[0]);opt=minimize(fun,b.ravel(),jac=True,method='L-BFGS-B',options={'maxiter':1200,'gtol':1e-9,'ftol':1e-14,'maxcor':30})
 B=opt.x.reshape(3,k);eta=np.column_stack([np.zeros(len(X)),X@B.T]);p=np.exp(eta-logsumexp(eta,axis=1,keepdims=True))
 H=np.block([[X.T@((N*p[:,a+1]*((1 if a==b else 0)-p[:,b+1]))[:,None]*X) for b in range(3)] for a in range(3)])
 scores=np.concatenate([X*(Y[:,a+1]-N*p[:,a+1])[:,None] for a in range(3)],axis=1);sd=pd.DataFrame(scores);sd['cluster']=agg.cluster.values;S=sd.groupby('cluster').sum().to_numpy();G=len(S);bread=np.linalg.pinv(H);cov=bread@(S.T@S)@bread*(G/(G-1))*((n-1)/(n-3*k));se=np.sqrt(np.maximum(np.diag(cov),0));q=t.ppf(.975,G-1)
 terms=[]
 for a in range(3):
  for j,name in enumerate(xf.columns):
   idx=a*k+j;beta=B[a,j];terms.append(dict(outcome=labels[a+1],term=name,beta=float(beta),se=float(se[idx]),rrr=float(np.exp(beta)),low=float(np.exp(beta-q*se[idx])),high=float(np.exp(beta+q*se[idx]))))
 # Independent numerical gradient check on selected coordinates.
 eps=1e-5;checks=[]
 for j in [0,k,2*k,min(len(opt.x)-1,2*k+5)]:
  step=np.zeros_like(opt.x);step[j]=eps;checks.append(abs((fun(opt.x+step)[0]-fun(opt.x-step)[0])/(2*eps)-fun(opt.x)[1][j]))
 meta=dict(n=int(n),clusters=G,features=list(xf.columns),profiles=len(X),iterations=opt.nit,max_gradient=float(np.max(np.abs(fun(opt.x)[1]*n))),max_gradient_per_observation=float(np.max(np.abs(fun(opt.x)[1]))),gradient_check_error=float(max(checks)),converged=bool(np.max(np.abs(fun(opt.x)[1]))<1e-7),hessian_rank=int(np.linalg.matrix_rank(H)),parameters=3*k,loglik=float(-fun(opt.x)[0]*n),reference=labels[0])
 print('MULTINOMIAL',meta,flush=True);assert meta['converged'];assert meta['hessian_rank']==meta['parameters'];assert meta['gradient_check_error']<1e-7
 return dict(meta=meta,terms=terms),B
model,B=fit(M)
train=M[M.ano<=2023];test=M[M.ano>=2024];valid,Bt=fit(train,False);xt=design(test,False).reindex(columns=valid['meta']['features'],fill_value=0).to_numpy();eta=np.column_stack([np.zeros(len(xt)),xt@Bt.T]);pt=np.exp(eta-logsumexp(eta,axis=1,keepdims=True));yt=test.outcome.to_numpy();baseline=np.bincount(train.outcome,minlength=4)/len(train);onehot=np.eye(4)[yt];conf=pd.crosstab(pd.Series(yt,name='observado'),pd.Series(pt.argmax(axis=1),name='previsto')).reindex(index=range(4),columns=range(4),fill_value=0)
validation=dict(train=[2022,2023],test=[2024,2025],n_train=len(train),n_test=len(test),log_loss=float(-np.log(pt[np.arange(len(yt)),yt]).mean()),baseline_log_loss=float(-np.log(baseline[yt]).mean()),brier_multiclasse=float(np.mean(np.sum((pt-onehot)**2,axis=1))),baseline_brier=float(np.mean(np.sum((baseline-onehot)**2,axis=1))),accuracy=float(np.mean(pt.argmax(axis=1)==yt)),baseline_accuracy=float(np.mean(yt==baseline.argmax())),confusion=conf.values.tolist(),classes=labels)
cal=[]
for j,label in enumerate(labels):
 pred=pt[:,j];obs=(yt==j).astype(int);bins=pd.qcut(pred,10,labels=False,duplicates='drop')
 for b in sorted(set(bins)):
  ix=bins==b;cal.append(dict(outcome=label,decile=int(b)+1,n=int(ix.sum()),pred=float(pred[ix].mean()),obs=float(obs[ix].mean())))
validation['calibration']=cal
simple,_=fit(M,withtype=False)
obj=dict(**model,validation=validation,counts={labels[i]:int((M.outcome==i).sum()) for i in range(4)},exclusions=len(D)-len(M),type_levels=types,sensitivity=dict(label='Sem controle pelo tipo de sinistro',terms=[t for t in simple['terms'] if t['term'] in base]),scope='Gravidade máxima nas ocorrências registradas; RRR compara a razão de probabilidades de cada desfecho versus sem vítimas. Não é risco relativo marginal, efeito causal ou risco por viagem. Tipo de sinistro é conhecido após o evento; modelo não é previsão prévia de acidentes.')
s=json.dumps(obj,ensure_ascii=False,separators=(',',':'),allow_nan=False);(R/'dist/data/multinomial.json').write_text(s,encoding='utf-8');(R/'dist/data/multinomial.js').write_text('window.MULTINOMIAL='+s+';',encoding='utf-8');pd.DataFrame(model['terms']).to_csv(R/'dist/exports/modelo-multinomial.csv',index=False,encoding='utf-8-sig')
print('VALIDAÇÃO MULTICLASSE',validation['log_loss'],validation['baseline_log_loss'],flush=True)
