"""Diagnóstico espacial com SNV 202604A. Não reconstrói governança histórica."""
from pathlib import Path
import sys,zipfile,json
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'/'vendor'))
import shapefile
RAW=ROOT/'data';OUT=ROOT/'dist'/'data'
def write(name,obj):
 t=json.dumps(obj,ensure_ascii=False,separators=(',',':'),allow_nan=False,default=lambda x:x.item() if hasattr(x,'item') else str(x));(OUT/(name+'.json')).write_text(t,encoding='utf8');(OUT/(name+'.js')).write_text('window.'+name.upper()+'='+t+';',encoding='utf8')
z=zipfile.ZipFile(RAW/'snv202604A.zip');s=next(n for n in z.namelist() if n.endswith('.shp'))
r=shapefile.Reader(shp=z.open(s),shx=z.open(s[:-4]+'.shx'),dbf=z.open(s[:-4]+'.dbf'),encoding='utf8')
S=pd.DataFrame([x.as_dict() for x in r.iterRecords()])
print({c:S[c].value_counts().to_dict() for c in ['sg_tipo_tr','ds_jurisdi','ds_sup_fed','ds_tipo_ad']},flush=True)
S['br']=pd.to_numeric(S.vl_br,errors='coerce');S['uf']=S.sg_uf
S['admin']=np.select([S.ds_tipo_ad.str.contains('Concess',case=False,na=False),S.ds_tipo_ad.fillna('').isin(['','Federal'])&S.ds_jurisdi.eq('Federal')],['Concessão no SNV 2026','Administração federal no SNV 2026'],default='Outros arranjos no SNV 2026')
D=pd.read_pickle(RAW/'prf-limpa.pkl');D['snv_id']=-1;D['snv_match']='Fora do intervalo'
main=S[(S.sg_tipo_tr=='B')&(S.vl_km_fina>S.vl_km_inic)].copy()
for (uf,br),g in D[D.loc_ok].groupby(['uf','br']):
 seg=main[(main.uf==uf)&(main.br==br)].sort_values('vl_km_inic')
 if seg.empty:continue
 km=g.km.to_numpy();lo=seg.vl_km_inic.to_numpy();hi=seg.vl_km_fina.to_numpy()
 matches=(km[:,None]>=lo[None,:])&(km[:,None]<hi[None,:])
 at_end=km==hi.max()
 if at_end.any():matches[at_end,:]=(hi==hi.max())[None,:]
 n=matches.sum(axis=1);unique=n==1
 D.loc[g.index[unique],'snv_id']=seg.id_trecho_.to_numpy()[matches[unique].argmax(axis=1)]
 D.loc[g.index[unique],'snv_match']='Único'
 D.loc[g.index[n>1],'snv_match']='Ambíguo'
 D.loc[g.index[n==0],'snv_match']='Sem correspondência'
D.loc[~D.loc_ok,'snv_match']='Chave inválida'
counts=D[D.snv_id>=0].groupby(['snv_id','ano']).agg(n=('id','size'),mortos=('mortos','sum'),graves=('feridos_graves','sum')).reset_index()
panel=S.merge(pd.DataFrame({'ano':[2022,2023,2024,2025]}),how='cross').merge(counts,left_on=['id_trecho_','ano'],right_on=['snv_id','ano'],how='left').fillna({'n':0,'mortos':0,'graves':0})
panel['eligible']=(panel.sg_tipo_tr=='B')&(panel.ds_jurisdi=='Federal')&(~panel.ds_sup_fed.isin(['PLA','LEN','LEI']))&(panel.vl_extensa>0)
by=[]
for (year,admin),g in panel[panel.eligible].groupby(['ano','admin']):
 by.append(dict(ano=int(year),admin=admin,trechos=len(g),sem_registro=int((g.n==0).sum()),ocorrencias=int(g.n.sum()),mortos=int(g.mortos.sum()),extensao=float(g.vl_extensa.sum())))
match=D.groupby(['ano','snv_match']).size().reset_index(name='n').to_dict('records')
cols=['id_trecho_','vl_codigo','br','uf','vl_km_inic','vl_km_fina','vl_extensa','ds_jurisdi','ds_sup_fed','admin','sg_tipo_tr']
records=[]
for _,g in panel.groupby('id_trecho_',sort=False):
 a=g.iloc[0];records.append([int(a.id_trecho_),a.vl_codigo,int(a.br),a.uf,round(float(a.vl_km_inic),3),round(float(a.vl_km_fina),3),round(float(a.vl_extensa),3),a.ds_jurisdi,a.ds_sup_fed,a.admin,a.sg_tipo_tr,bool(a.eligible)]+[[int(v) for v in g.sort_values('ano')[c]] for c in ['n','mortos','graves']])
write('snv',dict(version='202604A',n=len(S),main=len(main),eligible=int(panel[panel.ano==2022].eligible.sum()),match=match,groups=by,columns=cols+['eligible','n_2022_2025','mortos_2022_2025','graves_2022_2025'],rows=records,caution='Vinculação por UF, BR e intervalo [início,fim), somente eixo principal; empate é excluído. Cadastro de abril de 2026 aplicado retrospectivamente, sem reconstrução histórica. Zero indica ausência de correspondência de registro PRF e não ausência de sinistro. Sem correção por tráfego ou desambiguação de rodovias coincidentes.'))
panel[cols+['ano','n','mortos','graves','eligible']].to_csv(ROOT/'dist'/'exports'/'diagnostico-snv-202604A.csv',index=False,encoding='utf-8-sig')
print('MATCH',match,flush=True)
# Dicionários de dados revelam UF numérica no cadastro ANTT obtido.
antt=pd.read_csv(RAW/'antt-trecho-concedido-5.csv',sep=';',encoding='cp1252')
write('integracao',dict(antt_trechos=len(antt),uf_values=sorted(antt.uf.astype(str).unique().tolist()),uf_padrao=bool(antt.uf.astype(str).str.fullmatch('[A-Z]{2}').all()),decision='Não foi inferido mapa de códigos numéricos de UF da ANTT. O cadastro de concessões não foi usado como classificação histórica; a administração do SNV aparece apenas no diagnóstico retrospectivo.'))
