"""Contagens cadastrais, sem inferência de operação histórica."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
# Operacionalização e medições cadastrais: reprodução somente leitura.
print(pd.read_csv(ROOT/'dist/exports/operacionalizacao-governanca.csv').to_string(index=False))
# Extração descritiva dos campos existentes; sem inferir início de operação.
import csv, io
pieces=[]
for file in ['antt-sat-3.csv','antt-radar-2.csv','antt-cftv-1.csv']:
    path=ROOT/'data'/file
    try:
        text=path.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        text=path.read_text(encoding='cp1252')
    records=list(csv.reader(io.StringIO(text),delimiter=';'))
    headers=[h.strip().lstrip('\ufeff') for h in records[0]]
    valid=[r for r in records[1:] if len(r)==len(headers)]
    frame=pd.DataFrame(valid,columns=headers)
    counts=frame.groupby(['concessionaria','uf','situacao'],dropna=False).size().reset_index(name='registros')
    counts['arquivo']=file;pieces.append(counts)
    print(file, 'registros:',len(frame),'inativação preenchida:',frame.data_da_inativacao.str.strip().ne('').sum())
observed=pd.concat(pieces,ignore_index=True)
print(observed.to_string(index=False))
preserved=pd.read_csv(ROOT/'dist/exports/equipamentos-governanca-cadastro.csv')
assert observed.registros.sum()==preserved.registros.sum()
print('INTERPRETAÇÃO: capacidade instrumental cadastrada, sem validação histórica de funcionamento e sem comparação de densidade até harmonizar a extensão.')
