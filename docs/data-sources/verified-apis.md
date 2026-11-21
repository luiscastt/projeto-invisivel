# Fontes públicas verificadas para Serra e Vitória

Consulta em 20/11/2026. Os códigos IBGE são `3205002` para Serra e `3205309` para Vitória. Os serviços abaixo foram consultados por HTTP GET.

**Atualização da implementação:** este documento registra a pesquisa inicial. CNES, Obrasgov, Portal da Transparência, SINISA Gestão Municipal, escolas SEDU/ES e ouvidoria estadual foram posteriormente integrados. A situação atual, contagens e rotas estão no README e nos documentos `sinisa-2024.md` e `ouvidoria-educacao.md`. As notas de pendência abaixo descrevem o estado da pesquisa inicial, não substituem o catálogo atual da API.

## Indicadores municipais

| Tema | Indicador | Ano | Serra | Vitória | Unidade | Origem |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Demografia | População residente no Censo | 2022 | 520.653 | 322.869 | pessoas | IBGE, SIDRA 4714, variável 93 |
| Demografia | População estimada | 2026 | 586.901 | 343.935 | pessoas | IBGE, indicador 29171 |
| Educação | Escolarização de 6 a 14 anos | 2022 | 98,34 | 99,24 | % | IBGE, Censo 2022, indicador 60045 |
| Saúde | Taxa de mortalidade infantil | 2025 | 11,74 | 10,54 | óbitos por mil nascidos vivos | DATASUS via IBGE, indicador 30279 |
| Saneamento | Domicílios particulares permanentes ocupados com esgoto por rede geral, rede pluvial ou fossa ligada à rede | 2022 | 91,23 | 99,67 | % | IBGE, Censo 2022, SIDRA 6805, variável 1000381 |
| Território | Área da unidade territorial | 2025 | 547,631 | 97,124 | km² | IBGE, indicador 29167 |

### IBGE Pesquisas

[Valores dos indicadores para os dois municípios](https://servicodados.ibge.gov.br/api/v1/pesquisas/-/indicadores/29171%7C30279%7C60045%7C95335%7C29167/resultados/3205002%7C3205309) · [Metadados e unidades](https://servicodados.ibge.gov.br/api/v1/pesquisas/-/indicadores/29171%7C30279%7C60045%7C95335%7C29167) · [Perfil de Serra](https://www.ibge.gov.br/cidades-e-estados/es/serra.html) · [Perfil de Vitória](https://www.ibge.gov.br/cidades-e-estados/es/vitoria).

A resposta é um array de indicadores. Cada item tem `id` numérico e `res[]`. A consulta usa sete dígitos e devolve `localidade` como string de seis dígitos, `320500` ou `320530`. O período é a chave em `res` e o valor publicado é uma string com ponto decimal. Exemplo de recorte da resposta de escolarização.

~~~json
{
  "id": 60045,
  "res": [
    {"localidade": "320500", "res": {"2010": "96.9", "2022": "98.34"}, "notas": {"2010": null, "2022": null}},
    {"localidade": "320530", "res": {"2010": "97.6", "2022": "99.24"}, "notas": {"2010": null, "2022": null}}
  ]
}
~~~

Os metadados trazem `indicador`, `unidade.id`, `unidade.multiplicador`, `fonte[]` e `nota[]`. O multiplicador é 1 para os indicadores da tabela. O DATASUS usa o município de residência na taxa de mortalidade infantil. As séries podem ter lacunas, e os metadados de fonte podem terminar antes da série publicada. Preserve ano de referência e data de extração. O código 95335 mede área urbanizada em km².

### IBGE Agregados e saneamento

- A consulta da população residente devolveu `id: "93"`, `variavel: "População residente"` e `unidade: "Pessoas"`. As linhas ficam em `resultados[0].series[]`. Cada linha tem `localidade.id` de sete dígitos e `serie["2022"]` com o valor como string. [API de valores do Censo](https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93?localidades=N6%5B3205002,3205309%5D).
- A mesma variável em `N6[all]` devolveu 5.570 municípios do recorte do Censo. O catálogo territorial vigente tem 5.571 entradas. O código `5101837` de Boa Esperança do Norte não tem observação nessa série. [Série nacional verificada](https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93?localidades=N6%5Ball%5D).
- Os metadados JSON de esgotamento da tabela 6805 confirmam nível municipal `N6`, variável `381` para contagem de domicílios e `1000381` para percentual de domicílios. O JSON de valores retorna `unidade: "Percentual"` e a classificação `11558` com uma categoria, `46290`. Em `resultados[0].series[]`, `serie["2022"]` contém `"91.23"` para Serra e `"99.67"` para Vitória. [Metadados da tabela 6805](https://servicodados.ibge.gov.br/api/v3/agregados/6805/metadados) · [Consulta de valores verificada](https://servicodados.ibge.gov.br/api/v3/agregados/6805/periodos/2022/variaveis/1000381?localidades=N6%5B3205002,3205309%5D&classificacao=11558%5B46290%5D).
- O IJSN também publica percentuais de **moradores** de domicílios particulares permanentes, com denominador populacional. Para essa medida, o quadro indica 90,72% em Serra e 99,65% em Vitória. A apresentação do IBGE remete à tabela 9397. [Quadro oficial do IJSN](https://ijsn.es.gov.br/Media/IJSN/PublicacoesAnexos/S%C3%ADnteses/IJSN_Censo_2022_Domicilios.pdf) · [Apresentação do IBGE, tabela 9397](https://agenciadenoticias.ibge.gov.br/media/com_mediaibge/arquivos/c8c1e181fbe8557c7c14bdf22fc335cc.pdf).
- O SINISA 2025 tem referência 2024. O indicador `IES0001` mede a proporção da população atendida pela rede coletora de esgoto. Os resultados e glossários são públicos. O ZIP permite importação versionada. A área de coleta é destinada aos prestadores e responsáveis municipais. [Resultados SINISA](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025) · [Planilhas de esgoto de 2024](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/SINISA_ESGOTO_Planilhas_2024.zip) · [Glossário de indicadores](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/GlossrioIndicadores_ESGOTO_2024.pdf).

## Bairros e população

As malhas municipais simplificadas têm geometria GeoJSON oficial do IBGE e identificação pela propriedade `codarea`. [Malha municipal de Serra](https://servicodados.ibge.gov.br/api/v3/malhas/municipios/3205002?formato=application%2Fvnd.geo%2Bjson&qualidade=minima) · [Malha municipal de Vitória](https://servicodados.ibge.gov.br/api/v3/malhas/municipios/3205309?formato=application%2Fvnd.geo%2Bjson&qualidade=minima).

Os servidores municipais oferecem GeoJSON com `FeatureCollection.features[]`, `geometry` e `properties`. As consultas verificadas usam `outSR=4326` e retornam longitude e latitude. O limite documentado é 2.000 feições. Restrinja `outFields` aos campos necessários para a aplicação.

| Município | Camada | Campos | Evidência |
| --- | --- | --- | --- |
| Serra | `Hosted/PLA_Bairro/FeatureServer/0` | `pk_bairro_ctm`, `objectid`, `tx_bairro`, `sigla_bairro`, `populacao_censo2022`, `SHAPE__Area` | 130 feições, 129 com CTM e uma Área Rural. Lagoa de Jacaraípe, 2.801 pessoas. Jardim Tropical, 6.574. |
| Vitória | `Opendata/HubGeoweb/MapServer/32` | `codBairro`, `nome`, `regiaoAdministrativa`, `caminhoURL` | 80 polígonos com códigos únicos. Conquista, código 77. São José, código 70. |
| Vitória | `Opendata/HubGeoweb/MapServer/44` | `codBairro`, `bairro`, `populacao`, `ano`, `fonte`, `areaBairroM2`, `densidadeHabHa`, `totalDomicilios` | Camada municipal de população por bairro de 2022 documentada no serviço. |

- Serra. [Metadados da Prefeitura](https://mapas.serra.es.gov.br/server/rest/services/Hosted/PLA_Bairro/FeatureServer/0) · [GeoJSON verificado](https://mapas.serra.es.gov.br/server/rest/services/Hosted/PLA_Bairro/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson).
- Vitória. [Diretório do GeoWeb](https://gis.vitoria.es.gov.br/arcgis/rest/services/Opendata/HubGeoweb/MapServer) · [GeoJSON de limites verificado](https://gis.vitoria.es.gov.br/arcgis/rest/services/Opendata/HubGeoweb/MapServer/32/query?where=1%3D1&outFields=*&outSR=4326&f=geojson) · [Metadados da camada 44](https://gis.vitoria.es.gov.br/arcgis/rest/services/Opendata/HubGeoweb/MapServer/44?f=pjson) · [Consulta GeoJSON de população](https://gis.vitoria.es.gov.br/arcgis/rest/services/Opendata/HubGeoweb/MapServer/44/query?where=1%3D1&outFields=codBairro,bairro,populacao,ano,fonte&outSR=4326&f=geojson).

As 130 feições de Serra têm valores inteiros de população e somam 522.653. O Censo publica 520.653 para o município. Preserve os valores atribuídos a cada fonte e seus níveis geográficos. A Área Rural tem 4.442 pessoas, `objectid: 106` e CTM nulo. O Polo Industrial Tubarão tem zero publicado. Os campos `epc_saude` e `epc_educacao` carecem de período e metodologia na descrição consultada.

## Obras e estabelecimentos de saúde

**Obrasgov.br.** O OpenAPI verificado em JSON registra o servidor `/obras` e a rota `/geometria`, com `cod_ibge` inteiro, `pagina` iniciando em 1 e `tamanho_da_pagina` até 200. O contrato é `{data, total_pages, total_items, page_number, page_size}`. O campo `id_projeto_investimento` permite obter `desc_nome`, `situacao`, investimentos e pins em `/projeto-investimento`. A rota `/execucao-fisica` também usa o identificador do projeto. A API cobre registros da plataforma federal. [OpenAPI atual](https://api-publica.obrasgov.gestao.gov.br/obras/openapi.json) · [Consulta Serra](https://api-publica.obrasgov.gestao.gov.br/obras/geometria?cod_ibge=3205002&pagina=1&tamanho_da_pagina=2) · [Consulta Vitória](https://api-publica.obrasgov.gestao.gov.br/obras/geometria?cod_ibge=3205309&pagina=1&tamanho_da_pagina=2) · [Comunicado de migração](https://www.gov.br/obrasgov/pt-br/noticias/2026/comunicado-23-2026-mudancas-nos-acessos-as-apis-de-dados-abertos-do-transferegov-br-e-do-obrasgov-br).

**CNES.** A consulta pública `/cnes/estabelecimentos` retornou `{estabelecimentos: [...]}`. Cada registro pode conter `codigo_cnes`, `codigo_municipio` de seis dígitos, `codigo_uf`, `codigo_tipo_unidade`, `nome_fantasia`, `bairro_estabelecimento`, latitude e longitude decimais e `data_atualizacao`. O Swagger 2.0 v1.8.32 documenta os filtros inteiros `codigo_municipio`, `codigo_uf` e `status` (1 ativo, 0 inativo), e a paginação `limit` (até 20, segundo a descrição) e `offset` a partir de zero. A amostra municipal parametrizada ainda precisa ser verificada. Confirme `codigo_municipio` em todas as linhas e deduplique por CNES. O catálogo oficial oferece ainda arquivos em CSV, JSON e XML. Para contar unidades públicas ou com atendimento ao SUS, aplique critérios explícitos de classificação e atividade, com competência. [Swagger oficial](https://apidadosabertos.saude.gov.br/static/swagger.json) · [Consulta Serra](https://apidadosabertos.saude.gov.br/cnes/estabelecimentos?codigo_municipio=320500&limit=1&offset=0) · [Consulta Vitória](https://apidadosabertos.saude.gov.br/cnes/estabelecimentos?codigo_municipio=320530&limit=1&offset=0) · [Endpoint JSON](https://apidadosabertos.saude.gov.br/cnes/estabelecimentos) · [Catálogo público CNES](https://dadosabertos.saude.gov.br/dataset/cnes-cadastro-nacional-de-estabelecimentos-de-saude) · [Downloads do CNES](https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp).

## Fontes que exigem configuração

- O INEP publica os microdados anuais do Censo Escolar para download. A integração depende de importação versionada e consolidação por município. [Censo Escolar do INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar).
- A API do Portal da Transparência usa credencial da CGU no cabeçalho `chave-api-dados`. Cada consulta tem escopo e filtros próprios. [API de Dados do Portal da Transparência](https://portaldatransparencia.gov.br/api-de-dados).
- A API do Fala.BR exige OAuth 2.0 e permissões para consultar manifestações. O Painel Resolveu publica dados agregados. [Documentação da API](https://falabr.cgu.gov.br/help) · [Painéis e dados abertos da CGU](https://wiki.cgu.gov.br/wiki/Ouvidoria_-_Pain%C3%A9is%2C_Dados_Abertos_e_Relat%C3%B3rios).
