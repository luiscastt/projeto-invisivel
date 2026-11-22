# INVISIVEL

**O que os dados mostram, a cidade não pode ignorar.**

MVP de inteligência territorial e participação cidadã. Reúne navegação nacional, indicadores oficiais, mapas, relatos moderados, dossiês versionados, votação e simulação de investimentos. Piloto detalhado: **Serra e Vitória, Espírito Santo**.

## Apresentação breve do MVP

O **INVISIVEL** é uma plataforma de inteligência territorial e participação cidadã que reúne dados públicos e relatos da comunidade para tornar problemas coletivos visíveis e acompanháveis. Pelo mapa, o usuário consulta indicadores, escolas, estabelecimentos de saúde, obras e convênios oficiais. Também pode relatar um problema, acrescentar evidências e acompanhar sua evolução em um dossiê revisado pela moderação. O sistema sugere relatos semelhantes para evitar duplicidades, registra a percepção da comunidade e permite comparar cenários hipotéticos de investimento. O diferencial é conectar **território, dados oficiais e participação**, distinguindo informação governamental, relato ainda não comprovado e simulação.

Para o professor: selecione Serra, abra **Dados e serviços**, mostre um cadastro no mapa, ative a demonstração para abrir um dossiê e compare dois cenários no simulador. O sistema apoia a discussão de prioridades; não substitui uma ouvidoria oficial nem resolve problemas automaticamente. [Roteiro de três minutos](docs/apresentacao-mvp.md).

## Executar

Requisito: **Node.js 22.12+**. Nesta entrega, as dependências, o ambiente Python e o build já estão preparados no checkout indicado.

```powershell
cd C:\Users\Castt\Documents\GitHub\projeto-invisivel
npm start
```

Abra **http://127.0.0.1:8000**. API/OpenAPI: **http://127.0.0.1:8000/api/docs**. A interface compilada e a API são servidas pelo mesmo processo. Encerre uma execução antes de iniciar outra na mesma porta.

Em um clone novo:

```powershell
npm run setup
npm start
```

O instalador baixa `uv` da Astral, confere o SHA-256 publicado, prepara Python portátil em `work/runtime`, instala as versões dos lockfiles e compila a interface. Não é necessário instalar Python globalmente. O primeiro preparo exige internet. Os snapshots oficiais estão incluídos.

Para desenvolvimento: `npm run dev`. Interface em **http://127.0.0.1:5173**, API na porta **8000**, com proxy local e atualização automática. `Ctrl+C` encerra a execução.

### Contas de teste local

Em **Entrar**, os botões **Cidadão** e **Moderação** preenchem os campos; depois clique em **Entrar**.

| Papel | E-mail | Senha |
| --- | --- | --- |
| Participante | `cidadao@invisivel.local` | `Invisivel!2026` |
| Administração | `admin@invisivel.local` | `Invisivel!2026` |

Essas contas são criadas somente em desenvolvimento com autenticação local. E-mail local não tem propriedade verificada. **Não exponha esse modo à internet.** O servidor de desenvolvimento fica no loopback. Produção exige Supabase Auth, PostgreSQL e origem HTTPS, sem criar essas contas.

## Funcionalidades entregues

- Painel, pesquisa nacional, seleção de UF/município e bairros disponíveis.
- Mapa MapLibre, base OpenStreetMap com atribuição, limites municipais/bairros oficiais, marcadores publicados, controle de camadas e seleção de ponto.
- Listagem filtrável, busca sem distinção de acentos, página individual, relatos originais, fontes, imagens e histórico de versões.
- Cadastro/login local para teste e integração Supabase em produção; perfil, exportação e exclusão/pseudonimização de conta.
- Relato por etapas, coordenadas ou geolocalização opcional, imagens privadas, referências, sugestão de duplicidade, vínculo ou novo problema e protocolo.
- Moderação: aprovar, rejeitar, pedir esclarecimento privado, vincular, publicar, alterar situação, restaurar versão, unificar problemas e retirar evidência publicada com auditoria.
- Resposta privada a esclarecimentos no mesmo protocolo, preservando o texto original.
- Um voto ativo por conta/problema, substituível e removível. A percepção comunitária não muda automaticamente a verificação.
- Simulador com orçamento, custo hipotético, critérios alternativos, comparação, saldo e cenários persistidos por link.
- Fontes, metodologia e privacidade públicas; interface responsiva, navegação móvel de até cinco destinos, teclado e PWA.

A base comunitária **real inicia vazia**. Ausência de relatos não significa ausência de problemas. **Modo demonstração** mostra somente cenários fictícios, marcados no texto e separados dos resultados reais. Os indicadores oficiais continuam reais em ambos os modos.

## Fontes oficiais e cobertura

As integrações entregues consultam APIs públicas HTTPS de **JSON/GeoJSON**, sem raspar páginas ou gerar números. URL, data de coleta, referência, unidade e escala são preservadas.

| Conteúdo integrado | Fonte | Cobertura/referência |
| --- | --- | --- |
| UFs e municípios | [Localidades IBGE](https://servicodados.ibge.gov.br/api/docs/localidades) | Catálogo coletado: 27 UFs e 5.571 municípios |
| População residente | [SIDRA 4714](https://sidra.ibge.gov.br/tabela/4714), variável 93, API Agregados v3 | 5.570 municípios; Censo 2022 |
| Estimativa populacional | IBGE Pesquisas, indicador `29171` | Serra/Vitória; último ano disponível |
| Escolarização de 6 a 14 anos | IBGE Pesquisas, indicador `60045` | Serra/Vitória; 2022, percentual |
| Mortalidade infantil | DATASUS distribuído pelo IBGE, indicador `30279` | Serra/Vitória; óbitos por mil nascidos vivos |
| Esgotamento sanitário | [SIDRA 6805](https://sidra.ibge.gov.br/tabela/6805), variável `1000381`, categoria `46290` | Serra/Vitória; 2022, percentual de domicílios |
| Malhas municipais | IBGE Malhas v3 | GeoJSON simplificado do piloto |
| Limites de Serra | [Prefeitura da Serra](https://mapas.serra.es.gov.br/server/rest/services/Hosted/PLA_Bairro/FeatureServer/0) | 130 feições, incluindo Área Rural |
| Bairros de Vitória | [GeoWeb municipal](https://gis.vitoria.es.gov.br/arcgis/rest/services/Opendata/HubGeoweb/MapServer/32) | 80 feições |

O código atual `5101837`, Boa Esperança do Norte, não possui observação própria no Censo 2022. Essa lacuna aparece como dado ausente. Não são inventados limites ou indicadores de bairros fora da cobertura.

Conferência da coleta:

| Indicador | Serra | Vitória | Referência |
| --- | ---: | ---: | --- |
| População residente | 520.653 | 322.869 | 2022 |
| Escolarização de 6 a 14 anos | 98,34% | 99,24% | 2022 |
| Domicílios com esgoto por rede geral, pluvial ou fossa ligada à rede | 91,23% | 99,67% | 2022 |

O último indicador inclui rede pluvial/fossa ligada à rede e usa **domicílios particulares permanentes ocupados** como denominador. Não equivale exclusivamente a rede coletora nem a percentual de moradores. A pesquisa também consultou publicações estaduais do IJSN; elas não substituem silenciosamente as séries estruturadas utilizadas.

### Integrações verificadas nesta atualização

| Fonte | Conteúdo integrado | Cobertura da coleta |
| --- | --- | --- |
| SINISA Gestão Municipal | Informações institucionais e quatro indicadores numéricos; células vazias preservadas | Edição **2024**, referência **2023**; 5.570 municípios, 4.707 respondentes |
| CNES | Estabelecimentos ativos, com indicação de SUS ambulatorial e coordenadas oficiais quando válidas | 689 em Serra; 1.409 em Vitória; inclui rede privada |
| Obrasgov | Projetos vinculados ao município pela geometria oficial, situação e investimento previsto | 63 em Serra; 347 em Vitória |
| Portal da Transparência | Convênios federais com filtro de vigência da API de 01/01/2020 a 31/12/2030 | 98 em Serra; 622 em Vitória |
| SEDU/ES | Cadastro compacto de escolas **da rede estadual**, com código INEP | 376 escolas estaduais; 47 em Serra e 13 em Vitória |
| Ouvidoria estadual ES | Agregados de 2025 por município informado, tipo e situação | 27.536 registros lidos; 22.545 agregados em 78 municípios; 4.991 sem vínculo territorial |

Os registros estão em **Dados e serviços**, e as coordenadas disponíveis formam uma camada distinta dos problemas comunitários. Ausência de coordenada não gera ponto inventado. Valores previstos de obras e valores liberados em convênios não são custo de reparar problemas do cidadão.

### Por que CNES e Obrasgov não estavam integrados?

A entrega anterior deixou esses conectores pendentes. Isso não era prova de que as APIs fossem inacessíveis. Ambos retornaram HTTP 200 nesta verificação e agora possuem coleta paginada, validação, snapshots e visualização.

- **CNES:** `/v1/` é o endereço da documentação. A rota que respondeu é `https://apidadosabertos.saude.gov.br/cnes/estabelecimentos`. O filtro municipal usa seis dígitos, `status=1`, `limit=20` e `offset` como **número de página**, iniciando em zero. Todos os códigos municipais são conferidos. Contatos, e-mails e telefones não são republicados. Cadastro ativo não comprova disponibilidade efetiva de atendimento.
- **Obrasgov:** a coleta usa `/obras/geometria?cod_ibge=...` e depois `/obras/projeto-investimento?id_projeto_investimento=...`, com deduplicação e `pins` oficiais. O cadastro federal não cobre necessariamente todas as obras municipais.
- **Transparência:** a chave fornecida retornou HTTP 200 e fica somente no `.env` local. Filtros de datas precisam dos dois limites; enviar apenas a data inicial retornou HTTP 400. Chaves não entram em URLs, logs, snapshots, README ou frontend. As faixas acima são os filtros enviados à API, não uma estimativa de investimento municipal total.

### Fala.BR, Painel Resolveu? e alternativa estadual

A [documentação do Fala.BR](https://falabr.cgu.gov.br/help) é pública, mas isso não autoriza a consulta das manifestações. `GET /api/manifestacoes` sem token retornou **HTTP 401**. A [CGU exige conta webservice autorizada, perfil e token](https://wiki.cgu.gov.br/index.php/Fala.BR_-_M%C3%B3dulo_Ouvidoria). A chave do Portal da Transparência não autentica o Fala.BR.

O [Painel Resolveu?](https://centralpaineis.cgu.gov.br/visualizar/resolveu) está acessível por link no INVISIVEL. A base nacional estatística pública em ZIP é uma fonte separada: a consulta Range identificou aproximadamente **416 MB**. O painel não é apresentado como API operacional anônima.

Como alternativa funcional para o piloto, foi integrada a **ouvidoria estadual do ES** via CKAN, com paginação completa. Somente contagens agregadas de 2025 são publicadas; protocolos e textos individuais não saem no resultado. O município é o informado no registro de ouvidoria, não a localização de uma ocorrência de rua. Registros sem vínculo não são redistribuídos. **Essa base é estadual e não é apresentada como a base federal do Fala.BR.**

### Educação sem baixar os microdados nacionais

Para demonstrar o MVP, o usuário não precisa baixar o arquivo nacional enorme. A API oficial compacta da **SEDU/ES** já fornece nome, código INEP e coordenadas das escolas estaduais. Três registros sem coordenadas confiáveis permanecem listados sem marcador. A escolarização censitária do IBGE continua disponível separadamente.

Código INEP é identificador: esse cadastro estadual não substitui os microdados completos do Censo Escolar. A integração nacional continua catalogada à parte. As sinopses estatísticas municipais são uma alternativa oficial menor. O download direto testado apresentou problema de cadeia TLS neste ambiente; a verificação do certificado não foi desativada. Ver [fontes de ouvidoria e educação](docs/data-sources/ouvidoria-educacao.md).

### Interpretação do SINISA

A planilha enviada é de **Gestão Municipal**, edição **2024**, referência **2023**. O importador valida cabeçalhos, códigos IBGE e SHA-256. Serra e Vitória declararam plano de saneamento e um prestador de água e um de esgoto. Valores de investimento não informados permanecem ausentes, sem virar R$ 0. Isso não é percentual de cobertura por bairro. A base normalizada é distribuída em gzip, com aproximadamente 425 KB. [Campos, linhas e metodologia](docs/data-sources/sinisa-2024.md).

Continuam pendentes os microdados nacionais completos do INEP e a API operacional autenticada do Fala.BR. Referências jornalísticas continuam manuais e revisadas.

Detalhes: [APIs verificadas](docs/data-sources/verified-apis.md) e [coletor](pipelines/README.md).

### Atualização dos dados

```powershell
npm run sync:data
```

O comando atualiza IBGE, CNES, Obrasgov, Transparência (quando a chave está configurada), escolas estaduais e ouvidoria estadual. O painel administrativo também pode iniciar a sincronização. A navegação lê snapshots locais, sem consultar uma API federal a cada página. Cada coletor preserva seu cache anterior quando falha e registra proveniência, referências, horários, hashes, registros e erros em seu manifesto.

```powershell
npm run sync:services
npm run sync:es
npm run import:sinisa -- --file "C:\Users\Castt\Downloads\copy_of_SINISA_GESTAO_MUNICIPAL_Informacoes_2024.xlsx" --compress
```

Em outra instalação, configure `PORTAL_TRANSPARENCIA_API_KEY` no `.env`; o exemplo contém somente o nome da variável. O XLSX original permanece fora do Git. A versão pública normalizada comprimida e seu manifesto podem ser versionados. O SINISA é reimportado quando outro arquivo/edição é fornecido.

As substituições são atômicas por arquivo. Não execute sincronizações simultâneas. Operação distribuída exige publicação por geração completa e serialização de jobs.

Regras: ausência é `null`, nunca zero; escala municipal não é escala de bairro; estatística não comprova ocorrência pontual; votos não comprovam veracidade. Anos/metodologias diferentes não são somados em índice artificial. Vulnerabilidade composta e prioridade de 100 pontos ficam **sem avaliação** enquanto faltarem insumos verificados.

## Arquitetura e tudo que foi utilizado

```text
APIs oficiais → pipeline Python → cache JSON/GeoJSON com proveniência
                                          ↓
PWA React ← /api/v1 ← FastAPI → SQLAlchemy → SQLite local / PostgreSQL produção
                         ↓
             relatos, moderação, imagens privadas, votos e versões
```

| Camada | Ferramentas e finalidade |
| --- | --- |
| Interface | React 19, TypeScript estrito, Vite 7, React Router 7 |
| Dados remotos | TanStack Query 5; invalidação após mutações e API própria no mesmo domínio |
| Design | CSS próprio responsivo, Lucide, tipografia do sistema e paleta verde/teal; Tailwind/shadcn não foram necessários |
| Mapas | MapLibre GL JS 5, GeoJSON, OpenStreetMap com atribuição, Shapely para validação territorial |
| Gráficos | Recharts 3 para comparação de cenários |
| PWA | Manifest, ícones PNG, plugin Vite próprio gerando service worker e cache versionado pelo build |
| Backend | Python 3.13, FastAPI, Pydantic, pydantic-settings e Uvicorn |
| Persistência | SQLAlchemy 2, SQLite local, Psycopg 3; PostgreSQL/PostGIS/pg_trgm preparados para produção |
| Ingestão | HTTPX, biblioteca padrão, validação, threads limitadas, SHA-256 e escrita atômica |
| Leitura SINISA | openpyxl em modo somente leitura e gzip para o catálogo normalizado |
| Fotografias | Pillow: decode, orientação, redimensionamento e recodificação JPEG sem metadados originais |
| Identidade | Local: scrypt, sessões opacas por hash e cookies HttpOnly; produção: Supabase Auth validado no servidor |
| Testes | pytest, TestClient/HTTPX2, Vitest, Testing Library e Playwright/Chromium |
| Operação | uv/uv.lock, npm/lockfiles, Docker multi-stage, Compose, Caddy e GitHub Actions |

Arquivos são armazenados privadamente no servidor, com endpoint autorizado e volume persistente. **Supabase Storage não é usado** nesta implementação. Não há API paga de IA, embeddings ou redação generativa. Pandas/GeoPandas não foram incluídos porque os conectores entregues processam JSON/GeoJSON, sem necessidade dessas dependências.

```text
apps/api/app/           API, identidade, regras, moderação, mídia e simulação
apps/api/tests/         domínio, integração e regressões
apps/web/src/           páginas, mapa, formulários, componentes e testes
apps/web/public/        manifesto e identidade visual
pipelines/             conectores, sincronização e testes sem rede
data/official/         snapshots e manifesto de ingestão
database/migrations/   extensões e índices de produção
scripts/               instalação, execução, checks e teste de navegador
tests/e2e.mjs          percurso integrado com banco isolado
docs/                  especificação original, contrato e fontes
work/                  arquivos temporários e ambientes ignorados pelo Git
```

### Métodos e integridade

Relato e problema são entidades distintas. O texto original aprovado é preservado. Aprovação/complemento, restauração e mudança de situação criam versões e auditoria. Fusão conserva a URL original e não soma votos duplicados da mesma conta. Esclarecimentos são respostas privadas. Justificativas de decisões publicadas são públicas, como indicado no painel.

Duplicidade: geografia **40%**, texto normalizado **35%**, categoria **15%**, tempo **10%**. Limiares experimentais **0,65** (revisar) e **0,85** (forte). Municípios distintos não são associados. Categorias diferentes não geram sugestão forte. Não há fusão automática nem modelo semântico treinado; paráfrases complexas podem não ser detectadas.

Simulação: cálculos em **centavos**, custo igual e hipotético por registro. Capacidade = parte inteira do orçamento/custo; seleção limitada aos problemas elegíveis. A intervenção é infraestrutura genérica: não afirma custo real de pavimentação/iluminação. Sem escores completos, a estratégia de prioridade usa ordem estável por identificador e informa a limitação. Recência/relatos são critérios descritivos. Não estima efeito causal, população beneficiada nem resolve problemas reais.

## Segurança e privacidade

- Consultas públicas não retornam e-mails, IDs de autor, fila pendente ou auditoria privada. Fotos pendentes exigem dono ou administração.
- Sessão local: cookie HttpOnly/SameSite Lax, sete dias, revogação no logout. Autenticação local é bloqueada em produção.
- Supabase exige e-mail confirmado. Papel administrativo deriva de `ADMIN_EMAILS` e é recalculado com a identidade atual, sem confiar em metadados editáveis pelo cliente.
- Origens de escrita são controladas. Limites por IP: 180/min público, 20/min autenticação, 60/min participação, 2/min sincronização. O limitador é em memória para um worker; múltiplas réplicas exigem infraestrutura compartilhada.
- Corpo limitado antes do parser multipart; foto de até 5 MiB e 20 milhões de pixels. JPEG/PNG/WebP são decodificados e recodificados sem EXIF/GPS. A moderação pode retirar uma imagem publicada com auditoria.
- Referências exigem HTTPS público, sem credenciais, IP privado ou autoridade ambígua. Fontes oficiais precisam de domínio governamental brasileiro. URLs arbitrárias dos relatos não são baixadas pelo servidor.
- Transações são confirmadas antes da resposta de sucesso; votos têm unicidade. Mutações usam locks no PostgreSQL. SQLite serializa escritas em um processo.
- Exclusão remove sessões/votos, limpa conteúdo e localização ainda privados e pseudonimiza a atribuição pública sem reescrever o relato aprovado. Identidade externa Supabase requer também exclusão pelo operador do provedor.

O PWA guarda **somente o shell público**. Não coloca API, fotos privadas, conta ou auditoria em Cache Storage. Offline, a interface abre, mas consultas e envios exigem conexão. Não há fila silenciosa de relatos offline. O provedor de tiles recebe as requisições cartográficas do navegador.

Limpeza de sessões expiradas, uploads privados abandonados há mais de 24 horas e imagens rejeitadas há mais de 30 dias:

```powershell
npm run cleanup
```

Agende diariamente no ambiente de operação. Evidências em análise, arquivos públicos e histórico não são apagados por essa rotina. Dados rejeitados sem mídia permanecem até a definição de retenção institucional. Faça backup do banco, uploads e cache.

A página de privacidade descreve o funcionamento do MVP. Antes de operação pública, o responsável deve definir controlador, contato, bases legais, retenção e política institucional. O software não declara conformidade jurídica automática.

## Verificação e teste exploratório

```powershell
npm test
npm run test:e2e
```

`npm test`: API/ingestão, interface, TypeScript e build. `test:e2e`: Chromium compatível, API em porta dinâmica e **banco temporário próprio**, encerrado no final. Não insere testes na sua base principal. Capturas/logs ficam em `work/`.

Foram exercitados: território, duplicidades, privacidade, aprovação/complemento, original e versões, voto substituído/removido, simulação determinística, imagens sem EXIF, permissões, revogação administrativa, exclusão, falha de commit, URLs ambíguas, rate limiting, esclarecimentos, retirada de evidência e preservação de cache. No navegador: painel real, mapa visível, formulário, moderação, votos, comparação, rotas, viewport móvel de 390 px, PWA offline e ausência de cache privado/erros de página.

A suíte automatizada usa SQLite e contratos simulados, e a integração real PostgreSQL/Supabase Auth/Storage também foi exercitada com dados temporários isolados e removidos ao final. **Docker, PostGIS e a implantação Vercel ainda precisam de validação no ambiente de destino**. Veja [a verificação da integração](docs/supabase.md).

Roteiro sugerido:

1. Confira Serra/Vitória, fontes e anos; pesquise outro estado/município e observe as lacunas explícitas.
2. Ative a demonstração, abra um dossiê no mapa e depois volte à base real.
3. Entre como Cidadão e envie um relato dentro do município. Acompanhe o protocolo sem publicação automática.
4. Entre como Moderação; aprove, rejeite ou peça esclarecimento. Responda pelo perfil do cidadão.
5. Envie relato parecido, confirme o vínculo, aprove o complemento e confira as versões.
6. Altere/remova votos e compare simulações. A situação verificada não deve mudar por voto nem simulação.
7. Teste no celular, instale o PWA quando oferecido e desconecte a rede para ver o shell offline.

## Implantação permanente em HTTPS

Foram entregues `Dockerfile`, `compose.yaml`, `Caddyfile`, migrações, CI e `.env.example`. **Não houve publicação remota**: domínio, servidor e projeto Supabase de produção não estavam configurados. O endereço local está pronto para teste.

Em servidor com Docker Compose, DNS e portas 80/443, configure `.env` sem versioná-lo:

```dotenv
DOMAIN=invisivel.seudominio.org
POSTGRES_PASSWORD=senha_forte_sem_caracteres_reservados_de_URL
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=chave_publica_do_projeto
ADMIN_EMAILS=moderacao@seudominio.org
```

Supabase: confirmação obrigatória de e-mail, URLs de retorno e envio de mensagens configurados. Use chave pública, **nunca `service_role` no cliente**. Credenciais de serviços restritos ficam no backend, jamais em variáveis `VITE_*`.

```sh
docker compose up -d --build
docker compose exec -T db psql -U invisivel -d invisivel < database/migrations/002_geospatial_indexes.sql
```

No PowerShell, para a segunda etapa:

```powershell
Get-Content database/migrations/002_geospatial_indexes.sql | docker compose exec -T db psql -U invisivel -d invisivel
```

Execute a segunda migração depois que a API criar as tabelas. `001` habilita PostGIS/pg_trgm no primeiro provisionamento; `002` adiciona geometria gerada, índices espacial/trigram e largura do estado de moderação. Caddy provisiona TLS após configuração correta do domínio/rede. Banco, uploads, cache e certificados usam volumes persistentes. Mudanças futuras de schema requerem migrações incrementais.

O motor do MVP calcula duplicidade em Python/Shapely. Índices PostgreSQL ficam preparados; não há troca automática para SQL geoespacial. Antes de grande volume, mova agregações/paginação para SQL, compartilhe o rate limiter e publique snapshots por geração. A busca nacional automática de notícias, push, embeddings, ranking sem dados suficientes, protocolos oficiais automáticos e previsão causal continuam fora do MVP.

Veja a [especificação original](docs/superpowers/specs/2026-11-20-invisivel.md), o [contrato da API](docs/api-contract.md) e as [decisões da entrega](docs/architecture/decisions.md).

## Vercel Services e Supabase

Dois serviços em `vercel.json`: FastAPI em `/api` e Vite nas demais rotas. PostgreSQL, Auth e fotos em Storage privado estão integrados ao Supabase e foram verificados com fluxo real. Consulte [integração Supabase e execução local](docs/supabase.md) e [configuração Vercel](docs/vercel.md). Não houve deploy Vercel validado: faltam autenticação/vínculo na Vercel e configuração do pooler/domínio de implantação.
