"""Aquisição verificável das fontes oficiais. Executar da raiz deste projeto."""
from pathlib import Path
import concurrent.futures as cf
import hashlib, json, datetime, time
import requests

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'; RAW.mkdir(exist_ok=True)
OUT=ROOT/'dist'/'data'; OUT.mkdir(parents=True,exist_ok=True)
manifest=[]
def download(name,url):
    p=RAW/name
    try:
        if not p.exists():
            r=requests.get(url,timeout=(20,120));r.raise_for_status()
            p.write_bytes(r.content)
        b=p.read_bytes()
        item=dict(file=name,url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='baixado')
        manifest.append(item);print(name,len(b),flush=True)
        return p
    except Exception as e:
        manifest.append(dict(file=name,url=url,status='falha',error=str(e)));print(name,'FALHA',str(e)[:130],flush=True)

ids={2022:'1PRQjuV5gOn_nn6UNvaJyVURDIfbSAK4-',2023:'1-WO3SfNrwwZ5_l7fRTiwBKRw7mi1-HUq',2024:'14lB0vqMFkaZj8HZ44b0njYgxs9nAN8KO',2025:'1-G3MdmHBt6CprDwcW99xxC4BZ2DU5ryR'}
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(lambda kv: download(f'prf{kv[0]}.zip','https://drive.google.com/uc?export=download&id='+kv[1]),ids.items()))

api='https://dados.antt.gov.br/api/3/action/'
try:
    p=download('antt-catalogo.json',api+'package_search?fq=groups:rodovias&rows=1000')
    catalog=json.loads(p.read_text(encoding='utf-8'))['result']['results']
    if not catalog:
        p=download('antt-catalogo-todos.json',api+'package_search?rows=1000')
        catalog=json.loads(p.read_text(encoding='utf-8'))['result']['results']
    selected=[]
    for ds in catalog:
        title=ds.get('title','');name=ds['name']
        if name in ['trecho-concedido','sat','radar','cftv','volume-trafego-praca-pedagio','encerramento-investimentos','cadastros-investimentos','acompanhamento-anual']:
            resources=[r for r in ds['resources'] if r.get('format','').upper()=='CSV']
            for i,r in enumerate(resources):
                if name=='volume-trafego-praca-pedagio' and not any(x in r['url'] for x in ['2022.csv','2023.csv','2024_mensal','2025_mensal']):continue
                if name in ['trecho-concedido','sat','radar','cftv'] and i!=len(resources)-1:continue
                selected.append((f"antt-{name}-{i}.csv",r['url']))
    (RAW/'antt-selecao.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
    print('ANTT recursos',len(selected),flush=True)
    with cf.ThreadPoolExecutor(max_workers=5) as ex:list(ex.map(lambda x: download(*x),selected))
except Exception as e: print('CATALOGO',e,flush=True)

download('brasil-ufs.geojson','https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF')
download('snv202604A.zip','https://servicos.dnit.gov.br/dnitcloud/index.php/s/oTpPRmYs5AAdiNr/download?path=%2FSNV%20Bases%20Geom%C3%A9tricas%20%282013-Atual%29%20%28SHP%29&files=202604A.zip')
manifest.sort(key=lambda d:d['file'])
(RAW/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'fontes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
