# Verificação da entrega — 20/11/2026

## Evidência executada

| Comando | Resultado |
| --- | --- |
| `npm run setup` | Instalador portátil, checksums, instalação por lockfiles e build concluídos com código 0 |
| `npm test` | 34 testes Python aprovados; 4 suítes / 9 testes Vitest aprovados; TypeScript e Vite concluídos com código 0 |
| `npm run test:e2e` | 5 grupos de verificações Chromium concluídos, sem erros de página |
| `npm run cleanup` | Rotina executada; nenhum arquivo privado elegível removido nesta base |
| `npm start` | Inicialização concluída em `http://127.0.0.1:8000` |
| `python -m pipelines.sync --output data/official` | Manifesto concluído, sem erros; 27 UFs, 5.571 municípios, 5.570 observações censitárias nacionais |

O E2E usa porta dinâmica e SQLite próprios. Verificou mapa com altura visível, população oficial, envio autenticado e pendente privado, aprovação administrativa, votos substituídos sem mudar verificação, cenários salvos e comparados, rotas públicas, layout de 390 px, shell offline e ausência de API no cache do PWA.

Uma revisão independente do código apontou problemas de revogação de acesso, transação antes da resposta, exclusão de informação privada, compatibilidade PostgreSQL, limites de upload, URLs e origens no modo compilado. As correções foram integradas. Regressões incluem falha forçada de commit, revogação de papel, apagamento de coordenadas privadas, fonte com autoridade ambígua, login pela porta 8000, esclarecimento privado e retirada auditada de imagem.

O conflito entre o CSS global e o CSS do MapLibre foi reproduzido no navegador: contêiner com altura zero. A regra de tamanho/especificidade foi corrigida e o E2E exige altura maior que 250 px.

## Limites da verificação

PostgreSQL/PostGIS, Docker, Caddy com domínio público e Supabase real não estavam provisionados. Seus contratos, arquivos e instruções foram preparados; a operação real desses serviços requer validação no ambiente configurado. A publicação de um servidor HTTPS permanece externa; o envio do código ao GitHub é tratado na atualização abaixo. Os detalhes de fontes pendentes e escala estão no README.

## Atualização das integrações oficiais

- Coletas CNES, Obrasgov e Portal da Transparência: HTTP 200, paginação completa e manifestos sem erros.
- SINISA: XLSX fornecido importado sem alterar o original; 5.570 municípios, referência 2023; 7 testes do importador.
- Escolas SEDU/ES: 376 registros; ouvidoria estadual: 27.536 registros de 2025 processados, com publicação exclusivamente agregada.
- Suite atual: **65 testes Python** e **11 testes de interface**, com TypeScript e build aprovados. Chromium verifica seis grupos, incluindo as novas abas oficiais.
- A revisão adicional verificou ausência de CPF, e-mail e telefone nos campos publicados e a exclusão de protocolos individuais da ouvidoria.
- Coordenadas de cadastros incompatíveis com os limites oficiais são mantidas nas listas e excluídas dos marcadores. A malha IBGE utiliza a qualidade máxima disponível na API, com tolerância cartográfica de 0,002 grau para os pontos de contexto.
- Falhas de coleta e ausência da chave de Transparência ficam explícitas; a data do último snapshot não é reescrita como se houvesse nova coleta.
- A paginação reinicia ao trocar de município. Arquivos estáticos/PWA não consomem o limite de requisições da API.
- Chave real permanece em `.env` ignorado. A inspeção dos blobs preparados para commit não encontrou a chave, banco local, uploads privados ou XLSX original.
