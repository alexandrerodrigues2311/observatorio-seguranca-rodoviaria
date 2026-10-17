from pathlib import Path
import requests,json,concurrent.futures,datetime,hashlib
R=Path(__file__).resolve().parents[1];raw=R/'data';url='https://servicos.dnit.gov.br/dadospnct-api/api/v1/downloads/file'
manifest=json.loads((raw/'manifesto.json').read_text(encoding='utf8'))
def get(y):
 idxpath=raw/f'pnct-vmda-{y}-index.json'
 if not idxpath.exists():
  response=requests.get('https://servicos.dnit.gov.br/dadospnct-api/api/v1/downloads/diretorios',params={'path':f'Volume Médio Diário Anual (VMDa)/{y}/'},timeout=60);response.raise_for_status();idxpath.write_text(response.text,encoding='utf8')
 idx=json.loads(idxpath.read_text(encoding='utf8'));out=[]
 for f in idx['diretorios']:
  ext=Path(f['nome']).suffix
  if ext not in ['.xlsx','.pdf']:continue
  name=f'pnct-vmda-{y}'+ext;p=raw/name;r=requests.get(url,params={'path':f['filePath']},timeout=(20,90));r.raise_for_status();p.write_bytes(r.content)
  out.append(dict(file=name,url=r.url,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='baixado'))
  print(name,len(r.content),flush=True)
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for rows in ex.map(get,range(2022,2026)):manifest.extend(rows)
manifest=list({m['file']:m for m in manifest}.values())
(raw/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
(R/'dist'/'data'/'fontes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
