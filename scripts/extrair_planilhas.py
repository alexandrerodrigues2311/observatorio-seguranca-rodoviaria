"""Extração somente leitura de valores OOXML, sem alterar as fontes."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,csv
R=Path(__file__).resolve().parents[1]
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
for year in range(2022,2026):
 p=R/'data'/f'pnct-vmda-{year}.xlsx';z=zipfile.ZipFile(p)
 shared=[]
 if 'xl/sharedStrings.xml' in z.namelist():
  root=ET.fromstring(z.read('xl/sharedStrings.xml'));shared=[''.join(e.itertext()) for e in root.findall('s:si',ns)]
 for name in [n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]:
  root=ET.fromstring(z.read(name));rows=[]
  for row in root.findall('s:sheetData/s:row',ns):
   values=[]
   for c in row.findall('s:c',ns):
    ref=c.attrib.get('r','A1');letters=''.join(x for x in ref if x.isalpha());col=0
    for letter in letters:col=col*26+ord(letter)-64
    while len(values)<col:values.append('')
    v=c.find('s:v',ns);value=v.text if v is not None else ''
    if c.attrib.get('t')=='s':value=shared[int(value)] if value else ''
    elif c.attrib.get('t')=='inlineStr':value=''.join(c.find('s:is',ns).itertext())
    values[col-1]=value
   rows.append(values)
  out=R/'data'/f'pnct-{year}-{Path(name).stem}.csv'
  with out.open('w',encoding='utf8',newline='') as f:csv.writer(f).writerows(rows)
  print(year,name,'linhas',len(rows),'amostra',rows[:6])
