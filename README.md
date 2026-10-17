# Observatório de Segurança Rodoviária — laboratório de evidências

Painel e pesquisa reproduzível dos registros PRF 2022–2025, malha SNV 202604A, exposição modelada PNCT 2022–2025, cadastros públicos ANTT e cartografia IBGE. Edição de 17/10/2026.

## Acesso

- [Painel público na Vercel](https://observatorio-seguranca-rodoviaria.vercel.app/)

- [Notebook no Google Colab](https://colab.research.google.com/github/alexandrerodrigues2311/observatorio-seguranca-rodoviaria/blob/main/notebooks/seguranca_rodoviaria.ipynb)
- [Originais públicos preservados](https://github.com/alexandrerodrigues2311/observatorio-seguranca-rodoviaria/releases/tag/dados-2026-10-17)
- Painel: servir `dist` com `python -m http.server 8773 --directory dist` ou abrir `dist/index.html`. As dependências visuais e dados são locais.

Nove áreas: teoria, panorama, território, padrões, exposição, modelos, auditoria, métodos e laboratório. Filtros exploratórios não reestimam modelos nacionais. A exposição tem filtros próprios. Traçados são do SNV de 2026, sem reconstrução institucional histórica.

## Reprodução exata

Abra o notebook e execute em ordem. Ele baixa o pacote preservado, verifica SHA-256, exibe o código integral de cada etapa e executa o pipeline. Dependências em requirements.txt. Para execução local, extraia o ZIP da release na raiz e execute:

```sh
python -m pip install -r requirements.txt
python scripts/analisar.py
python scripts/integrar_snv.py
python scripts/geometria_rodovias.py
python scripts/extrair_planilhas.py
python scripts/analisar_exposicao.py
python scripts/modelo_multinomial.py
python scripts/publicar_resultados.py
```

Para uma nova aquisição, use coletar.py e coletar_pnct.py. Não misture versões sem um novo manifesto. URLs oficiais podem mudar; data de coleta/verificação não é data da publicação pelo órgão. Os metadados identificam versões e script principal. O notebook foi executado integralmente no ambiente local; o link Colab permite executar uma cópia na conta do leitor, sem afirmar criação no Drive pessoal.

## Métodos e limites

Auditoria de IDs, classificação, pessoas, localização e datas; regressão logística condicional à ocorrência registrada com covariância por UF–BR; persistência por Spearman com bootstrap de corredores; NB2 de sinistros e mortes com offset de veículos-km e controles observáveis; sensibilidades e validação temporal. Exposição PNCT é modelada; 2025 usa janela julho/2024–junho/2025. ICs não propagam incerteza do tráfego. Universo de persistência é condicionado à presença de registro em algum ano do período.

As comparações são observacionais. Concessão cadastral não mede qualidade da governança. Zero associado não identifica evento oculto. A associação de mortes muda na sensibilidade sem segmentos não simuláveis. Modelos não demonstram efeito causal, falha de governança ou interrupção de PDCA.

## Governança e extensões

- `dist/exports/catalogo-governanca.csv`: fontes públicas ANTT, cobertura, SHA-256 e limitações.
- `dist/exports/protocolo-governanca.html`: dimensões, indicadores, fontes públicas adicionais, moderação e mediação propostas, pressupostos e desenho de coleta histórica.
- `dist/exports/registro-extensoes.json`: distingue implementado, fonte identificada e pesquisa proposta.
- `dist/data/fontes.json`: manifesto de aquisição.

Arquivos brutos públicos estão na release; o repositório contém derivados e código. Histórico de contratos, disponibilidade operacional e entrevistas ainda não foi reconstruído. Não há mediação estimada nem índice validado de governança. A proposta privada da tese não é publicada; as extensões não são atribuídas à autora.

## Verificação e ativos

Notebook: execução sequencial das quatorze células de código com saídas preservadas. Pipeline: verificações de totais, taxas, cobertura e convergência. Navegador: navegação nas nove áreas, filtros, traçados, CSV/SVG, arquivos e largura móvel. Script `scripts/verificar-navegador.cjs` usa Playwright/Edge quando disponíveis.

ECharts é distribuído com seu aviso de licença; pyshp 3.0.3 tem licença MIT em scripts/vendor. Dados mantêm termos das fontes originais. Imagem da abertura gerada por IA, ilustrativa, sem correspondência com um sinistro real; ferramenta image_gen, 17/10/2026. Direção visual: sinistro não gráfico em rodovia brasileira, veículos no acostamento, cones, socorro e cores asfalto/âmbar/vermelho. Não usar como evidência empírica.

## Atualização de leitura e desfechos

Síntese dos achados na abertura e teoria; filtros da teoria aplicados ao resumo empírico; comentários por gráfico/tabela em dist/data/interpretacoes.json; rótulos permanentes na rosca; eixo redundante retirado da trajetória. Mapas têm nomes de UF, seleção de corredor, zoom e identificação por marcadores.

Modelo multinomial: quatro desfechos de gravidade máxima, referência sem vítimas, covariância por UF–BR, controles e tipos mais frequentes no treino, teste temporal, calibração e sensibilidade sem tipo. A hipótese IIA não foi validada como verdade substantiva. Acurácia quase igual à referência e baixa sensibilidade fatal impedem uso operacional. Coeficientes, métricas e matriz de confusão publicados.

A matriz dist/exports/viabilidade-protocolo.json separa o que é testável agora, parcialmente testável e dependente de nova coleta. As dez melhorias são propostas e estão em dist/exports/dez-melhorias-pesquisa.json. O notebook inclui as extensões e sua interpretação.

## Apresentação e caderno

[Apresentação de 20 minutos](https://observatorio-seguranca-rodoviaria.vercel.app/apresentacao/) com 18 slides, notas, fontes, cronômetro e tela cheia; [PowerPoint editável](https://observatorio-seguranca-rodoviaria.vercel.app/exports/apresentacao-qualificacao-fumec.pptx). Título, autora, orientação e cronograma conferidos no projeto. O cronograma original marca qualificação em nov–dez, enquanto a agenda informada pelo avaliador é 27/out/2026 às 15h; divergência explicitada, sem alteração silenciosa.

O caderno dist/exports/caderno-trabalho-tese.html explicita tese, hipóteses, medidas e viabilidade. O notebook contém 14 células executadas. Publicado como apoio à avaliação, com extensões separadas da proposta original.

O PowerPoint foi produzido com @oai/artifact-tool do runtime de apresentações; requer esse runtime para reconstrução. O arquivo final inclui objetos editáveis, gráfico com dados incorporados, tabelas e notas de fala. A apresentação web usa HTML/CSS/JavaScript locais e conteúdo estruturado em dist/apresentacao/conteudo.json. Ambos usam o logo fornecido pelo usuário.
