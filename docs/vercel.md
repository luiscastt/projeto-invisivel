# Vercel Services + Supabase

Implantação de produção validada em 22/11/2026: https://projeto-invisivel.vercel.app . Serviços app (FastAPI) e web (Vite), PostgreSQL via Session pooler confirmado no painel Supabase e bucket de fotos privado.

## Serviços

- `app`: FastAPI na raiz, entrypoint `index:app`; público em `/api` e `/api/*`, incluindo documentação e OpenAPI. O caminho original é preservado.
- `web`: Vite em `apps/web`, build próprio para `dist`, público nas outras rotas. Fallback SPA mantém links diretos como `/dados`.
- Sem bindings internos: as chamadas são do navegador para `/api/v1` no domínio público; o frontend estático não faz chamadas entre funções. Não exponha URLs internas como variáveis VITE_.

## Variáveis necessárias

```dotenv
APP_ENV=production
AUTH_PROVIDER=supabase
SEED_DEMO=false
DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:SENHA_CODIFICADA@POOLER_HOST:5432/postgres?sslmode=require
DATABASE_SCHEMA=invisivel
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=CHAVE_PUBLISHABLE
SUPABASE_SECRET_KEY=CHAVE_SECRETA_APENAS_BACKEND
STORAGE_PROVIDER=supabase
SUPABASE_STORAGE_BUCKET=invisivel-evidence
ADMIN_EMAILS=EMAIL_VERIFICADO_DO_MODERADOR
```

Copie o hostname e os parâmetros de **Connect → Session pooler** no painel Supabase. A conexão direta foi testada nesta máquina; ela pode usar IPv6, e isso não comprova conectividade de uma Function Vercel. Não adivinhe o hostname/região do pooler. A senha deve ser codificada na URL (o gerador local já faz isso).

O backend usa NullPool e desabilita prepared statements no psycopg. A conexão de sessão preserva o search_path do schema privado.

Configure `PUBLIC_ORIGIN` com o domínio HTTPS final, se usar domínio próprio. Quando omitido, a aplicação usa VERCEL_PROJECT_PRODUCTION_URL em produção e VERCEL_URL em preview. Permanece a validação estrita de Origin nas mutações. Configure no Supabase Auth o Site URL e Redirect URLs para o domínio escolhido e `/entrar`; o cadastro envia explicitamente o retorno à origem do navegador.

## Publicação

Com Vercel CLI autenticado, a partir da raiz:

```sh
npx vercel@66.6.0 login
npx vercel@66.6.0 link
npm run vercel:env
npx vercel@66.6.0 dev --listen 3000
npx vercel@66.6.0 deploy --prod
```

Antes de `vercel:env`, confirme o DATABASE_URL do pooler em `work/supabase-production.env`. O script envia variáveis por stdin para Preview e Production, como secrets; não inclui credenciais nos argumentos nem nos logs. Requer `.vercel/project.json` já vinculado e não cria projetos automaticamente.

A configuração inicial não possuía variáveis de ambiente, o que impedia importar index.py e causava FUNCTION_INVOCATION_FAILED. Após autenticação da CLI como luiscastt, o checkout foi vinculado ao projeto existente; 11 variáveis foram enviadas como secrets para Production e Preview, e a implantação foi reconstruída. A nova produção dpl_CC7Qz61PrUwVS8wkez2TeWxet4F6 foi verificada no domínio público. A senha PostgreSQL e as chaves Supabase não substituem login Vercel.

## Dados e testes

Fotos já usam Supabase Storage privado, com moderação/autorização pela API e exclusão com repetição. Não use `/tmp` como persistência. Os snapshots oficiais versionados são lidos do pacote; sync que grave arquivos deve rodar fora de Functions e gerar novo deploy.

Verifique `/`, `/dados`, `/api/v1/health`, `/api/v1/auth/config`, `/api/docs`, assets e `/sw.js`. `/api/v1/inexistente` deve responder com o 404 da API. Teste cadastro, confirmação de e-mail, moderação e foto em uma implantação real antes de apresentar o domínio como disponível.

O rate limiter atual é por instância; não é uma quota distribuída entre Functions. O MVP mantém os controles locais e precisa dessa evolução antes de receber grande volume.

Referências: https://vercel.com/docs/services, https://vercel.com/docs/services/routing, https://vercel.com/docs/services/bindings, https://vercel.com/docs/frameworks/backend/fastapi e https://supabase.com/docs/guides/database/connecting-to-postgres.

## Verificação de produção em 22/11/2026

HTTP 200 confirmado em `/`, `/dados`, `/api/v1/health`, `/api/v1/auth/config`, `/api/v1/states`, resumo/contexto/cadastros oficiais de Serra, `/api/v1/issues`, `/api/docs` e `/api/openapi.json`. A saúde informa production e o login usa Supabase, sem contas locais. Rota inexistente retorna JSON 404; mutação sem login retorna 401; origem externa retorna 403. A chave secreta não aparece nas respostas verificadas.

A região e o hostname de Session pooler foram obtidos pelo painel do próprio projeto, não por sondagem de servidores. As credenciais permaneceram nos secrets Vercel e em arquivos locais ignorados. A entrega de e-mails e URLs de retorno do Supabase Auth continuam exigindo validação específica; estes testes não enviaram e-mails nem criaram relatos públicos reais.
