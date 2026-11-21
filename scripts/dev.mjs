import {existsSync} from 'node:fs';
import {spawn} from 'node:child_process';
import path from 'node:path';
import {root,python} from './python.mjs';
const built=process.argv.includes('--built');
if(!existsSync(python)){console.error('Execute npm run setup primeiro.');process.exit(1)}
if(built&&!existsSync(path.join(root,'apps/web/dist/index.html'))){console.error('Execute npm run build primeiro.');process.exit(1)}
const children=[];
function start(command,args,cwd=root){const child=spawn(command,args,{cwd,stdio:'inherit',windowsHide:true});children.push(child);child.on('error',e=>{console.error(e.message);stop(1)});child.on('exit',code=>{if(code)stop(code)});return child}
let stopping=false;
function stop(code=0){if(stopping)return;stopping=true;for(const c of children)c.kill('SIGTERM');setTimeout(()=>process.exit(code),250)}
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop());
start(python,['-m','uvicorn','app.main:app','--app-dir','apps/api','--host','127.0.0.1','--port','8000',...(built?[]:['--reload','--reload-dir','apps/api'])]);
if(!built){if(process.platform==='win32')start('cmd.exe',['/d','/s','/c','npm.cmd','run','dev'],path.join(root,'apps/web'));else start('npm',['run','dev'],path.join(root,'apps/web'))}
console.log(`\nINVISIVEL: http://127.0.0.1:${built?'8000':'5173'}\nAPI: http://127.0.0.1:8000/api/docs\nCtrl+C encerra os serviços.\n`);
