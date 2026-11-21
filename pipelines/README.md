# Coleta de dados oficiais

Execute na raiz do projeto, com as dependências do repositório instaladas.

~~~sh
python -m pipelines.sync --output data/official
~~~

A API consulta o cache local. A coleta faz requisições HTTPS para endereços fixos do IBGE e das prefeituras da Serra e de Vitória. As conexões têm tempo limite e repetem falhas transitórias. Cada resposta válida gera registro de URL, instante de coleta, tamanho e SHA-256 no manifesto.

| Arquivo | Conteúdo |
| --- | --- |
| `catalog.json` | Estados e municípios do Brasil. Os municípios do piloto têm ponto interno de referência `[longitude, latitude]`. |
| `indicators-{codigo}.json` | Observações oficiais dos dois municípios do piloto, com unidade, período e proveniência. |
| `geometry-{codigo}.json` | Malha municipal simplificada do IBGE em GeoJSON. |
| `neighborhoods-{codigo}.json` | Identificador, nome, origem e polígonos dos serviços geográficos municipais. A camada de Serra inclui uma feição de Área Rural. |
| `population-national.json` | Mapa opcional de código IBGE municipal de sete dígitos para população residente em 2022. Ausência de chave significa que o Censo não disponibilizou observação para o código. |
| `sources.json` | Catálogo de fontes e estado da integração. `last_synced` corresponde à última coleta válida da fonte. |
| `ingestion-manifest.json` | Última tentativa, `jobs`, `errors`, `warnings`, `files`, `last_successful_sync` e `cache_preserved`. Cada job identifica a origem da extração. |

As respostas obrigatórias são validadas antes da primeira escrita. Em uma falha de rede ou validação obrigatória, o processo conserva os arquivos publicados e registra a tentativa no manifesto. A população nacional é uma coleta opcional. Em uma falha dessa série, o manifesto registra um aviso e a última série nacional válida permanece disponível. As substituições de arquivos individuais são atômicas.

A população municipal usa o Censo Demográfico 2022, SIDRA 4714, variável 93. O indicador de saneamento usa o percentual de domicílios particulares permanentes ocupados, SIDRA 6805, variável 1000381 e categoria 46290. A taxa de mortalidade infantil usa óbitos por mil nascidos vivos. Cada observação identifica seu ano. O Censo de 2022 reflete a divisão municipal da época da coleta.

O manifesto retorna `completed` quando os arquivos obrigatórios foram publicados e `failed` quando houve erro obrigatório. A CLI sai com código 1 em uma falha obrigatória. Os testes de normalização, proveniência e preservação de cache rodam sem rede.

~~~sh
python -m pytest -q pipelines/tests
~~~
