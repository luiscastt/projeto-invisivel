# Aplicativo web do INVISIVEL

O painel abre em Serra (ES), em modo real. O seletor no cabeçalho consulta o catálogo nacional da API. A demonstração é ativada pelo menu e identifica os problemas ilustrativos. Os indicadores oficiais conservam seu município, fonte, ano e unidade nos dois modos.

## Execução

Na pasta `apps/web`, use Node.js 22.12 ou superior, `npm ci` e `npm run dev`. O servidor Vite atende em `http://127.0.0.1:5173` e encaminha `/api` para `http://127.0.0.1:8000`. No PowerShell, `npm.cmd` também funciona.

`npm run build` valida TypeScript com modo estrito e cria a distribuição estática na pasta `dist`. `npm run preview` serve essa distribuição localmente. Em produção, o host deve encaminhar `/api` para o backend e entregar `index.html` para as rotas da aplicação. O service worker requer HTTPS ou localhost.

## Fluxos disponíveis

| Rota | Operação |
| --- | --- |
| `/` | Resumo territorial, contagens revisadas, mapa municipal, dossiês recentes e indicadores oficiais |
| `/explorar` e `/problemas` | Mapa e lista com busca, filtros de bairro, categoria, situação e verificação, ordenação e paginação |
| `/problemas/:id` | Dossiê com textos originais, evidências, referências, versões, indicadores, votação substituível ou removível e compartilhamento |
| `/relatar` | Localização manual, geolocalização por solicitação ou ponto no mapa, descrição, fotos, referências, correspondências e envio para moderação |
| `/relatar?problema=:id` | Complemento de um dossiê com território, localização e vínculo pré-selecionados |
| `/entrar` e `/perfil` | Cadastro e sessão local ou Supabase, acompanhamento por protocolo, exportação e exclusão da conta |
| `/admin` | Revisão de fotos e referências, aprovação como problema novo ou relacionado, rejeição, esclarecimento, mudança de situação, restauração, unificação e auditoria |
| `/simulador` e `/simulador/:id` | Intervenções cadastradas, custos hipotéticos, comparação de duas estratégias e acesso ao cenário persistido |
| `/fontes`, `/metodologia`, `/sobre` e `/privacidade` | Proveniência, qualidade, explicação dos critérios e informações ao participante |

## Cartografia e acesso

O MapLibre combina a base raster do OpenStreetMap com os contornos municipais e de bairros fornecidos pela API. As camadas permitem consultar os problemas publicados e os equipamentos quando a geometria inclui pontos. A seleção de um marcador abre seu dossiê. Em dispositivos sem WebGL a interface traça os contornos oficiais em SVG. A lista e as coordenadas manuais continuam disponíveis. Referências de terceiros e a cobertura geográfica dependem das fontes carregadas.

A navegação móvel oferece cinco destinos. O menu secundário reúne simulador, fontes e demais páginas. O visual inclui foco de teclado, link para pular a navegação, diálogos nativos e suporte à preferência por movimento reduzido.

## Sessão e disponibilidade

A API recebe cookies same-origin no modo local e o token de acesso do SDK no modo Supabase. O backend fornece os perfis de teste apenas quando o modo local de desenvolvimento está habilitado. A distribuição JavaScript não contém as senhas desses perfis.

O build gera `sw.js` com uma lista fechada dos arquivos da versão. A instalação armazena a interface pública, os ícones e o manifesto. Solicitações de API, fotos, respostas de autenticação, terceiros e requisições com autorização passam diretamente à rede. A interface informa a falta de conexão. Consultas e envios requerem acesso ao servidor. O botão de instalação aparece nos navegadores que disponibilizam o evento de instalação.

## Validação

- TypeScript estrito e Vite 7.3.8 concluíram o build de produção. A rodada de referência transformou 2.229 módulos em 9,05 s.
- `npm test` executou quatro suítes e nove testes. Os casos cobrem formatação, dados ausentes, coordenadas, destino após login, vínculos no relato, estado vazio e exclusões do cache.
- A inspeção de `dist/sw.js` encontrou os 20 arquivos listados em disco e nenhuma rota da API. A busca na distribuição confirmou a ausência da senha de teste local.
- O teste de formulário usa a API simulada e verifica o corpo da submissão pendente. A aplicação em execução usa as rotas reais de `/api/v1`.

Em sandboxes Windows que bloqueiam a renomeação de arquivos no diretório temporário do sistema, atribua `TEMP` e `TMP` a uma pasta de trabalho gravável na sessão de testes. Isso permite que o Vitest escreva seus módulos temporários.
