# Base de Conhecimento ENSO para Predicao do ClimateWise

Data de consolidacao: 5 de maio de 2026

## 1. Objetivo

Consolidar o conhecimento tecnico sobre El Nino e La Nina (ENSO) a partir da pagina NOAA NCEI ENSO e seus links oficiais internos, transformando o conteudo em regras e variaveis operacionais para melhorar a assertividade preditiva do motor ClimateWise.

Escopo da consolidacao:
- Introducao ENSO (NCEI)
- Technical Discussion (NCEI)
- Definitions (NCEI)
- SOI (NCEI)
- SST / RONI e regioes Nino (NCEI)
- OLR (NCEI)
- Resources (NCEI)
- Referencias operacionais CPC relacionadas (indices, RONI, ONI)

## 2. Fontes de dados e referencia

Fontes NOAA/NCEI:
- https://www.ncei.noaa.gov/access/monitoring/enso/
- https://www.ncei.noaa.gov/access/monitoring/enso/technical-discussion
- https://www.ncei.noaa.gov/access/monitoring/enso/definitions
- https://www.ncei.noaa.gov/access/monitoring/enso/soi
- https://www.ncei.noaa.gov/access/monitoring/enso/sst
- https://www.ncei.noaa.gov/access/monitoring/enso/olr
- https://www.ncei.noaa.gov/access/monitoring/enso/resources

Fontes CPC/NOAA citadas pela NCEI:
- https://www.cpc.ncep.noaa.gov/data/indices/
- https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/
- https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php

Base SST:
- ERSST (NCEI): https://www.ncei.noaa.gov/products/extended-reconstructed-sst

## 3. Conceitos cientificos consolidados

### 3.1 O que e ENSO

ENSO e uma oscilacao acoplada oceano-atmosfera no Pacifico equatorial, com periodicidade tipica de 2 a 7 anos, que combina:
- Componente oceanica: anomalias de temperatura da superficie do mar (SST)
- Componente atmosferica: variacao de pressao ao nivel do mar entre Tahiti e Darwin (Oscilacao Sul)

Esse acoplamento altera ventos alisios, termoclina, conveccao tropical e teleconexoes, gerando impactos em chuva e temperatura em varias regioes do planeta.

### 3.2 Mecanismo fisico operacional

Sinais fisicos principais:
- Enfraquecimento dos alisios favorece aquecimento no Pacifico central/leste
- Menor ressurgencia de aguas frias no leste durante El Nino
- Ajuste da termoclina e do gradiente de pressao no Pacifico tropical
- Mudanca no padrao de conveccao (medida indiretamente por OLR)
- Variacoes de nivel do mar como indicador complementar

## 4. Indices principais para modelagem

### 4.1 ONI (Oceanic Nino Index)

Definicao operacional tradicional:
- Media movel trimestral de anomalias SST na regiao Nino 3.4
- Evento quente/frio quando >= +0,5 C ou <= -0,5 C por pelo menos 5 trimestres moveis sobrepostos consecutivos

Uso no ClimateWise:
- Label de regime ENSO historico
- Variavel de estado para modelos de risco climatico

### 4.2 RONI (Relative ONI)

Definicao consolidada NOAA/CPC:
- Parte de SST Nino 3.4 (media trimestral)
- Subtrai anomalia media tropical (20N-20S)
- Ajusta variancia para manter comparabilidade com Nino 3.4 original
- Limiares de classificacao: +0,5 C e -0,5 C por 5 trimestres sobrepostos

Vantagem para predicao:
- Reduz contaminacao de aquecimento tropical de fundo
- Melhora separacao de sinal ENSO versus tendencia termica de larga escala

Observacao operacional importante:
- Valores mais recentes podem ser revisados por ate 2 meses devido ao filtro aplicado na serie ERSST.

### 4.3 SOI (Southern Oscillation Index)

Definicao NCEI:
- Diferenca padronizada de pressao ao nivel do mar entre Tahiti e Darwin

Forma consolidada:
- SOI = sSLP(Tahiti) - sSLP(Darwin), padronizado no periodo base
- NCEI informa anomalias em relacao ao periodo 1981-2010 para metodologia apresentada

Interpretacao:
- SOI negativo persistente: tipico de El Nino
- SOI positivo persistente: tipico de La Nina

Uso no ClimateWise:
- Confirmacao atmosferica do estado ENSO
- Recurso para detectar desacoplamento oceano-atmosfera

### 4.4 OLR (Outgoing Longwave Radiation)

Definicao NCEI:
- Indice de anomalia padronizada OLR na faixa equatorial (aprox. 160E-160W)
- Proxy de conveccao tropical

Interpretacao:
- OLR negativo: mais conveccao/nuvens, consistente com El Nino
- OLR positivo: menos conveccao, consistente com La Nina

Uso no ClimateWise:
- Recurso de intensidade convectiva
- Validacao do impacto atmosferico de anomalias de SST

### 4.5 Regioes Nino

Regioes monitoradas:
- Nino 1+2
- Nino 3
- Nino 3.4
- Nino 4

Ponto tecnico relevante:
- A propria NOAA/NCEI observa que Nino 3.4 pode nao ser ideal para todos os episodios de La Nina; Nino 4 pode melhorar interpretacao de deslocamento convectivo por limiar fisico de cerca de 28 C.

## 5. Regras de classificacao recomendadas para o ClimateWise

Regra base (estado ENSO):
- El Nino: indice principal (RONI preferencial, ONI alternativo) >= +0,5 C por 5 trimestres moveis sobrepostos
- La Nina: indice principal <= -0,5 C por 5 trimestres moveis sobrepostos
- Neutro: demais casos

Regra de confianca do regime (multissinal):
- Alta confianca: sinal oceanico (RONI/ONI) e sinal atmosferico (SOI/OLR) coerentes por >= 2 janelas mensais
- Media confianca: apenas sinal oceanico coerente
- Baixa confianca: sinais divergentes ou fase de transicao

Regra de transicao:
- Transicao quente: slope de RONI positivo e cruzamento de 0 rumo a +0,5 C
- Transicao fria: slope de RONI negativo e cruzamento de 0 rumo a -0,5 C

Regra de severidade (sugestao parametrica inicial):
- Fraco: 0,5 a 0,9 C (modulo)
- Moderado: 1,0 a 1,4 C
- Forte: >= 1,5 C

## 6. Feature engineering para predicao mais assertiva

### 6.1 Features nucleares

- roni_t: RONI atual
- roni_t1_t3: lags 1, 2, 3 meses
- roni_slope_3m: tendencia linear 3 meses
- roni_slope_6m: tendencia linear 6 meses
- oni_t: ONI atual (quando disponivel)
- soi_t: SOI atual
- soi_ma3: media movel de 3 meses do SOI
- olr_t: OLR atual
- olr_ma3: media movel de 3 meses do OLR
- nino12_t, nino3_t, nino34_t, nino4_t: anomalias SST por regiao
- tropical_mean_sst_anomaly_t: media tropical 20N-20S

### 6.2 Features de acoplamento oceano-atmosfera

- coupling_score_1 = z(roni_t) - z(soi_t)
- coupling_score_2 = -z(olr_t) + z(roni_t)
- phase_consistency_flag = 1 se sinais oceanico e atmosferico concordam

### 6.3 Features de regime e histerese

- consecutive_warm_windows
- consecutive_cold_windows
- time_since_regime_change
- regime_transition_flag

### 6.4 Features sazonais

- mes
- trimestre_climatico
- sazonalidade_convectiva (peso mensal para limiar efetivo de impacto)

Nota cientifica:
- A resposta atmosferica ao mesmo valor de anomalia SST e sazonalmente dependente. Um limiar fixo de 0,5 C nao implica o mesmo impacto em todos os meses.

## 7. Pipeline de dados recomendado

Passo 1 - Ingestao mensal:
- Capturar RONI, ONI, SOI, OLR e SST Nino regionais
- Capturar data de publicacao e versao

Passo 2 - Controle de qualidade:
- Marcar ultimos 2 meses de RONI como provisoria/revisavel
- Verificar valores faltantes e interpolacao controlada

Passo 3 - Harmonizacao temporal:
- Consolidar tudo em frequencia mensal
- Preservar janelas trimestrais sobrepostas para ONI/RONI

Passo 4 - Geracao de features:
- Lags, medias moveis, slopes, score de acoplamento

Passo 5 - Scoring ClimateWise:
- Separar score de probabilidade de regime ENSO
- Separar score de impacto regional (chuva/temperatura extremos)

## 8. Proposta de formula para uso no ClimateWise

Score ENSO bruto:

Score_ENSO = w1*z(RONI) - w2*z(SOI) - w3*z(OLR) + w4*z(slope_RONI_3m)

Probabilidade de fase (logistica):

P(ElNino) = sigma(Score_ENSO - theta_warm)
P(LaNina) = sigma(-Score_ENSO - theta_cold)
P(Neutral) = 1 - max(P(ElNino), P(LaNina))

Onde sigma(x) = 1 / (1 + exp(-x)).

Recomendacao:
- Calibrar pesos por backtest historico com janelas walk-forward e validação temporal.

## 9. Regras de governanca e risco de erro

Cuidados essenciais:
- Nao tratar ponto mensal isolado como mudanca de fase oficial
- Exigir persistencia (5 janelas sobrepostas) para rotulo oficial
- Aplicar faixa de incerteza nos meses mais recentes (especialmente RONI)
- Distinguir deteccao de fase ENSO de previsao de impacto local

Risco conhecido:
- Sinal ENSO sozinho nao explica toda variabilidade regional; combinar com MJO, circulacao subtropical, bloqueios atmosfericos e forcantes locais.

## 10. Integracao recomendada ao ClimateAI

Campos minimos para tabela climate_enso_signals:
- reference_date
- roni
- oni
- soi
- olr
- nino12
- nino3
- nino34
- nino4
- regime_label
- regime_confidence
- provisional_flag
- source_url
- ingestion_timestamp

Campos derivados para calculo ClimateWise:
- enso_score
- p_el_nino
- p_la_nina
- p_neutral
- coupling_score
- transition_score
- impact_risk_modifier

## 11. Checklist de implementacao pratica

1. Criar coletor mensal para indices ENSO (NCEI/CPC).
2. Persistir serie historica completa (1950+ para RONI quando disponivel).
3. Implementar classificacao oficial por persistencia de 5 janelas.
4. Implementar classificacao de transicao de curto prazo.
5. Treinar calibracao de pesos por regiao de risco do produto ClimateWise.
6. Publicar score final com confianca e flag de revisao.

## 12. Resumo executivo para decisao

Para aumentar a assertividade preditiva do ClimateWise:
- Use RONI como variavel oceanica principal e ONI como referencia de mercado.
- Exija confirmacao atmosferica por SOI e OLR para elevar confianca.
- Modele transicao e persistencia, nao apenas estado instantaneo.
- Trate os meses recentes como estimativas revisaveis.
- Separe previsao de fase ENSO da traducao para risco local.

Com essa base, o ClimateWise passa a operar com uma arquitetura ENSO multissinal, fisicamente coerente, auditavel e preparada para backtesting historico robusto.
