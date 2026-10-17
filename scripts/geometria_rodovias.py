"""Geometrias oficiais simplificadas apenas para visualização."""
from pathlib import Path
import sys,json,zipfile,math
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'/'vendor'));import shapefile
O=R/'dist'/'data';D=pd.read_pickle(R/'data'/'prf-limpa.pkl')
z=zipfile.ZipFile(R/'data'/'snv202604A.zip');base=next(n for n in z.namelist() if n.endswith('.shp'))
r=shapefile.Reader(shp=z.open(base),shx=z.open(base[:-4]+'.shx'),dbf=z.open(base[:-4]+'.dbf'),encoding='utf8')
roads=[];metas=[]
for sr in r.iterShapeRecords():
 a=sr.record.as_dict()
 if a['sg_tipo_tr']!='B' or a['ds_jurisdi']!='Federal' or a['ds_sup_fed'] not in ['PAV','DUP','IMP']:continue
 pts=sr.shape.points;parts=list(sr.shape.parts)+[len(pts)];lines=[]
 for k in range(len(parts)-1):
  part=pts[parts[k]:parts[k+1]];step=max(1,math.ceil(len(part)/140));sample=part[::step]
  if sample and sample[-1]!=part[-1]:sample.append(part[-1])
  if len(sample)>1:lines.append([[round(p[0],5),round(p[1],5)] for p in sample])
 roads.append(dict(id=int(a['id_trecho_']),uf=a['sg_uf'],br=int(a['vl_br']),code=a['vl_codigo'],km=[a['vl_km_inic'],a['vl_km_fina']],admin=a['ds_tipo_ad'],lines=lines))
 metas.append(a)
S=pd.DataFrame(metas);S['br']=pd.to_numeric(S.vl_br);D['snv_map']=-1
for (uf,br),g in D[D.loc_ok].groupby(['uf','br']):
 seg=S[(S.sg_uf==uf)&(S.br==br)].sort_values('vl_km_inic')
 if seg.empty:continue
 km=g.km.to_numpy();lo=seg.vl_km_inic.to_numpy();hi=seg.vl_km_fina.to_numpy();ma=(km[:,None]>=lo)&(km[:,None]<hi)
 end=km==hi.max()
 if end.any():ma[end,:]=(hi==hi.max())[None,:]
 unique=ma.sum(axis=1)==1;D.loc[g.index[unique],'snv_map']=seg.id_trecho_.to_numpy()[ma[unique].argmax(axis=1)]
data=json.loads((O/'registros.json').read_text(encoding='utf8'))
if len(data['columns'])==15:
 data['columns'].append('snv_202604A_visualizacao')
 for a,sid in zip(data['rows'],D.snv_map):a.append(int(sid))
else:
 for a,sid in zip(data['rows'],D.snv_map):a[15]=int(sid)
for name,obj in [('rodovias',roads),('registros',data)]:
 text=json.dumps(obj,ensure_ascii=False,separators=(',',':'));(O/(name+'.json')).write_text(text,encoding='utf8');(O/(name+'.js')).write_text('window.'+name.upper()+'='+text+';',encoding='utf8')
print('GEOMETRIA',len(roads),'trechos',sum(len(l)for r in roads for l in r['lines']),'pontos; ocorrências associadas',int((D.snv_map>=0).sum()),flush=True)
