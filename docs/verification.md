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
- Suite das integrações oficiais antes do Supabase: **65 testes Python** e **11 testes de interface**, com TypeScript e build aprovados. Chromium verifica seis grupos, incluindo as novas abas oficiais.
- A revisão adicional verificou ausência de CPF, e-mail e telefone nos campos publicados e a exclusão de protocolos individuais da ouvidoria.
- Coordenadas de cadastros incompatíveis com os limites oficiais são mantidas nas listas e excluídas dos marcadores. A malha IBGE utiliza a qualidade máxima disponível na API, com tolerância cartográfica de 0,002 grau para os pontos de contexto.
- Falhas de coleta e ausência da chave de Transparência ficam explícitas; a data do último snapshot não é reescrita como se houvesse nova coleta.
- A paginação reinicia ao trocar de município. Arquivos estáticos/PWA não consomem o limite de requisições da API.
- Chave real permanece em `.env` ignorado. A inspeção dos blobs preparados para commit não encontrou a chave, banco local, uploads privados ou XLSX original.

## Supabase e Vercel — 22/11/2026

- Suíte final: **105 testes Python aprovados**, incluindo Storage, fila de exclusão com repetição, isolamento de schema, chaves públicas e logs sanitizados.
- **11 testes de interface**, TypeScript e build Vite aprovados.
- Chromium: seis grupos aprovados, incluindo moderação, votos, abas oficiais, layout móvel e PWA sem cache privado.
- Supabase real: conexão PostgreSQL TLS e inicialização no schema privado; 11 tabelas com RLS e sem grants diretos para anon/authenticated. Bucket invisivel-evidence privado, restrito a JPEG.
- Fluxo real com schema/identidade/objetos temporários: login, identidade persistida, envio privado de foto, EXIF removido, anonimato antes da aprovação, relato, moderação e voto. Limpeza dos dados sintéticos confirmada.
- vercel.json conferido contra as propriedades do schema publicado, usando compatibilidade Draft 7 porque a declaração Draft 4 publicada contém exclusiveMinimum numérico. Isso não substitui um build/deploy Vercel real.
- CLI Vercel 66.6.0 executada; vercel dev parou na autenticação. Não houve deploy Vercel validado. Faltam login/vínculo, pooler e URLs de retorno do domínio final.
- Credenciais reais permaneceram em work/ e .env ignorados. Nenhum segredo foi incluído no commit.

## Correção da implantação Vercel — 22/11/2026

A primeira implantação retornava 500 em todas as chamadas da API porque não havia variáveis de ambiente. O log apontava a proteção que exige APP_ENV=production. A correção consistiu em vincular o projeto existente, configurar 11 secrets de Production/Preview, confirmar o Session pooler no painel Supabase e reconstruir a produção.

Implantação verificada: `dpl_CC7Qz61PrUwVS8wkez2TeWxet4F6`, domínio https://projeto-invisivel.vercel.app . Onze rotas públicas devolveram 200, incluindo saúde em modo production, configuração Auth sem contas locais, estados, dados oficiais de Serra, issues, frontend e docs. API inexistente retornou JSON 404, voto sem login 401 e Origin externo 403. Nenhum dado sintético foi gravado nesta verificação pública.

## Base inicial de reclamações oficiais — 22/11/2026

Importação real CKAN 2025–2026: 50.736 linhas examinadas, 15.172 reclamações do recorte aceitas, 1.606 dossiês em 78 municípios. Serra 3.418/124; Vitória 2.355/120. Campos pessoais/narrativas/protocolos ausentes, coordenadas não inferidas e encerramento administrativo separado da resolução. 227 datas futuras ficaram indisponíveis, sem reinterpretar dia/mês.

Testes cobrem idempotência, retirada e reaparecimento, reassociação, preservação de decisões humanas/recursos omitidos, datas, metadados e contagens. Migração SQLite preservou relatório vinculado e integridade referencial. A validação real PostgreSQL usou schema temporário e confirmou migração/importação, dossiês e reinício sem duplicação; o schema foi removido ao final. A conexão do pooler passou a qualificar o schema em SQL e selecioná-lo por transação, pois opções iniciais de sessão podem ser ignoradas pelo provedor.

Verificação final desta atualização: **138 testes Python**, **23 testes de interface**, TypeScript/build e **sete grupos Chromium aprovados**. Em PostgreSQL isolado, migração de tabela antiga + importação completa validaram 124 dossiês/3.418 registros em Serra; reinício não duplicou dados. A aplicação passou a qualificar explicitamente as tabelas pelo schema para evitar fallback silencioso do pooler. A importação de produção concluiu com 12 tabelas protegidas por RLS, os totais de Serra/Vitória esperados e nove datas iniciais desconhecidas preservadas como null.
