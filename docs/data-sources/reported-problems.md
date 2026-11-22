# Base inicial de problemas já relatados — Ouvidoria estadual do ES

O INVISIVEL não depende de novos relatos para começar. A base inicial reúne metadados públicos de reclamações já registradas em fonte oficial, organizadas em dossiês temáticos. O registro comprova que a reclamação foi recebida, não que a alegação foi confirmada nem que existe uma ocorrência física distinta por linha.

## Fonte e cobertura

SECONT/ES, conjunto [Manifestações da Ouvidoria](https://dados.es.gov.br/dataset/manifestacoes-da-ouvidoria), API CKAN oficial:

- 2026: recurso `46ddbf22-cc80-49f3-812a-ae7c6ac88d97`.
- 2025: recurso `edbe3888-9138-4174-b52f-52394ef025cb`.
- Campos solicitados: `_id`, `Ano`, `TipoManifestacao`, `Orgao`, `Assunto`, `Municipio`, `Situacao`, `DataRegistro`, `DataSituacao`.
- Protocolos, nomes, sexo, identificação e narrativas não são coletados nem publicados pelo pipeline.

Foram lidas 50.736 linhas. O recorte conservador de reclamações sobre serviços coletivos, com pares assunto/órgão explicitamente revisados, aceitou **15.172 registros**, agrupados em **1.606 dossiês** nos 78 municípios do ES.

| Município informado na fonte | Registros aceitos | Dossiês temáticos |
| --- | ---: | ---: |
| Serra | 3.418 | 124 |
| Vitória | 2.355 | 120 |

Foram excluídos 17.700 registros de outros tipos de manifestação, 5.294 sem vínculo municipal aceito, 12.180 de assuntos não mapeados/não coletivos e 390 com pares assunto/órgão fora do recorte. A regra e os totais estão no manifesto. Elogios, pedidos de informação, denúncias e assuntos particulares não viram problemas automaticamente.

Essa é uma fonte estadual, não a totalidade dos problemas do ES, nem a base municipal da Serra ou a base federal do Fala.BR. Fora dessa cobertura, a ausência de registros não permite concluir ausência de problemas.

## Agrupamento, datas e localização

A chave de dossiê combina município informado, órgão, assunto normalizado exato e ano. Cada registro conserva identificador técnico derivado do recurso/linha, assunto, órgão, tipo, situação administrativa, data válida quando disponível, origem e coleta. O agrupamento evita criar centenas de dossiês repetidos para o mesmo tema; não é deduplicação de incidentes físicos nem contagem de moradores.

O município é o declarado na fonte; não é endereço georreferenciado. Não são criados bairro, rua, latitude/longitude ou marcador no centro da cidade. Esses dossiês aparecem na lista e no painel municipal, sem um ponto fabricado no mapa. Podem receber contribuições revisadas dentro do escopo do dossiê, mas não são unificados como se fossem uma ocorrência física única.

Situações como **Encerrada** descrevem o atendimento da ouvidoria. A situação do problema fica **não avaliada**; não se transforma automaticamente em resolvido nem em aberto verificado. O custo genérico por intervenção física do simulador não se aplica a dossiês temáticos sem localização.

A fonte contém 227 datas futuras em relação à coleta; elas são preservadas como indisponíveis no recorte, sem adivinhar troca de dia/mês. Nove dossiês não possuem data inicial válida. Nenhuma data de reclamação é inventada. A coleta e os anos de referência permanecem explícitos no manifesto.

## Persistência e atualização

`data/official/reported-problems-es.json.gz` contém apenas campos permitidos, e o manifesto inclui SHA-256, regras, qualidade e referências. A inicialização importa o snapshot em transação, com identificadores estáveis e uma marca de hash para evitar duplicação. Não chama a ouvidoria a cada requisição.

Atualização:

```sh
npm run sync:problems
```

Após revisar manifesto e contagens, publique o novo snapshot. A próxima inicialização reconcilia os registros gerenciados pela fonte. Decisões humanas, relatos, votos e histórico são preservados. Dossiês oficiais vazios e ainda não avaliados são arquivados quando deixam o recorte; isso não indica solução. Recursos de outros anos/fontes não incluídos na atualização não são apagados.

Os totais de **registros oficiais**, **dossiês** e **relatos na plataforma** ficam separados na API e na interface. Os dados de 2025 agregados na aba Dados e serviços continuam sendo uma estatística complementar; não devem ser somados novamente às reclamações importadas.
