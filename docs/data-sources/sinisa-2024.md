# SINISA 2024 · Gestão Municipal

A primeira coleta do Sistema Nacional de Informações em Saneamento Básico ocorreu em 2024 e tem **2023 como ano de referência**. O módulo Gestão Municipal reúne declarações sobre organização dos serviços, planejamento, regulação e investimentos municipais. [Resultados do Ministério das Cidades](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa) · [Glossário de informações](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/area-do-prestador/arquivos/GLOSSARIO_INFORMACOES_SINISA_GESTAO_MUNICIPAL.pdf)

## Arquivo e importação

A cópia fornecida, `copy_of_SINISA_GESTAO_MUNICIPAL_Informacoes_2024.xlsx`, contém 5.570 registros municipais na aba `GM`. A coluna `A` marca 4.707 respondentes e 863 não respondentes. A chave na coluna `B` é o código IBGE de sete dígitos. Os códigos, descrições e unidades dos campos constam nas linhas 11 a 13. Os registros começam na linha 15.

```powershell
uv run python -m pipelines.sinisa --file "C:\caminho\copy_of_SINISA_GESTAO_MUNICIPAL_Informacoes_2024.xlsx" --output data/official --compress
```

- `sinisa-municipalities.json.gz` contém o objeto JSON indexado pelo código IBGE. Cada registro traz a situação da resposta, o ano, os campos selecionados, os indicadores numéricos e a aba e a linha de origem. Para gerar `sinisa-municipalities.json`, basta omitir `--compress`.
- `sinisa-manifest.json` registra edição, referência, data de importação, contagens, hash SHA-256, nome do XLSX e as colunas e definições dos campos selecionados. O SHA-256 da cópia fornecida é `1401ae309e5171f2f686456563001eceec09b88653e6f7b34a4442c12431d99e`.

A extração usa somente as observações municipais da aba `GM`. As abas `Detalhamento Prestadores Serv` e `Detalhamento Reguladores` têm várias linhas por município. As contagens de prestadores vêm diretamente das colunas `BJ` e `BL` de `GM`.

## Interpretação dos valores

As respostas categóricas preservam a declaração original, como `Sim` e `Não`. O marcador literal `null` da planilha representa ausência de resposta do município. Células em branco representam campos sem preenchimento. Ambos geram `value: null`, com motivos distintos (`nonrespondent` e `blank`). Um zero publicado continua valendo zero.

Os indicadores numéricos representam contagens de prestadores e os valores de investimento total realizado pelo próprio município, conforme `OGM4204` e `OGM4304`. Os totais de investimento são importados em R$/ano. Os campos `OGM1001` e `OGM1101` registram a existência declarada de serviço público de água com rede de distribuição e de esgotamento sanitário com rede coletora. Para cobertura da população e desempenho dos serviços, o Ministério das Cidades publica séries nos módulos setoriais. [Resultados por módulo](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa)

## Conferência dos municípios piloto

| Campo em `GM` | Serra `3205002`, linha 3181 | Vitória `3205309`, linha 3189 |
| --- | --- | --- |
| Respondeu ao módulo (`A`) | Sim | Sim |
| Lei que institui a Política Municipal de Saneamento Básico (`BY`, `OGM3001`) | Sim | Não |
| Plano de Saneamento Básico municipal ou regional (`CC`, `OGM3004`) | Sim | Sim |
| Instrumento de aprovação do plano (`CD:CF`, `OGM3005–OGM3007`) | Lei 4010 de 14/02/2013 | Lei 8945 de 13/05/2016 |
| Áreas abrangidas pelo plano (`CI`, `OGM3010`) | Urbana e rural | Urbana |
| Conselho Municipal com atuação específica para saneamento básico (`DD`, `OGM3201`) | Sim | Não |
| Prestadores de abastecimento de água e esgotamento sanitário (`BJ`, `BL`) | 1 de água e 1 de esgoto | 1 de água e 1 de esgoto |
| Investimentos municipais totais em água e esgoto (`AM`, `AZ`) | Ambas as células em branco | Ambas as células em branco |
