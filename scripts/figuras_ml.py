"""Figuras científicas de avaliação, geradas dos resultados publicados."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];m=json.loads((R/'dist/data/aprendizado.json').read_text(encoding='utf-8'));O=R/'dist/exports';plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig,ax=plt.subplots(1,2,figsize=(10,3.8),layout='constrained');names=['Constante','Multinomial','Boosting'];vals=[m['classifier']['reference']['log_loss'],m['classifier']['multinomial_reference']['log_loss'],m['classifier']['calibrated']['log_loss']];ax[0].bar(names,vals,color=['#c6c0b8','#8a7667','#a33b32']);ax[0].set_ylim(0,1.3);ax[0].set_title('Log loss · menor é melhor');ax[0].set_yticks([])
for i,v in enumerate(vals):ax[0].text(i,v+.025,f'{v:.3f}',ha='center')
rec=np.array(m['classifier']['calibrated']['recall'])*100;ax[1].bar(['Sem vítimas','Leves','Graves','Mortes'],rec,color='#a33b32');ax[1].set_ylim(0,110);ax[1].set_ylabel('Sensibilidade (%)');ax[1].set_title('Escolha da classe de maior probabilidade')
for i,v in enumerate(rec):ax[1].text(i,v+2,f'{v:.1f}%',ha='center')
fig.suptitle('Gravidade registrada · teste 2024–2025');fig.savefig(O/'ml-classificacao.png',dpi=220);fig.savefig(O/'ml-classificacao.svg');plt.close(fig)
s=np.array(m['clusters']['scatter']);fig,ax=plt.subplots(figsize=(8,4.6),layout='constrained')
for g,c in [(1,'#a33b32'),(2,'#ba8c39')]:
 a=s[s[:,2]==g];ax.scatter(a[:,0],a[:,1],s=9,alpha=.35,color=c,label='Grupo '+str(g))
ax.set(xlabel='Componente principal 1',ylabel='Componente principal 2',title='Perfis descritivos de 2022–2023 · projeção PCA');ax.legend(frameon=False);fig.savefig(O/'ml-agrupamentos.png',dpi=220);fig.savefig(O/'ml-agrupamentos.svg');plt.close(fig)
print('Figuras ML geradas dos mesmos resultados; sem nova estimação.')
