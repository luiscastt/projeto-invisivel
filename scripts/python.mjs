import {existsSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
export const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const python=path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
export function run(command,args,options={}) {
 return new Promise((resolve,reject)=>{
  const child=spawn(command,args,{cwd:root,stdio:'inherit',...options});
  child.once('error',reject);child.once('exit',code=>code===0?resolve():reject(new Error(`${command} saiu com código ${code}`)));
 });
}
export function npm(args,options={}) {
 return process.platform==='win32'?run('cmd.exe',['/d','/s','/c','npm.cmd',...args],options):run('npm',args,options);
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 process.env.PYTHONPATH=[path.join(root,'apps/api'),root,process.env.PYTHONPATH].filter(Boolean).join(path.delimiter);
 if(!existsSync(python)){console.error('Execute npm run setup primeiro.');process.exit(1)}
 await run(python,process.argv.slice(2)).catch(e=>{console.error(e.message);process.exitCode=1});
}
