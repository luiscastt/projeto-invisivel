# Supabase no MVP INVISIVEL

A aplicação usa PostgreSQL, Supabase Auth e o bucket privado `invisivel-evidence`. Não há chaves reais versionadas.

## Persistência e acesso

O schema PostgreSQL `invisivel` contém as tabelas SQLAlchemy. A inicialização é transacional e serializada com advisory lock para evitar corridas entre instâncias. As tabelas têm RLS habilitado, sem grants de acesso direto para anon/authenticated. A API usa a conexão SQL do backend e aplica as permissões por identidade; não há acesso direto do navegador às tabelas privadas. Outros schemas do projeto são preservados.

O navegador recebe apenas a URL Supabase e a chave publishable pelo endpoint `/api/v1/auth/config`. O backend valida a sessão no Auth, exige e-mail confirmado e deriva a moderação de `ADMIN_EMAILS`. A chave secreta fica no backend, enviada ao Storage no header `apikey`. Nunca configure a chave secret/service_role como chave pública.

Imagens são convertidas para JPEG sem EXIF/GPS, armazenadas em bucket privado, e consultadas pela API após checagem de proprietário/moderador/publicação. A aprovação não torna o bucket público. Exclusão de conta e retenção usam uma fila durável para repetir remoções se o Storage falhar.

## Configuração

Variáveis: `APP_ENV`, `AUTH_PROVIDER`, `SEED_DEMO`, `DATABASE_URL`, `DATABASE_SCHEMA`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` (aceita sb_publishable), `SUPABASE_SECRET_KEY`, `STORAGE_PROVIDER=supabase`, `SUPABASE_STORAGE_BUCKET`, `ADMIN_EMAILS` e `PUBLIC_ORIGIN`.

No ambiente desta sessão, as credenciais foram guardadas somente em `work/supabase.env` e `work/supabase-production.env`, ambos ignorados pelo Git. `.env` e o SQLite da demonstração local foram preservados.

Para executar localmente com Supabase real e o frontend compilado:

```sh
npm run build
npm run start:supabase
```

Isso usa o banco remoto e Auth real; não habilita contas locais de demonstração. Cadastre seu e-mail e confirme-o; o e-mail configurado em `ADMIN_EMAILS` recebe moderação após autenticação verificada. `npm start` continua usando a demonstração SQLite local.

## Verificação real executada

Foram exercitados, com sucesso: conexão PostgreSQL TLS, criação das tabelas, RLS/grants, login real via Auth, persistência da identidade, envio/consulta privada de foto, bloqueio de URL pública do Storage, remoção de EXIF, envio de relato pendente, aprovação e voto. Usou-se um schema de teste separado, identidade sintética e objetos temporários; todos foram removidos ao final. Nenhuma alegação fictícia foi deixada na base real.

A confirmação por e-mail está habilitada no projeto. O fluxo de envio/entrega de e-mail e a lista de redirecionamentos do domínio final precisam ser verificados com a URL de implantação. As credenciais de projeto não fornecem acesso à Management API nem autenticam a conta Vercel.

Para Vercel, veja [a configuração de implantação](vercel.md).
