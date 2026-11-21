# INVISIVEL
## Plataforma Nacional de Inteligencia Territorial e Participacao Cidada
### Documento de arquitetura, produto e planejamento do MVP

**Versao:** 2.0  
**Tipo:** Progressive Web App (PWA)  
**Abrangencia planejada:** Brasil  
**MVP piloto:** Serra e Vitoria, Espirito Santo  
**Publico:** Cidadaos, comunidades, pesquisadores e gestores publicos  
**Estado:** Especificacao para desenvolvimento

---

# 1. DEFINICAO DO PROJETO

## 1.1. O que e o INVISIVEL?

O INVISIVEL e uma plataforma de inteligencia territorial que conecta dados publicos brasileiros, relatos de cidadaos e evidencias documentais para identificar, acompanhar e priorizar problemas de interesse coletivo.

A proposta central e:

**"Um mapa que revela onde o poder publico deveria agir primeiro."**

O aplicativo permitira que qualquer pessoa navegue pelo territorio brasileiro, identifique problemas em sua regiao, consulte suas evidencias, participe do acompanhamento e simule alternativas de investimento publico.

A plataforma combinara:

1. Dados governamentais.
2. Indicadores sociais e territoriais.
3. Relatos enviados por cidadaos.
4. Identificacao inteligente de problemas repetidos.
5. Evidencias e noticias relacionadas.
6. Monitoramento colaborativo de resolucao.
7. Analise de prioridades.
8. Simulacao de investimentos.

## 1.2. Missao

Tornar problemas coletivos mais visiveis, documentados e compreensiveis, facilitando a participacao cidada e a discussao de prioridades de investimento.

## 1.3. Principio fundamental

O INVISIVEL nao sera uma rede social convencional.

Cada problema sera tratado como um registro publico estruturado, contendo localizacao, descricao, historico, evidencias, fontes e acompanhamento.

O sistema devera diferenciar:

- O que foi informado por um cidadao.
- O que foi confirmado por fontes independentes.
- O que consta em bases governamentais.
- O que foi declarado por algum orgao publico.
- O que permanece sem comprovacao suficiente.

Uma ocorrencia nao se torna verdadeira apenas por receber varios votos.

---

# 2. PROBLEMAS QUE O SISTEMA ABORDARA

## 2.1. Categorias principais

### Infraestrutura urbana

- Buracos em vias.
- Falta de iluminacao publica.
- Calcadas danificadas.
- Problemas de pavimentacao.
- Obras paralisadas.
- Problemas de drenagem.
- Pontes e estruturas danificadas.

### Saneamento

- Falta de abastecimento de agua.
- Esgoto a ceu aberto.
- Vazamentos.
- Problemas de coleta de lixo.
- Descarte irregular.
- Falta de infraestrutura sanitaria.

### Saude

- Dificuldades de acesso a unidades.
- Deficiencias de infraestrutura.
- Falta de equipamentos relatada.
- Problemas de acessibilidade.
- Problemas estruturais em unidades de saude.

### Educacao

- Escolas sem recursos essenciais.
- Problemas estruturais.
- Ausencia de acessibilidade.
- Deficiencias de conectividade.
- Obras escolares interrompidas.

### Mobilidade

- Pontos de onibus sem cobertura.
- Falta de acessibilidade.
- Travessias perigosas.
- Problemas de sinalizacao.
- Ausencia de infraestrutura para pedestres.

### Meio ambiente

- Descarte irregular de residuos.
- Poluicao de cursos de agua.
- Areas degradadas.
- Problemas ambientais urbanos.
- Pontos recorrentes de alagamento.

## 2.2. Categorias do MVP

Para a primeira entrega:

- Infraestrutura urbana.
- Saneamento.
- Mobilidade.
- Educacao e saude, inicialmente como camadas de dados.

As demais categorias serao incorporadas progressivamente.

---

# 3. A EXPERIENCIA DO CIDADAO

## 3.1. Fluxo de navegacao

O usuario abre o INVISIVEL.

A pagina inicial permite:

1. Selecionar um estado.
2. Selecionar um municipio.
3. Selecionar um bairro, quando cadastrado.
4. Visualizar os problemas encontrados.
5. Filtrar por categoria.
6. Visualizar problemas no mapa.
7. Abrir detalhes de um problema.
8. Consultar fontes e atualizacoes.
9. Marcar "Resolvido" ou "Nao resolvido".
10. Enviar um novo relato.
11. Simular investimentos para a regiao.

Tambem sera disponibilizada uma pesquisa por nome do local.

## 3.2. Navegacao territorial

Hierarquia:

```text
BRASIL
  |
  +-- ESTADO
       |
       +-- MUNICIPIO
            |
            +-- BAIRRO
                 |
                 +-- PROBLEMAS
                 |
                 +-- INDICADORES
                 |
                 +-- INVESTIMENTOS
                 |
                 +-- RELATOS
```

A identificacao territorial usara codigos oficiais sempre que disponiveis.

Para bairros sem delimitacao geoespacial confiavel, o sistema usara registros locais identificados como nao validados cartograficamente.

## 3.3. Navegacao publica

Qualquer visitante podera:

- Pesquisar localidades.
- Visualizar indicadores.
- Consultar problemas publicados.
- Ler atualizacoes.
- Abrir referencias.
- Comparar regioes.
- Utilizar o simulador.

Nao sera necessario cadastro para essas funcoes.

## 3.4. Participacao

Para enviar relatos ou votar, o MVP exigira uma conta autenticada.

Autenticacao inicial:

- Email.
- Link de acesso ou senha.

Nao sera exigido CPF.

O usuario podera escolher se seu nome publico sera exibido como pseudonimo ou se o relato aparecera sem identificacao publica.

O sistema mantera controles internos contra abuso, respeitando a politica de privacidade.

---

# 4. O CONCEITO DE PROBLEMA UNIFICADO

## 4.1. Problema

Um problema e uma situacao territorial especifica que pode receber diferentes relatos ao longo do tempo.

Exemplo:

```text
PROBLEMA #1042

Titulo:
Iluminacao publica insuficiente na Rua Exemplo

Local:
Bairro Exemplo - Municipio Exemplo

Categoria:
Infraestrutura urbana

Primeiro relato:
10/11/2026

Relatos associados:
7

Evidencias:
4

Situacao de verificacao:
Corroborado por multiplos relatos

Percepcao comunitaria:
Nao resolvido

Referencia oficial:
Nenhuma localizada

Ultima atualizacao:
18/11/2026
```

Todos esses dados sao ilustrativos.

## 4.2. Problema nao e a mesma coisa que relato

O banco de dados diferenciara:

**Problema:**

Registro central que representa uma situacao.

**Relato:**

Contribuicao enviada por uma pessoa.

Um problema podera possuir varios relatos.

Essa separacao e fundamental para evitar dezenas de registros repetidos sobre a mesma situacao.

## 4.3. Materia do problema

Cada problema tera uma pagina publica propria.

Essa pagina funcionara como um dossie de acompanhamento, nao como uma noticia jornalistica produzida automaticamente.

Conteudo:

- Titulo.
- Resumo.
- Localizacao.
- Categoria.
- Data do primeiro registro.
- Situacao.
- Historico.
- Evidencias.
- Relatos relacionados.
- Noticias relacionadas.
- Documentos publicos.
- Indicadores territoriais.
- Votacao comunitaria.
- Atualizacoes verificadas.

---

# 5. ENVIO DE RELATOS

## 5.1. Formulario

Campos obrigatorios:

- Categoria.
- Estado.
- Municipio.
- Localizacao do problema.
- Descricao.

Campos opcionais:

- Bairro.
- Rua ou ponto de referencia.
- Fotos.
- Data aproximada da ocorrencia.
- Link de documento publico.
- Link de noticia.
- Informacoes adicionais.

A interface podera usar a localizacao aproximada do usuario somente com permissao explicita.

## 5.2. Fluxo de envio

```text
CIDADAO ENVIA RELATO
          |
          v
VALIDACAO DOS CAMPOS
          |
          v
VERIFICACAO DE CONTEUDO
          |
          v
BUSCA POR PROBLEMAS SIMILARES
          |
          v
EXISTE POSSIVEL DUPLICIDADE?
      /          \
    SIM          NAO
     |            |
     v            v
MOSTRAR          CRIAR
PROBLEMAS        CANDIDATO
EXISTENTES       DE NOVO
     |           PROBLEMA
     v            |
USUARIO           v
CONFIRMA       MODERACAO
RELACAO           |
     |            v
     v         PUBLICACAO
ASSOCIAR
RELATO
     |
     v
VALIDAR NOVAS
INFORMACOES
     |
     v
ATUALIZAR
DOSSIER
```

## 5.3. Verificacao antes da publicacao

O sistema executara:

1. Validacao de localizacao.
2. Classificacao de categoria.
3. Busca de relatos semelhantes.
4. Deteccao de possivel spam.
5. Analise de informacoes pessoais expostas.
6. Identificacao de novos fatos relevantes.
7. Encaminhamento para moderacao.

O motor automatico nao publicara acusacoes ou afirmacoes nao comprovadas como fatos verificados.

---

# 6. MOTOR DE DETECCAO DE DUPLICIDADES

## 6.1. Objetivo

Evitar que o aplicativo apresente varios registros independentes para o mesmo problema.

## 6.2. Exemplo

Relato existente:

"A Rua Exemplo esta com varios postes apagados."

Novo relato:

"Faz semanas que a iluminacao da Rua Exemplo nao funciona."

O sistema devera considerar que os textos podem se referir a mesma situacao.

## 6.3. Criterios de comparacao

Comparar:

- Municipio.
- Bairro.
- Distancia geografica.
- Categoria.
- Similaridade textual.
- Periodo da ocorrencia.
- Identificadores de obras ou equipamentos, quando existentes.

## 6.4. Formula inicial de similaridade

Pesos experimentais:

```text
Localizacao geografica: 40%
Similaridade textual:   35%
Categoria:              15%
Contexto temporal:      10%

TOTAL:                 100%
```

Esses pesos deverao ser calibrados com exemplos reais.

## 6.5. Interpretacao inicial

```text
Score >= 0.85
Possivel duplicidade muito forte.

Score entre 0.65 e 0.84
Possivel duplicidade a revisar.

Score abaixo de 0.65
Candidato a problema distinto.
```

Os valores sao parametros iniciais, sujeitos a testes.

Uma pontuacao alta nao autoriza a fusao automatica definitiva.

## 6.6. Apresentacao ao usuario

Antes da conclusao do envio:

```text
+--------------------------------------+
| ENCONTRAMOS UM PROBLEMA PARECIDO     |
+--------------------------------------+
|                                      |
| Iluminacao na Rua Exemplo            |
|                                      |
| 7 relatos associados                 |
| 350 metros da localizacao informada  |
|                                      |
| [ E O MESMO PROBLEMA ]               |
|                                      |
| [ E UM PROBLEMA DIFERENTE ]          |
|                                      |
+--------------------------------------+
```

O usuario deve poder contestar a correspondencia sugerida.

## 6.7. Tecnologias

MVP:

- PostgreSQL.
- Extensao PostGIS.
- Busca textual normalizada.
- pg_trgm.
- Comparacao por distancia.
- Regras deterministicas.

Evolucao:

- Embeddings semanticos.
- pgvector.
- Classificador de duplicidade.
- Revisao assistida por IA.

A primeira versao nao dependera de uma API paga de inteligencia artificial.

---

# 7. ATUALIZACAO COLABORATIVA DOS PROBLEMAS

## 7.1. Conceito

Quando um novo relato corresponder a um problema existente, o sistema verificara se a contribuicao oferece informacoes novas.

Exemplo:

Problema original:

"Uma rua apresenta esgoto a ceu aberto."

Novo relato:

"Alem do esgoto, a situacao causa mau cheiro e dificulta o acesso de pedestres."

Nesse caso, a nova contribuicao pode complementar o problema.

## 7.2. Classificacao das contribuicoes

O sistema identificara:

- Repeticao de informacao existente.
- Complemento descritivo.
- Nova evidencia fotografica.
- Atualizacao temporal.
- Contestacao.
- Possivel resolucao.
- Nova fonte documental.

## 7.3. Regra de atualizacao

Informacoes novas nao serao incorporadas imediatamente como fatos confirmados.

Fluxo:

```text
NOVA CONTRIBUICAO
        |
        v
COMPARACAO COM DOSSIER
        |
        v
EXTRACAO DE INFORMACOES NOVAS
        |
        v
ANALISE DE EVIDENCIAS
        |
        v
APROVACAO OU REJEICAO
        |
        v
NOVA VERSAO DO DOSSIER
```

## 7.4. Versionamento

Cada atualizacao aprovada devera registrar:

- Versao anterior.
- Versao nova.
- Data.
- Origem da contribuicao.
- Campos alterados.
- Responsavel pela moderacao.
- Justificativa.

Nenhuma informacao anterior sera apagada silenciosamente.

## 7.5. Distincao de confiabilidade

As contribuicoes poderao receber rotulos como:

- Relato comunitario.
- Relato corroborado.
- Evidencia documental.
- Informacao oficial.
- Informacao contestada.

O aplicativo nao apresentara uma pontuacao artificial de "verdade".

---

# 8. SISTEMA DE RESOLVIDO E NAO RESOLVIDO

## 8.1. Interacao principal

Cada problema apresentara dois botoes:

```text
+--------------------------------------+
| ESTE PROBLEMA FOI RESOLVIDO?         |
|                                      |
| [ RESOLVIDO ]  [ NAO RESOLVIDO ]     |
|                                      |
| 18 confirmacoes de resolucao         |
| 64 indicacoes de nao resolvido       |
+--------------------------------------+
```

## 8.2. Regras de votacao

- Um voto ativo por usuario e problema.
- O usuario pode modificar o proprio voto.
- Votos repetidos nao aumentam a contagem.
- A interface exibira contagens separadas.
- O sistema registrara o horario da interacao.
- Atividades suspeitas poderao ser limitadas.

## 8.3. Diferenca entre voto e situacao oficial

Votos representam a percepcao da comunidade.

O problema tera dois campos independentes:

**Situacao de acompanhamento:**

- Aguardando verificacao.
- Relatado.
- Corroborado.
- Em atendimento.
- Resolucao declarada.
- Resolucao verificada.
- Contestada.

**Percepcao comunitaria:**

- Predominantemente resolvido.
- Predominantemente nao resolvido.
- Divergente.
- Sem votos suficientes.

Uma prefeitura informar que resolveu o problema nao implica que os moradores concordem.

Da mesma forma, muitos votos nao comprovam que a situacao foi resolvida.

## 8.4. Reabertura

Um problema encerrado podera ser reaberto quando existirem novas evidencias suficientes.

Reaberturas serao registradas no historico.

---

# 9. REFERENCIAS PUBLICAS E NOTICIAS

## 9.1. Objetivo

Associar problemas a informacoes externas relevantes e verificaveis.

Cada referencia devera possuir:

- Titulo.
- URL original.
- Entidade publicadora.
- Data de publicacao.
- Data da consulta.
- Tipo de fonte.
- Relacao com o problema.
- Trecho resumido ou metadados permitidos.

## 9.2. Tipos de fonte

### Fontes oficiais

- Portais de transparencia.
- Dados governamentais.
- Comunicados de prefeituras.
- Diarios oficiais.
- Contratos publicos.
- Obras publicas.
- Relatorios de fiscalizacao.
- Respostas de ouvidorias legitimamente acessiveis.

### Fontes jornalisticas

- Reportagens locais.
- Noticias regionais.
- Publicacoes sobre obras e infraestrutura.
- Atualizacoes sobre problemas urbanos.

### Fontes comunitarias

- Fotografias.
- Relatos.
- Documentos enviados por usuarios.
- Atualizacoes verificadas pela equipe.

## 9.3. Vinculacao de noticias

O motor de busca de referencias utilizara:

- Nome do municipio.
- Nome do bairro.
- Categoria.
- Localizacao.
- Termos relevantes do relato.
- Periodo da ocorrencia.

A correspondencia devera considerar a data e o contexto.

Uma noticia que menciona o mesmo bairro nao sera automaticamente associada ao problema.

## 9.4. Publicacao

O problema podera apresentar:

```text
FONTES RELACIONADAS

1. Documento oficial
   Entidade: Prefeitura
   Data: ...
   [ABRIR FONTE]

2. Noticia local
   Veiculo: ...
   Data: ...
   [LER REPORTAGEM]

3. Evidencia comunitaria
   Tipo: Fotografia
   Data: ...
```

As fontes jornalisticas serao identificadas separadamente das fontes governamentais.

Nao sera obrigatorio encontrar uma noticia para publicar um problema.

## 9.5. MVP

Na primeira versao:

- Cadastro manual de links.
- Validacao basica de URL.
- Associacao de documentos a problemas.
- Exibicao da origem e data.
- Revisao antes de publicar.

A busca automatica de noticias sera implementada posteriormente, utilizando integracoes permitidas e respeitando licencas e direitos autorais.

---

# 10. BASES GOVERNAMENTAIS

## 10.1. Principio de integracao

O INVISIVEL utilizara fontes oficiais como base de inteligencia territorial.

Os datasets nao serao tratados como um inventario de denuncias individuais.

Uma estatistica de saneamento, por exemplo, descreve a cobertura ou situacao informada para determinado territorio.

Ela nao comprova automaticamente que uma rua especifica apresenta vazamento.

## 10.2. IBGE - Territorio e populacao

Fontes:

https://servicodados.ibge.gov.br/api/docs/localidades

https://servicodados.ibge.gov.br/api/docs/agregados

https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/26565-malhas-de-setores-censitarios-divisoes-intramunicipais.html

Usos:

- Estados.
- Municipios.
- Codigos territoriais.
- Populacao.
- Indicadores censitarios.
- Setores censitarios.
- Malhas de bairros disponiveis.
- Limites geograficos.

Granularidade:

- Estado.
- Municipio.
- Setor censitario, conforme o produto.
- Bairro, conforme cobertura disponivel.

## 10.3. INEP - Educacao

Fonte:

https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar

Usos:

- Identificacao de escolas.
- Infraestrutura educacional.
- Matriculas.
- Recursos escolares.
- Indicadores de acessibilidade.

Granularidade principal:

- Escola.
- Municipio.
- Estado.

## 10.4. DATASUS / CNES - Saude

Fontes:

https://dadosabertos.saude.gov.br/

https://apidadosabertos.saude.gov.br/

Usos:

- Estabelecimentos de saude.
- Localizacao de unidades quando disponibilizada.
- Caracteristicas cadastradas.
- Indicadores da rede assistencial.

Granularidade:

- Estabelecimento.
- Municipio.
- Estado.

A existencia de uma unidade nao comprova, isoladamente, disponibilidade efetiva de atendimento.

## 10.5. SINISA - Saneamento

Fonte:

https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa

Usos:

- Abastecimento de agua.
- Esgotamento sanitario.
- Residuos solidos.
- Drenagem e aguas pluviais.
- Indicadores municipais.

Granularidade principal:

- Municipio.
- Prestador de servico, conforme a tabela.

Os dados nao deverao ser distribuidos artificialmente entre bairros.

## 10.6. Obrasgov.br - Obras publicas

Fonte:

https://api-publica.obrasgov.gestao.gov.br/

Usos:

- Projetos de investimento.
- Obras publicas registradas.
- Situacao de obras.
- Dados geograficos disponiveis.
- Informacoes de acompanhamento.

Granularidade:

- Empreendimento.
- Municipio.
- Localizacao, quando disponivel.

Nem todas as obras municipais estao necessariamente presentes no sistema federal.

## 10.7. Portal da Transparencia

Fonte:

https://api.portaldatransparencia.gov.br/swagger-ui/index.html

Usos:

- Contratos federais.
- Convenios.
- Transferencias.
- Despesas publicas.
- Informacoes sobre investimentos.

Os endpoints utilizados deverao ser confirmados na documentacao atual.

Credenciais e limites de acesso serao tratados exclusivamente no backend.

## 10.8. Fala.BR / CGU

Fontes:

https://www.gov.br/cgu/pt-br/acesso-a-informacao/dados-abertos/arquivos/ouvidoria

https://falabr.cgu.gov.br/help

Usos:

- Estatisticas publicas de ouvidoria.
- Analise de assuntos registrados.
- Estudos sobre demanda por servicos publicos.
- Referencia para encaminhamento a canais oficiais.

Restricao:

A API operacional do Fala.BR possui controles de acesso e permissoes.

O INVISIVEL nao pressupora acesso irrestrito aos textos completos das manifestacoes.

O envio de relatos ao INVISIVEL nao sera apresentado como registro automatico de uma manifestacao oficial.

## 10.9. Portal Brasileiro de Dados Abertos

Fonte:

https://dados.gov.br/

Documentacao:

https://dados.gov.br/swagger-ui/index.html

Usos:

- Descoberta de datasets.
- Identificacao de fontes complementares.
- Consulta de metadados.
- Descoberta de novos recursos publicos.

O catalogo nao substitui as fontes originais.

---

# 11. GRANULARIDADE TERRITORIAL

## 11.1. Problema central

Nem todo dado governamental existe na escala de bairro.

Por exemplo:

Um municipio pode informar cobertura de esgotamento sanitario de determinada porcentagem.

Isso nao permite concluir automaticamente que todos os bairros apresentam a mesma cobertura.

## 11.2. Modelo territorial

O sistema adotara:

```text
UF
 |
 +-- Municipio
      |
      +-- Bairro
      |
      +-- Distrito
      |
      +-- Setor censitario
      |
      +-- Ponto georreferenciado
```

Bairro, distrito e setor censitario serao entidades territoriais relacionadas ao municipio, nao necessariamente uma hierarquia obrigatoria entre si.

## 11.3. Regras

- Indicadores estaduais serao exibidos na escala estadual.
- Indicadores municipais serao exibidos na escala municipal.
- Dados escolares serao associados as unidades correspondentes.
- Relatos pontuais serao georreferenciados.
- Bairros serao identificados por geometria validada quando possivel.
- Dados ausentes nao serao estimados sem metodologia explicita.

## 11.4. Tratamento de bairros

O sistema devera importar inicialmente os bairros presentes nas malhas do IBGE 2022.

Quando houver lacunas:

1. Buscar dados oficiais da prefeitura.
2. Validar nomes e geometrias.
3. Registrar a origem.
4. Permitir localizacao por ponto mesmo sem poligono disponivel.
5. Mostrar "limite territorial nao disponivel" quando necessario.

O MVP nao precisa possuir todos os bairros do Brasil para permitir navegacao nacional por estado e municipio.

---

# 12. ARQUITETURA GERAL

## 12.1. Componentes

O INVISIVEL utilizara cinco camadas:

1. Frontend PWA.
2. API backend.
3. Banco de dados geoespacial.
4. Pipeline de dados governamentais.
5. Motor de inteligencia e moderacao.

## 12.2. Diagrama

```text
+------------------------------------------------+
|                FONTES EXTERNAS                 |
|                                                |
| IBGE  INEP  DATASUS  SINISA  OBRASGOV  CGU     |
|                                                |
| Portais publicos e fontes jornalisticas        |
+----------------------+-------------------------+
                       |
                       v
+------------------------------------------------+
|              CAMADA DE INGESTAO                |
|                                                |
| Python                                         |
| Conectores de APIs                             |
| Download de datasets                           |
| Validacao                                      |
| Normalizacao                                   |
| Georreferenciamento                            |
| Historico de atualizacoes                      |
+----------------------+-------------------------+
                       |
                       v
+------------------------------------------------+
|                BANCO DE DADOS                  |
|                                                |
| PostgreSQL                                     |
| PostGIS                                        |
| Dados territoriais                             |
| Indicadores                                    |
| Problemas                                      |
| Relatos                                        |
| Evidencias                                     |
| Votos                                          |
| Historico                                      |
+----------------------+-------------------------+
                       |
                       v
+------------------------------------------------+
|                  BACKEND API                   |
|                                                |
| FastAPI                                        |
| Autenticacao                                   |
| Consulta territorial                           |
| Busca de problemas                             |
| Cadastro de relatos                            |
| Deteccao de duplicidade                        |
| Moderacao                                      |
| Simulacoes                                     |
+----------------------+-------------------------+
                       |
                       v
+------------------------------------------------+
|                  FRONTEND PWA                  |
|                                                |
| React + TypeScript                             |
| Dashboard                                      |
| Mapa                                           |
| Feed territorial                               |
| Pagina de problemas                            |
| Novo relato                                    |
| Simulador                                      |
+------------------------------------------------+
```

## 12.3. Tecnologias

Frontend:

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui.
- Lucide Icons.
- React Router.
- TanStack Query.

Mapas:

- MapLibre GL JS.
- GeoJSON.
- Tiles geograficos.

Graficos:

- Recharts.

Backend:

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.

Banco:

- PostgreSQL.
- PostGIS.
- pg_trgm.
- pgvector em fase posterior.

Autenticacao e armazenamento inicial:

- Supabase Auth.
- Supabase Storage.

Processamento:

- Pandas.
- GeoPandas.
- Scripts de ETL.
- Jobs agendados.

Hospedagem:

- Frontend: Cloudflare Pages ou Vercel.
- API: Servico de hospedagem Python.
- Banco: PostgreSQL gerenciado.

## 12.4. Simplificacao do MVP

A primeira versao podera usar Supabase como banco, autenticacao e armazenamento.

Isso reduz a necessidade de desenvolver infraestrutura propria para usuarios e arquivos.

FastAPI concentrara:

- Analises.
- Busca de duplicidades.
- Regras de moderacao.
- Simulacoes.
- Consultas publicas especializadas.

---

# 13. MODELAGEM DO BANCO DE DADOS

## 13.1. Tabelas principais

```text
states
municipalities
neighborhoods
territorial_areas
data_sources
datasets
indicator_definitions
indicator_observations

users
issues
reports
issue_evidence
issue_sources
issue_updates
issue_votes
issue_status_history

interventions
simulation_scenarios

moderation_queue
audit_logs
ingestion_jobs
```

## 13.2. states

Campos:

```text
id
ibge_code
name
abbreviation
geometry
```

## 13.3. municipalities

Campos:

```text
id
ibge_code
state_id
name
geometry
population
population_reference_year
```

## 13.4. neighborhoods

Campos:

```text
id
municipality_id
official_code
name
geometry
source_id
geometry_status
```

O codigo oficial podera ser nulo quando inexistente.

## 13.5. issues

Representa o problema principal.

```text
id
title
summary
category
municipality_id
neighborhood_id
location
location_precision
verification_status
operational_status
first_reported_at
last_activity_at
created_at
updated_at
```

O campo `location` sera geoespacial.

A localizacao podera representar um ponto ou uma geometria mais ampla, conforme o tipo de problema.

## 13.6. reports

Representa um relato individual.

```text
id
issue_id
author_id
original_text
category
reported_location
occurrence_date
moderation_status
created_at
```

## 13.7. issue_evidence

```text
id
issue_id
report_id
evidence_type
storage_path
visibility
verification_status
created_at
```

## 13.8. issue_sources

```text
id
issue_id
title
url
publisher
source_type
published_at
checked_at
review_status
```

## 13.9. issue_votes

```text
id
issue_id
user_id
vote
created_at
updated_at
```

Valores:

```text
RESOLVED
UNRESOLVED
```

Restricao:

Um voto por usuario e problema.

## 13.10. indicator_observations

```text
id
indicator_id
territorial_area_id
value
unit
reference_year
source_id
quality_status
```

## 13.11. issue_updates

```text
id
issue_id
update_type
previous_version
new_version
source_report_id
approved_by
created_at
```

## 13.12. Relacionamentos essenciais

```text
STATE
  |
  +-- MUNICIPALITY
         |
         +-- NEIGHBORHOOD
         |
         +-- ISSUE
                |
                +-- REPORTS
                |
                +-- EVIDENCE
                |
                +-- SOURCES
                |
                +-- VOTES
                |
                +-- UPDATES
```

Um registro de problema tambem podera existir sem bairro definido.

---

# 14. API DO INVISIVEL

## 14.1. Principio

O frontend consumira uma API propria.

A API nao devera consultar os sistemas federais a cada navegacao.

Os dados oficiais serao sincronizados e armazenados conforme a frequencia de atualizacao de cada fonte.

## 14.2. Endpoints territoriais

```http
GET /api/v1/states

GET /api/v1/states/{id}/municipalities

GET /api/v1/municipalities/{id}/neighborhoods

GET /api/v1/territories/{id}/summary

GET /api/v1/territories/{id}/indicators
```

## 14.3. Endpoints de problemas

```http
GET /api/v1/issues

GET /api/v1/issues/{id}

GET /api/v1/issues/{id}/reports

GET /api/v1/issues/{id}/sources

GET /api/v1/issues/{id}/updates

GET /api/v1/issues/{id}/votes
```

Filtros da listagem:

```text
state
municipality
neighborhood
category
verification_status
operational_status
bbox
page
page_size
```

## 14.4. Endpoints de contribuicoes

```http
POST /api/v1/reports

POST /api/v1/reports/check-duplicates

POST /api/v1/issues/{id}/votes

POST /api/v1/issues/{id}/evidence
```

## 14.5. Endpoints de simulacao

```http
POST /api/v1/simulations

GET /api/v1/simulations/{id}
```

## 14.6. Endpoints administrativos

```http
GET /api/v1/admin/moderation

POST /api/v1/admin/reports/{id}/approve

POST /api/v1/admin/reports/{id}/reject

POST /api/v1/admin/issues/{id}/merge

POST /api/v1/admin/issues/{id}/status
```

Todos os endpoints administrativos exigirao autenticacao e autorizacao por papel.

## 14.7. API publica

Endpoints de leitura poderao ser disponibilizados publicamente com:

- Paginacao.
- Limites de requisicao.
- Cache.
- Documentacao OpenAPI.
- Campos seguros.
- Identificacao de versao.

Informacoes pessoais e dados internos de moderacao nao serao disponibilizados.

---

# 15. MOTOR DE INTELIGENCIA TERRITORIAL

## 15.1. Objetivo

Identificar regioes potencialmente desassistidas utilizando indicadores publicos.

## 15.2. Dados considerados

- Populacao.
- Indicadores de infraestrutura.
- Dados educacionais.
- Dados de saude.
- Dados de saneamento.
- Dados sobre investimentos.
- Densidade de problemas relatados.

## 15.3. Dois sistemas de analise

O INVISIVEL nao devera misturar indiscriminadamente indicadores oficiais com relatos comunitarios.

Serao utilizados dois modelos separados.

### Modelo A - Vulnerabilidade territorial

Baseado em indicadores oficiais.

Objetivo:

Apontar possiveis carencias estruturais.

### Modelo B - Prioridade dos problemas

Baseado nos problemas cadastrados e nas evidencias.

Objetivo:

Ordenar situacoes que merecem atencao ou investigacao.

## 15.4. Modelo A

Os indicadores deverao ser normalizados e comparados somente quando forem metodologicamente compativeis.

Exemplo conceitual:

```text
Indice territorial =
  infraestrutura
+ acesso a servicos
+ vulnerabilidade
```

Os pesos serao configuraveis e documentados.

Dados insuficientes produzirao "sem avaliacao", nao uma pontuacao artificial.

## 15.5. Modelo B

Criterios iniciais de priorizacao:

```text
Gravidade estimada:       25
Populacao potencial:      20
Persistencia:             20
Corroboracao:             15
Vulnerabilidade local:    15
Recencia:                  5

TOTAL:                   100
```

Os criterios utilizarao escalas normalizadas.

Esses pesos sao parametros de teste, nao uma classificacao oficial.

## 15.6. Restricoes

- Votos nao serao considerados prova de veracidade.
- Ausencia de relatos nao significara ausencia de problemas.
- Mais usuarios ativos nao significara necessariamente maior gravidade.
- A populacao afetada nao sera inventada.
- Indicadores de anos distintos serao identificados.
- A qualidade dos dados aparecera ao lado dos resultados.

## 15.7. Ordenacoes disponiveis

O usuario podera visualizar:

- Problemas mais recentes.
- Problemas sem resolucao verificada.
- Maior gravidade estimada.
- Maior quantidade de relatos associados.
- Maior quantidade de evidencias corroboradas.
- Problemas em atendimento declarado.
- Problemas com contestacao de resolucao.

---

# 16. SIMULADOR DE INVESTIMENTOS

## 16.1. Conceito

O cidadao podera escolher uma regiao e comparar cenarios de investimento.

Exemplo:

"Se o municipio tivesse R$ 500.000 para enfrentar determinados problemas, quais alternativas poderiam ser consideradas?"

## 16.2. Entradas

- Municipio.
- Categoria.
- Orcamento hipotetico.
- Tipo de intervencao.
- Custo unitario.
- Estrategia de priorizacao.

## 16.3. Saidas

- Quantidade de intervencoes possiveis.
- Problemas potencialmente contemplados.
- Orcamento utilizado.
- Saldo.
- Indicadores que mudariam no modelo.
- Lista de intervencoes.
- Explicacao dos criterios.

## 16.4. Metodologia do MVP

Utilizar um problema de alocacao sob restricao orcamentaria.

Exemplo simplificado:

```text
MAXIMIZAR
  Soma dos beneficios estimados

SUJEITO A
  Soma dos custos <= Orcamento
```

O beneficio estimado sera calculado a partir das premissas escolhidas e de dados validos.

O sistema nao afirmara conhecer o custo real de reparar cada problema.

## 16.5. Diferenca entre simulacao e realidade

Toda simulacao sera marcada:

"Resultado hipotetico. Nao representa uma previsao oficial nem substitui estudos tecnicos."

O simulador nao podera transformar uma intervencao virtual em um problema realmente resolvido.

---

# 17. INTERFACE E EXPERIENCIA VISUAL

## 17.1. Objetivo de design

O INVISIVEL deve parecer um aplicativo civico moderno, simples e acessivel.

O usuario nao precisara entender estatistica para navegar.

Diretrizes:

- Mobile-first.
- Poucos elementos por tela.
- Mapas intuitivos.
- Cards simples.
- Busca em destaque.
- Informacoes progressivas.
- Cores consistentes.
- Icones claros.
- Acessibilidade.
- Estados vazios explicativos.

## 17.2. Identidade visual

Paleta proposta:

```text
Background:       #F8FAFC
Cards:            #FFFFFF
Texto:            #0F172A
Secundario:       #64748B

Primaria:         #0F766E
Primaria clara:   #CCFBF1

Atencao:          #D97706
Problema:         #DC2626
Informacao:       #2563EB
Bordas:           #E2E8F0
```

Tema padrao: claro.

Tema escuro: opcional.

Tipografia: Inter.

Icones: Lucide.

## 17.3. Menu principal

Desktop:

```text
INVISIVEL

Inicio
Explorar
Problemas
Reportar
Simulador
Sobre
```

Mobile:

```text
Inicio | Mapa | Reportar | Problemas | Perfil
```

A interface de navegacao tera no maximo cinco destinos principais no celular.

---

# 18. TELA INICIAL

## 18.1. Estrutura desktop

```text
+--------------------------------------------------------------+
| INVISIVEL      Explorar  Problemas  Simulador  Entrar         |
+--------------------------------------------------------------+
|                                                              |
|  VEJA O QUE PRECISA MUDAR PERTO DE VOCE                      |
|                                                              |
|  Descubra problemas, acompanhe solucoes e participe.         |
|                                                              |
|  Estado:    [ Espirito Santo     v ]                          |
|  Municipio: [ Selecione          v ]                          |
|  Bairro:    [ Todos              v ]                          |
|                                                              |
|  [ EXPLORAR REGIAO ]            [ REPORTAR PROBLEMA ]         |
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|  PANORAMA DA REGIAO                                         |
|                                                              |
|  [ Problemas ] [ Nao resolvidos ] [ Resolvidos ]             |
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|  +---------------------------+----------------------------+   |
|  |                           |                            |   |
|  |     MAPA INTERATIVO       |  PROBLEMAS EM DESTAQUE     |   |
|  |                           |                            |   |
|  |    Marcadores             |  1. Problema A             |   |
|  |    Agrupamentos           |  2. Problema B             |   |
|  |                           |  3. Problema C             |   |
|  +---------------------------+----------------------------+   |
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|  INDICADORES TERRITORIAIS                                    |
|                                                              |
|  Educacao | Saude | Saneamento | Infraestrutura              |
|                                                              |
+--------------------------------------------------------------+
```

## 18.2. Mobile

```text
+------------------------+
| INVISIVEL          [=] |
+------------------------+
|                        |
| O que precisa mudar    |
| na sua regiao?         |
|                        |
| [ ESTADO           v ] |
| [ MUNICIPIO        v ] |
| [ BAIRRO           v ] |
|                        |
| [ EXPLORAR ]           |
|                        |
| [ + REPORTAR ]         |
|                        |
+------------------------+
|                        |
| Problemas encontrados  |
|                        |
| [ Total ] [ Pendentes ]|
|                        |
+------------------------+
|                        |
|      MAPA              |
|                        |
|   o       o            |
|       o                |
|                        |
+------------------------+
|                        |
| Problemas recentes     |
|                        |
| [ Card ]               |
| [ Card ]               |
|                        |
+------------------------+
| Inicio Mapa + Problemas|
+------------------------+
```

O conteudo sera reorganizado automaticamente conforme o tamanho da tela.

---

# 19. TELA DE EXPLORACAO

## Objetivo

Permitir descobrir problemas por localizacao.

## Recursos

- Busca territorial.
- Mapa com marcadores.
- Agrupamento de marcadores.
- Filtros por categoria.
- Filtros por situacao.
- Alternancia mapa/lista.
- Ordenacao.
- Paginas de detalhes.

## Comportamento

Selecionar um estado:

Atualiza a lista de municipios.

Selecionar um municipio:

Atualiza a lista de bairros.

Selecionar um bairro:

Filtra problemas relacionados a regiao.

Selecionar uma categoria:

Mostra apenas os problemas correspondentes.

## Marcadores

Os marcadores utilizarao icones por categoria.

Exemplos:

- Infraestrutura: construcao.
- Saneamento: agua.
- Mobilidade: estrada.
- Educacao: escola.
- Saude: cruz.
- Meio ambiente: folha.

As cores indicarao estados ou prioridades documentadas, nao apenas categorias.

---

# 20. TELA DO PROBLEMA

## Estrutura

```text
+------------------------------------------------------+
| INVISIVEL / PROBLEMA #1042                           |
+------------------------------------------------------+
|                                                      |
| Iluminacao publica insuficiente                      |
|                                                      |
| Bairro Exemplo - Municipio Exemplo                   |
|                                                      |
| [ INFRAESTRUTURA ]  [ RELATO CORROBORADO ]           |
|                                                      |
+------------------------------------------------------+
|                                                      |
| [ FOTOGRAFIAS ]                                      |
|                                                      |
+------------------------------------------------------+
|                                                      |
| RESUMO                                               |
|                                                      |
| Descricao atual do problema.                         |
|                                                      |
+------------------------------------------------------+
|                                                      |
| LOCALIZACAO                                          |
|                                                      |
| [ MAPA ]                                             |
|                                                      |
+------------------------------------------------------+
|                                                      |
| ESTE PROBLEMA FOI RESOLVIDO?                         |
|                                                      |
| [ RESOLVIDO ] [ NAO RESOLVIDO ]                       |
|                                                      |
+------------------------------------------------------+
|                                                      |
| LINHA DO TEMPO                                       |
|                                                      |
| 10/11 - Primeiro relato                              |
| 14/11 - Nova evidencia                               |
| 18/11 - Atualizacao comunitaria                      |
|                                                      |
+------------------------------------------------------+
|                                                      |
| FONTES E NOTICIAS                                    |
|                                                      |
| [ Documento publico ]                                |
| [ Noticia relacionada ]                              |
|                                                      |
+------------------------------------------------------+
|                                                      |
| [ ADICIONAR INFORMACAO ]                             |
|                                                      |
+------------------------------------------------------+
```

## Requisitos

- Compartilhamento por link.
- URL permanente.
- Historico verificavel.
- Evidencias com legenda.
- Referencias abertas.
- Explicacao do estado de verificacao.
- Votacao simples.
- Atualizacoes associadas ao problema.

---

# 21. TELA DE NOVO RELATO

## Fluxo visual

Etapa 1:

"Onde esta o problema?"

Selecionar localizacao.

Etapa 2:

"O que esta acontecendo?"

Selecionar categoria e descrever.

Etapa 3:

"Tem alguma evidencia?"

Adicionar foto ou referencia.

Etapa 4:

"Encontramos algo parecido."

Mostrar problemas semelhantes.

Etapa 5:

"Revise seu relato."

Mostrar resumo e enviar.

Etapa 6:

"Relato recebido."

Exibir codigo interno e situacao de moderacao.

## Regra principal

O usuario podera associar seu relato a um problema ja existente ou solicitar a criacao de um registro separado.

O aplicativo explicara que a publicacao depende de verificacoes e regras de moderacao.

---

# 22. PAINEL DE MODERACAO

## 22.1. Objetivo

Garantir que informacoes novas possam ser revisadas antes de sua publicacao.

## 22.2. Fila

```text
+------------------------------------------------------+
| ADMIN / MODERACAO                                    |
+------------------------------------------------------+
|                                                      |
| Pendentes: 12                                        |
|                                                      |
| [ NOVOS ] [ COMPLEMENTOS ] [ CONTESTACOES ]          |
|                                                      |
+------------------------------------------------------+
|                                                      |
| Relato #302                                          |
|                                                      |
| Categoria: Infraestrutura                            |
| Municipio: Exemplo                                   |
|                                                      |
| Similaridade com #1042: 89%                          |
|                                                      |
| [ VISUALIZAR ]                                       |
|                                                      |
| [ ASSOCIAR ] [ NOVO PROBLEMA ] [ REJEITAR ]          |
|                                                      |
+------------------------------------------------------+
```

## 22.3. Acoes

- Aprovar relato.
- Rejeitar com motivo.
- Solicitar esclarecimento.
- Vincular a problema existente.
- Criar novo problema.
- Revisar evidencia.
- Aprovar complemento.
- Corrigir categorizacao.
- Contestar informacao.
- Reabrir problema.
- Restaurar versao anterior.

## 22.4. Automacao

O motor automatico auxiliara na triagem.

A publicacao de conteudo sensivel ou ambiguidade relevante exigira revisao humana.

---

# 23. PIPELINE DE DADOS OFICIAIS

## 23.1. Funcionamento

```text
FONTE GOVERNAMENTAL
        |
        v
CONECTOR ESPECIFICO
        |
        v
DOWNLOAD / API
        |
        v
VALIDACAO
        |
        v
NORMALIZACAO
        |
        v
IDENTIFICACAO TERRITORIAL
        |
        v
BANCO DE DADOS
        |
        v
CALCULO DE INDICADORES
        |
        v
API DO INVISIVEL
```

## 23.2. Frequencia

A atualizacao dependera da fonte.

Politica inicial:

- Codigos territoriais: verificar periodicamente.
- Censo: atualizar por publicacao ou revisao.
- Censo Escolar: atualizar por nova edicao.
- CNES: verificar atualizacoes conforme fonte.
- SINISA: atualizar por ciclo publicado.
- Obrasgov: sincronizacao conforme limites da API.
- Relatos cidadaos: processamento continuo.
- Noticias: nova consulta ou revisao conforme necessidade.

Datas de referencia e de sincronizacao serao distintas.

## 23.3. Controle de qualidade

Cada integracao registrara:

- Fonte.
- Versao.
- Data da coleta.
- Ano de referencia.
- Quantidade de registros.
- Quantidade rejeitada.
- Campos ausentes.
- Erros.
- Ultima sincronizacao bem-sucedida.

Uma integracao com falha nao devera apagar dados anteriores validos.

---

# 24. SEGURANCA E PRIVACIDADE

## 24.1. LGPD

O aplicativo coletara somente os dados pessoais necessarios para operacao, seguranca e participacao.

Requisitos:

- Politica de privacidade.
- Base legal adequada para tratamento.
- Controle de acesso.
- Retencao definida.
- Possibilidade de solicitacao de exclusao, quando aplicavel.
- Registro de atividades administrativas.
- Tratamento seguro de arquivos.

## 24.2. Fotografias

Antes da publicacao:

- Validar tipo e tamanho.
- Remover metadados EXIF sensiveis.
- Analisar possivel exposicao de pessoas.
- Evitar publicacao de dados pessoais indevidos.
- Permitir revisao humana.
- Armazenar em bucket privado ate aprovacao.

## 24.3. Denuncias sensiveis

O MVP nao sera um canal oficial de denuncias sigilosas.

Alegacoes envolvendo crimes, pessoas identificaveis ou riscos pessoais exigirao tratamento especifico.

A interface devera encaminhar o usuario a canais oficiais quando necessario.

## 24.4. Protecao contra abuso

- Rate limiting.
- CAPTCHA ou mecanismo equivalente quando necessario.
- Verificacao de conta.
- Limite de envio.
- Deteccao de spam.
- Controle de permissoes.
- Logs de moderacao.
- Protecao contra votos automatizados.

---

# 25. MVP REALISTA PARA APRESENTACAO

## 25.1. Objetivo

Demonstrar o conceito completo em escala reduzida.

A arquitetura sera nacional, mas a primeira base de problemas sera limitada a uma regiao piloto.

## 25.2. Territorio inicial

Proposta:

- Espirito Santo.
- Serra.
- Vitoria.
- Bairros oficiais disponiveis.

Os demais estados e municipios poderao aparecer na navegacao, mesmo quando ainda nao existirem problemas publicados.

Nesse caso, a interface mostrara um estado vazio explicativo.

## 25.3. Funcionalidades obrigatorias

### Navegacao

- Estados.
- Municipios.
- Bairros disponiveis.
- Pesquisa territorial.

### Problemas

- Listagem.
- Mapa.
- Detalhes.
- Categorias.
- Situacoes.
- Fontes.

### Participacao

- Login.
- Criacao de relato.
- Busca por possiveis duplicidades.
- Associacao a problema existente.
- Complementacao de problema.
- Votos resolvido/nao resolvido.

### Moderacao

- Fila de relatos.
- Aprovacao.
- Vinculacao.
- Publicacao.
- Atualizacao de dossie.

### Dados

- Populacao municipal.
- Indicadores de pelo menos tres setores.
- Fontes oficiais.
- Ano e granularidade dos dados.

### Simulacao

- Um tipo de intervencao.
- Orcamento hipotetico.
- Regras documentadas.
- Comparacao entre cenarios.

## 25.4. Funcionalidades adiadas

- Busca nacional automatica de noticias.
- IA generativa para redacao de materias.
- Embeddings em larga escala.
- Aplicativo nativo.
- Integracao com ouvidorias restritas.
- Envio automatico de protocolos oficiais.
- Notificacoes push.
- Ranking nacional completo.
- Previsoes causais complexas.
- Importacao automatica de portais municipais sem API.

---

# 26. FASES DE DESENVOLVIMENTO

## Fase 1 - Fundacao

Entregas:

- Repositorio.
- Projeto React.
- Projeto FastAPI.
- PostgreSQL.
- PostGIS.
- Autenticacao.
- Layout responsivo.
- Documentacao.

Validacao:

Frontend, backend e banco funcionando de forma integrada.

## Fase 2 - Territorio

Entregas:

- Estados.
- Municipios.
- Bairros disponiveis.
- Importacao do IBGE.
- Geometrias.
- Busca territorial.
- Mapa.

Validacao:

Navegacao e filtros funcionando.

## Fase 3 - Problemas

Entregas:

- Cadastro de problemas.
- Cadastro de relatos.
- Pagina de detalhes.
- Categorias.
- Historico.
- Fontes.
- Evidencias.

Validacao:

Problema publicado aparece corretamente no territorio correspondente.

## Fase 4 - Inteligencia colaborativa

Entregas:

- Deteccao de duplicidades.
- Vinculacao de relatos.
- Identificacao de complementos.
- Moderacao.
- Votos.
- Atualizacoes versionadas.

Validacao:

Dois relatos semelhantes podem compor um unico dossie, sem perda da informacao original.

## Fase 5 - Dados governamentais

Entregas:

- Conectores do IBGE.
- Importacao de dados educacionais.
- Importacao de dados de saude.
- Importacao de indicadores de saneamento.
- Proveniencia.
- Dashboard territorial.

Validacao:

Indicadores reais aparecem com fonte, unidade, ano e territorio corretos.

## Fase 6 - Simulador

Entregas:

- Estrategias.
- Custos hipoteticos.
- Orcamento.
- Calculo.
- Comparativo.
- Explicacao.

Validacao:

Resultados consistentes com os parametros informados.

## Fase 7 - Publicacao

Entregas:

- PWA.
- HTTPS.
- Manifest.
- Cache.
- Hospedagem.
- Testes de seguranca.
- Testes responsivos.
- Documentacao final.

Validacao:

Aplicativo acessivel por celular e computador.

---

# 27. TESTES OBRIGATORIOS

## Territorio

- Municipio pertence ao estado correto.
- Bairro pertence ao municipio correto.
- Marcador aparece dentro da localizacao esperada.
- Local sem bairro conhecido continua pesquisavel.

## Duplicidade

- Mesma rua e mesmo problema geram sugestao.
- Problemas diferentes na mesma rua nao sao fundidos automaticamente.
- Diferencas de acentuacao nao impedem comparacao.
- Problemas com nomes parecidos em municipios distintos permanecem separados.

## Relatos

- Relato precisa de categoria e localizacao.
- Conteudo rejeitado nao aparece publicamente.
- Arquivo nao aprovado permanece privado.
- Relato vinculado preserva texto original.

## Votacao

- Usuario nao vota duas vezes.
- Usuario pode alterar voto.
- Votos nao alteram automaticamente a verificacao.
- Votos removidos deixam de contar.

## Indicadores

- Fonte e ano obrigatorios.
- Dado ausente nao vira zero.
- Indicador municipal nao e apresentado como indicador de bairro.
- Indicadores de unidades diferentes nao sao somados diretamente.

## Simulacao

- Orcamento nao e ultrapassado.
- Parametros iguais geram resultados iguais.
- Simulacao nao altera problemas reais.
- Custos hipoteticos aparecem identificados.

## Seguranca

- Usuario comum nao acessa moderacao.
- Upload possui validacao.
- API possui limitacao de requisicoes.
- Credenciais nao aparecem no frontend.
- Registros internos nao sao retornados por endpoints publicos.

---

# 28. ESTRUTURA DE PASTAS

```text
invisivel/
|
+-- apps/
|   |
|   +-- web/
|   |   +-- src/
|   |       +-- app/
|   |       +-- pages/
|   |       +-- components/
|   |       +-- features/
|   |       |   +-- territories/
|   |       |   +-- issues/
|   |       |   +-- reports/
|   |       |   +-- voting/
|   |       |   +-- maps/
|   |       |   +-- indicators/
|   |       |   +-- simulations/
|   |       +-- services/
|   |       +-- hooks/
|   |       +-- styles/
|   |
|   +-- api/
|       +-- app/
|           +-- main.py
|           +-- core/
|           +-- modules/
|           |   +-- territories/
|           |   +-- issues/
|           |   +-- reports/
|           |   +-- moderation/
|           |   +-- analytics/
|           |   +-- simulation/
|           +-- database/
|           +-- tests/
|
+-- pipelines/
|   +-- ibge/
|   +-- inep/
|   +-- datasus/
|   +-- sinisa/
|   +-- obrasgov/
|
+-- database/
|   +-- migrations/
|   +-- seeds/
|
+-- docs/
|   +-- architecture/
|   +-- api/
|   +-- data-sources/
|   +-- methodology/
|
+-- README.md
```

Cada modulo devera ter responsabilidades bem delimitadas.

---

# 29. METRICAS DO PROJETO

## 29.1. Qualidade dos dados

- Percentual de registros com localizacao valida.
- Percentual de indicadores com fonte identificada.
- Registros rejeitados na importacao.
- Tempo desde a ultima atualizacao.

## 29.2. Participacao

- Usuarios participantes.
- Relatos enviados.
- Relatos aprovados.
- Relatos associados a problemas existentes.
- Novos problemas publicados.
- Votos registrados.

## 29.3. Qualidade do motor de duplicidade

- Precisao das sugestoes.
- Duplicidades confirmadas.
- Falsos positivos.
- Falsos negativos em conjunto de teste.

## 29.4. Acompanhamento

- Problemas com novas evidencias.
- Problemas com resolucao declarada.
- Problemas com resolucao verificada.
- Problemas contestados.
- Tempo entre relatos e atualizacoes.

Essas metricas nao comprovam, por si, que o aplicativo causou a resolucao de problemas.

---

# 30. ROTEIRO DE APRESENTACAO

## Demonstracao 1 - Inteligencia territorial

Abrir o INVISIVEL.

Selecionar:

- Espirito Santo.
- Serra.
- Um bairro disponivel.

Mostrar os indicadores reais disponiveis para aquela escala.

Explicar como as fontes sao integradas.

## Demonstracao 2 - Descoberta de problema

Abrir o mapa.

Selecionar um problema publicado.

Mostrar:

- Localizacao.
- Historico.
- Evidencias.
- Referencias.
- Votacao.

## Demonstracao 3 - Novo relato

Utilizar um usuario de teste.

Enviar um relato que descreva o mesmo problema com outras palavras.

O sistema sugere a possivel duplicidade.

Associar o relato ao problema existente.

## Demonstracao 4 - Complementacao

Adicionar uma informacao nova ao relato de teste.

Abrir a fila de moderacao.

Aprovar a contribuicao.

Mostrar a nova versao do dossie com o historico preservado.

## Demonstracao 5 - Votacao

Marcar "Nao resolvido".

Mostrar a atualizacao da contagem comunitaria.

Explicar por que essa informacao nao altera automaticamente o status de verificacao.

## Demonstracao 6 - Simulacao

Abrir o simulador.

Selecionar a regiao.

Definir um orcamento ficticio.

Comparar os cenarios calculados.

## Demonstracao 7 - Transparencia

Abrir a metodologia.

Mostrar:

- Fontes oficiais.
- Regras de processamento.
- Criterios de prioridade.
- Limitacoes.
- Ano de referencia.

---

# 31. CRITERIOS DE CONCLUSAO

O MVP sera considerado funcional quando:

- [ ] O PWA abrir em dispositivos moveis.
- [ ] O usuario puder selecionar estado e municipio.
- [ ] O usuario puder selecionar bairros disponiveis.
- [ ] Os problemas aparecerem no mapa.
- [ ] Os problemas possuirem paginas individuais.
- [ ] O sistema aceitar relatos autenticados.
- [ ] A busca por duplicidade funcionar.
- [ ] Um relato puder complementar outro.
- [ ] A moderacao funcionar.
- [ ] As alteracoes forem versionadas.
- [ ] A votacao funcionar sem duplicacoes.
- [ ] Fontes externas puderem ser associadas.
- [ ] Indicadores oficiais aparecerem corretamente.
- [ ] O simulador funcionar.
- [ ] A interface for responsiva.
- [ ] As permissoes de acesso forem testadas.
- [ ] As limitacoes forem documentadas.
- [ ] O sistema estiver publicado em HTTPS.

---

# 32. VERSAO 2.0 - EVOLUCAO NACIONAL

Apos a validacao do MVP, o projeto podera evoluir para:

- Cobertura nacional de problemas comunitarios.
- Conectores estaduais e municipais.
- Atualizacao automatica de fontes.
- Busca inteligente de noticias.
- Identificacao semantica com embeddings.
- Alertas de mudancas de situacao.
- Analise temporal.
- Comparacao entre bairros e municipios.
- API publica para pesquisadores.
- Painel para organizacoes comunitarias.
- Relatorios territoriais exportaveis.
- Encaminhamento assistido a canais oficiais.
- Integracao formal com ouvidorias, quando autorizada.
- Monitoramento de obras associadas a problemas.
- Indicadores avancados de desigualdade territorial.

O crescimento sera gradual, respeitando a qualidade das fontes e a capacidade de moderacao.

---

# 33. DIFERENCIAL DO INVISIVEL

O projeto nao pretende apenas mostrar onde existem problemas.

Pretende organizar um ciclo completo:

```text
IDENTIFICAR
    |
    v
DOCUMENTAR
    |
    v
CRUZAR COM DADOS PUBLICOS
    |
    v
VERIFICAR E COMPLEMENTAR
    |
    v
PRIORIZAR
    |
    v
SIMULAR ALTERNATIVAS
    |
    v
ACOMPANHAR
    |
    v
VERIFICAR RESULTADOS
```

A inovacao proposta esta na integracao dessas etapas em uma experiencia publica, territorial e colaborativa.

---

# 34. RESUMO EXECUTIVO

**Nome:** INVISIVEL

**Definicao:** Plataforma de inteligencia territorial e participacao cidada.

**Problema:** Dados publicos e relatos comunitarios encontram-se dispersos, dificultando a identificacao, a verificacao e o acompanhamento de necessidades coletivas.

**Solucao:** Um PWA que organiza problemas por territorio, conecta informacoes oficiais, detecta duplicidades, recebe contribuicoes e permite simular prioridades de investimento.

**Cobertura planejada:** Brasil.

**MVP:** Serra e Vitoria, Espirito Santo, com navegacao nacional e dados progressivamente incorporados.

**Fontes principais:** IBGE, INEP, DATASUS, SINISA, Obrasgov.br e fontes publicas complementares.

**Frontend:** React + TypeScript.

**Backend:** FastAPI.

**Banco:** PostgreSQL + PostGIS.

**Autenticacao:** Supabase Auth.

**Dados oficiais:** APIs e downloads governamentais tratados por conectores.

**Motor inteligente inicial:** Similaridade textual, geoespacial e regras documentadas.

**Funcionalidade central:** Problemas territoriais unificados, com relatos, evidencias, fontes e acompanhamento.

**Diferencial analitico:** Relacionar problemas comunitarios com indicadores publicos e comparar alternativas de investimento.

**Restricao principal:** Nem todo dado esta disponivel na escala de bairro, e relatos nao comprovados nao podem ser tratados como fatos oficiais.

**Objetivo final:** Tornar problemas coletivos visiveis, verificaveis e acompanhaveis pela sociedade.

**Slogan:**

"INVISIVEL - O que os dados mostram, a cidade nao pode ignorar."