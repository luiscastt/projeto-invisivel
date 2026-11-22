import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {root} from './python.mjs';

const filename = path.join(root, 'work/supabase-production.env');
if (!fs.existsSync(path.join(root, '.vercel/project.json'))) throw Error('Vincule o projeto com vercel link antes de enviar as variaveis.');
process.loadEnvFile(filename);
const keys = ['APP_ENV','AUTH_PROVIDER','SEED_DEMO','DATABASE_URL','DATABASE_SCHEMA','SUPABASE_URL','SUPABASE_ANON_KEY','SUPABASE_SECRET_KEY','STORAGE_PROVIDER','SUPABASE_STORAGE_BUCKET','ADMIN_EMAILS'];
for (const key of keys) {
  const value = process.env[key];
  if (!value) throw Error('Variavel obrigatoria ausente: ' + key);
  const args = ['--yes','vercel@66.6.0','env','add',key,'--environment','production,preview','--sensitive','--force','--yes','--json'];
  await new Promise((resolve,reject) => {
    const cmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';
    const child = spawn(cmd,args,{cwd:root,stdio:['pipe','pipe','pipe'],shell:process.platform === 'win32',windowsHide:true});
    // Values travel only through stdin; never print returned payloads or keys.
    child.stdout.resume();child.stderr.resume();
    child.once('error',()=>reject(Error('Nao foi possivel executar a CLI Vercel.')));
    child.once('exit',code=>code===0?resolve():reject(Error('Falha ao configurar ' + key + '; confira login e projeto Vercel.')));
    child.stdin.on('error',()=>{});child.stdin.end(value);
  });
  console.log('Configurada: ' + key);
}
