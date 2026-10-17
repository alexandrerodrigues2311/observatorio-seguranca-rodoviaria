"""Três extensões de ML com separação temporal e espacial e interpretação restrita.
Não identifica governança causal, sinistros ocultos ou eficácia institucional.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','4');os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
from pathlib import Path
import json,hashlib,warnings
import numpy as np,pandas as pd,sklearn
from scipy.special import softmax
from scipy.optimize import minimize_scalar
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from sklearn.preprocessing import OrdinalEncoder,RobustScaler
from sklearn.metrics import log_loss,accuracy_score,balanced_accuracy_score,f1_score,average_precision_score,confusion_matrix,mean_absolute_error,mean_poisson_deviance,silhouette_score,adjusted_rand_score
from sklearn.cluster import KMeans
from sklearn.inspection import permutation_importance
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits
threadpool_limits(4)
R=Path(__file__).resolve().parents[1];SEED=20261017;rng=np.random.default_rng(SEED);OUT=R/'dist/data';EXP=R/'dist/exports'
def save(name,obj):
 s=json.dumps(obj,ensure_ascii=False,separators=(',',':'),allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x));(OUT/(name+'.json')).write_text(s,encoding='utf-8');(OUT/(name+'.js')).write_text('window.'+name.upper()+'='+s+';',encoding='utf-8')
def hold(groups):return np.array([int(hashlib.sha256(('20261017|'+str(g)).encode()).hexdigest()[:8],16)%5==0 for g in groups])
def encode(train,test,nums,cats):
 enc=OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=np.nan,encoded_missing_value=np.nan);a=enc.fit_transform(train[cats].astype(str));b=enc.transform(test[cats].astype(str));return np.column_stack([train[nums].to_numpy(float),a]),np.column_stack([test[nums].to_numpy(float),b]),[False]*len(nums)+[True]*len(cats),enc
D=pd.read_pickle(R/'data/prf-limpa.pkl');M=D[D.mortos.notna()&D.tipo_pista.isin(['Simples','Dupla','Múltipla'])&D.uso_solo.isin(['Sim','Não'])&D.hora.between(0,23)&D.br.between(1,999)].copy()
M['outcome']=np.select([M.mortos>0,M.feridos_graves>0,M.feridos_leves>0],[3,2,1],default=0);M['noite']=(M.hora.ge(18)|M.hora.lt(6)).astype(int);M['urbano']=(M.uso_solo=='Sim').astype(int);M['dupla']=(M.tipo_pista=='Dupla').astype(int);M['multipla']=(M.tipo_pista=='Múltipla').astype(int);M['chuva']=M.condicao_metereologica.str.lower().str.contains('chuva').astype(int);M['fim_semana']=M.semana.isin([5,6]).astype(int);M['cluster']=M.uf+'-'+M.br.astype(int).astype(str)
numc=['noite','urbano','dupla','multipla','chuva','fim_semana'];catc=['uf','tipo'];top=M[M.ano==2022].tipo_acidente.value_counts().head(6).index.tolist();M['tipo']=M.tipo_acidente.where(M.tipo_acidente.isin(top),'Outros tipos')
configs=[dict(max_iter=100,max_leaf_nodes=7,l2_regularization=10.),dict(max_iter=180,max_leaf_nodes=15,l2_regularization=15.)]
labels=['Sem vítimas','Somente feridos leves','Com feridos graves, sem mortes','Com mortes']
def classmetrics(y,p):
 y=np.asarray(y);p=np.clip(p,1e-12,1);p/=p.sum(axis=1,keepdims=True);guess=p.argmax(1);cm=confusion_matrix(y,guess,labels=range(4));return dict(n=len(y),log_loss=float(log_loss(y,p,labels=range(4))),brier=float(np.mean(np.sum((np.eye(4)[y]-p)**2,axis=1))),accuracy=float(accuracy_score(y,guess)),balanced_accuracy=float(balanced_accuracy_score(y,guess)),macro_f1=float(f1_score(y,guess,average='macro',zero_division=0)),fatal_ap=float(average_precision_score(y==3,p[:,3])),fatal_prevalence=float(np.mean(y==3)),recall=(np.diag(cm)/cm.sum(1)).tolist(),confusion=cm.tolist())
def classifier(train,test,spatial=False):
 fit=train[train.ano==2022];val=train[train.ano==2023];a,b,mask,_=encode(fit,val,numc,catc);trials=[];best=None
 for cfg in configs:
  mod=HistGradientBoostingClassifier(**cfg,learning_rate=.08,min_samples_leaf=80,early_stopping=False,categorical_features=mask,random_state=SEED);mod.fit(a,fit.outcome);p=mod.predict_proba(b);loss=log_loss(val.outcome,p,labels=range(4));trials.append(dict(**cfg,validation_log_loss=float(loss)))
  if best is None or loss<best[0]:best=(loss,cfg,p)
 lp=np.log(np.clip(best[2],1e-12,1));temp=minimize_scalar(lambda t:log_loss(val.outcome,softmax(lp/t,axis=1),labels=range(4)),bounds=(.5,3),method='bounded').x
 a,b,mask,enc=encode(train,test,numc,catc);mod=HistGradientBoostingClassifier(**best[1],learning_rate=.08,min_samples_leaf=80,early_stopping=False,categorical_features=mask,random_state=SEED).fit(a,train.outcome);raw=mod.predict_proba(b);p=softmax(np.log(np.clip(raw,1e-12,1))/temp,axis=1);base=np.bincount(train.outcome,minlength=4)/len(train);result=dict(train_n=len(train),test_n=len(test),trials=trials,chosen=best[1],temperature=float(temp),raw=classmetrics(test.outcome,raw),calibrated=classmetrics(test.outcome,p),reference=classmetrics(test.outcome,np.tile(base,(len(test),1))),categorical_levels=[list(map(str,c)) for c in enc.categories_]);print('CLASSIFICADOR',spatial,result['calibrated'],flush=True)
 if not spatial:
  take=np.sort(np.random.default_rng(SEED).choice(len(test),min(15000,len(test)),replace=False));importance=permutation_importance(mod,b[take],test.outcome.to_numpy()[take],scoring='neg_log_loss',n_repeats=3,random_state=SEED,n_jobs=1);result['importance']=[dict(feature=f,delta_log_loss=float(v),sd=float(s)) for f,v,s in zip(numc+catc,importance.importances_mean,importance.importances_std)]
  cal=[]
  for j,label in enumerate(labels):
   bins=pd.qcut(p[:,j],10,labels=False,duplicates='drop')
   for k in sorted(set(bins)):
    ix=bins==k;cal.append(dict(outcome=label,decile=int(k)+1,n=int(ix.sum()),pred=float(p[ix,j].mean()),obs=float((test.outcome.to_numpy()[ix]==j).mean())))
  result['calibration']=cal
 return result
train=M[M.ano<=2023];test=M[M.ano>=2024];clf=classifier(train,test);clf_sp=classifier(train[~hold(train.cluster)],test[hold(test.cluster)],True)
clf['multinomial_reference']=json.loads((OUT/'multinomial.json').read_text(encoding='utf-8'))['validation'];assert set(train[~hold(train.cluster)].cluster).isdisjoint(set(test[hold(test.cluster)].cluster))
P=pd.read_pickle(R/'data/painel-pnct.pkl');P=P[P.admin!='Outros arranjos'].copy();nums=['dupla','log_vmd','pesados_10pp','concessao','nao_simulavel'];cats=['uf']
def regmetrics(y,p):return dict(n=len(y),observed=float(np.sum(y)),predicted=float(np.sum(p)),mae=float(mean_absolute_error(y,p)),poisson_deviance=float(mean_poisson_deviance(y,np.maximum(p,1e-10))))
def regression(train,test,spatial=False):
 fit=train[train.ano==2022];val=train[train.ano==2023];a,b,mask,_=encode(fit,val,nums,cats);e=fit.exposicao.to_numpy()/1e8;ev=val.exposicao.to_numpy()/1e8;trials=[];best=None
 for cfg in configs:
  mod=HistGradientBoostingRegressor(loss='poisson',**cfg,learning_rate=.06,min_samples_leaf=45,early_stopping=False,categorical_features=mask,random_state=SEED).fit(a,fit.mortos.to_numpy()/e,sample_weight=e/e.mean());pred=mod.predict(b)*ev;loss=mean_poisson_deviance(val.mortos,np.maximum(pred,1e-10));trials.append(dict(**cfg,validation_poisson_deviance=float(loss)))
  if best is None or loss<best[0]:best=(loss,cfg)
 a,b,mask,_=encode(train,test,nums,cats);e=train.exposicao.to_numpy()/1e8;et=test.exposicao.to_numpy()/1e8;mod=HistGradientBoostingRegressor(loss='poisson',**best[1],learning_rate=.06,min_samples_leaf=45,early_stopping=False,categorical_features=mask,random_state=SEED).fit(a,train.mortos.to_numpy()/e,sample_weight=e/e.mean());pred=mod.predict(b)*et;base=train.mortos.sum()/e.sum()*et;result=dict(train_n=len(train),test_n=len(test),trials=trials,chosen=best[1],model=regmetrics(test.mortos,pred),reference=regmetrics(test.mortos,base))
 if not spatial:
  def score(est,x,y):return -mean_poisson_deviance(y,np.maximum(est.predict(x)*et,1e-10))
  im=permutation_importance(mod,b,test.mortos.to_numpy(),scoring=score,n_repeats=3,random_state=SEED);result['importance']=[dict(feature=f,delta_deviance=float(v),sd=float(s)) for f,v,s in zip(nums+cats,im.importances_mean,im.importances_std)]
  export=test[['ano','uf','br','vl_km_i_estim','vl_km_f_estim','exposicao','admin','mortos']].copy();export['predicted']=pred;export['observed_minus_predicted']=export.mortos-pred;export.to_csv(EXP/'ml-regressao-predicoes.csv',index=False,encoding='utf-8-sig')
  bins=pd.qcut(pred,10,labels=False,duplicates='drop');result['calibration']=[dict(decile=int(k)+1,n=int((bins==k).sum()),predicted=float(pred[bins==k].sum()),observed=int(test.mortos.to_numpy()[bins==k].sum())) for k in sorted(set(bins))]
 print('REGRESSÃO',spatial,result['model'],flush=True);return result
tr=P[P.ano<=2023];te=P[P.ano>=2024];reg=regression(tr,te);reg_sp=regression(tr[~hold(tr.cluster)],te[hold(te.cluster)],True);reg['nb2_reference']=json.loads((OUT/'exposicao.json').read_text(encoding='utf-8'))['validation']
# Clusters are descriptive profiles of a stable early-period physical segment cohort.
keys=['uf','br','vl_km_i_estim','vl_km_f_estim'];early=P[P.ano<=2023];C=early.groupby(keys).agg(years=('ano','nunique'),vmda=('vmda','mean'),pesados=('pesados','mean'),dupla=('dupla','mean'),exposicao=('exposicao','sum'),n=('n','sum'),mortos=('mortos','sum'),admin=('admin',lambda x:'Misto no cadastro' if x.nunique()>1 else x.iloc[0])).reset_index();C=C[C.years==2].copy().reset_index(drop=True);C['log_vmda']=np.log(C.vmda);C['taxa_mortes']=1e8*C.mortos/C.exposicao;C['taxa_sinistros']=1e8*C.n/C.exposicao;C['log_taxa_mortes']=np.log1p(C.taxa_mortes);C['log_taxa_sinistros']=np.log1p(C.taxa_sinistros);features=['log_vmda','pesados','dupla','log_taxa_mortes','log_taxa_sinistros'];sc=RobustScaler();Z=np.clip(sc.fit_transform(C[features]),-5,5);trials=[];models={};sample=min(2000,len(C))
for k in range(2,7):
 km=KMeans(n_clusters=k,n_init=20,random_state=SEED).fit(Z);counts=np.bincount(km.labels_,minlength=k);sil=silhouette_score(Z,km.labels_,sample_size=sample,random_state=SEED);aris=[]
 for repeat in range(8):
  ix=np.random.default_rng(SEED+repeat).choice(len(Z),int(.8*len(Z)),replace=False);other=KMeans(n_clusters=k,n_init=10,random_state=SEED+repeat).fit(Z[ix]);aris.append(adjusted_rand_score(km.labels_,other.predict(Z)))
 trials.append(dict(k=k,silhouette=float(sil),ari_mean=float(np.mean(aris)),ari_min=float(np.min(aris)),min_share=float(counts.min()/len(C))));models[k]=km
eligible=[x for x in trials if x['min_share']>=.05 and x['ari_mean']>=.7];choice=max(eligible or trials,key=lambda x:x['silhouette']);km=models[choice['k']];C['group']=km.labels_+1;coords=PCA(n_components=2,random_state=SEED).fit_transform(Z);summ=[]
for group,g in C.groupby('group'):
 summ.append(dict(group=int(group),segments=len(g),vmda_median=float(g.vmda.median()),heavy_median=float(g.pesados.median()),dupla_share=float(g.dupla.mean()),mortos=int(g.mortos.sum()),n=int(g.n.sum()),exposure=float(g.exposicao.sum()),death_rate=float(1e8*g.mortos.sum()/g.exposicao.sum()),crash_rate=float(1e8*g.n.sum()/g.exposicao.sum())))
# Later outcomes are a description of exactly matching physical intervals, not cluster validation by labels.
late=P[P.ano>=2024].groupby(keys).agg(late_years=('ano','nunique'),late_exposure=('exposicao','sum'),late_deaths=('mortos','sum')).reset_index();later=C[keys+['group']].merge(late,on=keys,how='left');coverage=int(later.late_years.notna().sum());late_summary=[]
for group,g in later.dropna().groupby('group'):late_summary.append(dict(group=int(group),matched_segments=len(g),deaths=int(g.late_deaths.sum()),exposure=float(g.late_exposure.sum()),death_rate=float(1e8*g.late_deaths.sum()/g.late_exposure.sum())))
# Candidate comparisons share UF and profile but differ in the cadastral arrangement.
pairs=[]
for (uf,gr),g in C.groupby(['uf','group']):
 a=g[g.admin=='Administração federal no cadastro PNCT'];b=g[g.admin=='Concessão no cadastro PNCT']
 if a.empty or b.empty:continue
 for ia in a.index:
  ds=np.sqrt(((Z[b.index]-Z[ia])**2).sum(1));ib=b.index[int(np.argmin(ds))];pairs.append(dict(uf=uf,group=int(gr),direct_index=int(ia),concession_index=int(ib),distance=float(ds.min()),direct_br=int(C.loc[ia,'br']),direct_kmi=float(C.loc[ia,'vl_km_i_estim']),concession_br=int(C.loc[ib,'br']),concession_kmi=float(C.loc[ib,'vl_km_i_estim']),status='Candidato documental; sem interpretação causal ou confirmação de equivalência institucional'))
pairs=sorted(pairs,key=lambda p:p['distance'])[:30];pd.DataFrame(pairs).to_csv(EXP/'ml-casos-candidatos.csv',index=False,encoding='utf-8-sig');C.to_csv(EXP/'ml-agrupamentos-trechos.csv',index=False,encoding='utf-8-sig')
clusters=dict(n=len(C),features=features,transform='RobustScaler seguido de corte em [-5,5]; taxas observadas transformadas por log1p; ajustado apenas em 2022–2023',selection='k 2–6; melhor silhouette entre soluções com grupo mínimo 5% e ARI médio >=0,70; caso nenhuma, melhor silhouette com ressalva',trials=trials,selected=choice,profiles=summ,future_matching_segments=coverage,future_profiles=late_summary,case_candidates=pairs,scatter=[[round(float(x),4),round(float(y),4),int(g)] for (x,y),g in zip(coords,C.group)],scope='Perfis descritivos, condicionados aos mesmos limites físicos em 2022 e 2023. Incluem desfechos do período inicial: diferenças iniciais de gravidade são parte da construção, não validação independente. Não são classes de qualidade de governança.')
obj=dict(seed=SEED,library=sklearn.__version__,scope='Modelos exploratórios; previsão de registros e seleção de casos. Nenhum resíduo é interpretado como sinistro oculto ou falha institucional.',split='Treino 2022–2023; escolha de dois candidatos com 2022→2023; teste 2024–2025. Espacial: 20% dos corredores UF–BR definidos por hash, ausentes também da seleção e do treino; teste espacial-temporal nos anos posteriores.',classifier=clf,classifier_spatial=clf_sp,regression=reg,regression_spatial=reg_sp,clusters=clusters)
save('aprendizado',obj);pd.DataFrame(clf['importance']).to_csv(EXP/'ml-importancia-classificacao.csv',index=False,encoding='utf-8-sig');pd.DataFrame(reg['importance']).to_csv(EXP/'ml-importancia-regressao.csv',index=False,encoding='utf-8-sig');assert clf['calibrated']['n']==len(test);assert reg['model']['n']==len(te);assert sum(p['segments'] for p in summ)==len(C);print('ML CONCLUÍDO',choice,flush=True)
