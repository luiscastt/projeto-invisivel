import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import net from 'node:net';
import {root,python,run} from './python.mjs';
const work=path.join(root,'work');await fs.mkdir(work,{recursive:true});
const testDir=await fs.mkdtemp(path.join(work,'browser-'));
const port=await new Promise(resolve=>{const server=net.createServer();server.listen(0,'127.0.0.1',()=>{const value=server.address().port;server.close(()=>resolve(value))})});
const base=`http://127.0.0.1:${port}`;
const env={...process.env,APP_ENV:'development',AUTH_PROVIDER:'local',SEED_DEMO:'true',DATABASE_URL:`sqlite:///${path.join(testDir,'browser.db').replaceAll('\\','/')}`,DATA_DIR:testDir,PUBLIC_ORIGIN:base,E2E_BASE_URL:base,TEMP:testDir,TMP:testDir,PLAYWRIGHT_BROWSERS_PATH:process.env.PLAYWRIGHT_BROWSERS_PATH||path.join(work,'browsers')};
await run(process.execPath,[path.join(root,'node_modules/playwright/cli.js'),'install','chromium'],{env});
const server=spawn(python,['-u','-m','uvicorn','app.main:app','--app-dir','apps/api','--host','127.0.0.1','--port',String(port)],{cwd:root,env,stdio:['ignore','pipe','pipe'],windowsHide:true});
let log='';server.stdout.on('data',b=>log+=b);server.stderr.on('data',b=>log+=b);
try{
 let ready=false;for(let i=0;i<100;i++){try{if((await fetch(base+'/api/v1/health')).ok){ready=true;break}}catch{}await new Promise(r=>setTimeout(r,300))}
 if(!ready)throw Error('API de teste não iniciou: '+log);
 await run(process.execPath,['tests/e2e.mjs'],{env});
}finally{server.kill('SIGTERM');await fs.writeFile(path.join(testDir,'server.log'),log);console.log('Banco e logs de teste isolados em',testDir)}
