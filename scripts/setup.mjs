import fs from 'node:fs/promises';
import {existsSync} from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {root,run,npm} from './python.mjs';

// Portable Python is isolated inside ignored work/, never installed machine-wide.
const runtime=path.join(root,'work/runtime');
await fs.mkdir(runtime,{recursive:true});
const win=process.platform==='win32';
const target=win?'x86_64-pc-windows-msvc':process.platform==='darwin'?(process.arch==='arm64'?'aarch64-apple-darwin':'x86_64-apple-darwin'):(process.arch==='arm64'?'aarch64-unknown-linux-gnu':'x86_64-unknown-linux-gnu');
const uvPath=path.join(runtime,'uv',win?'uv.exe':`uv-${target}/uv`);
const env={...process.env,UV_CACHE_DIR:path.join(runtime,'cache'),UV_PYTHON_INSTALL_DIR:path.join(runtime,'python'),UV_PYTHON_BIN_DIR:path.join(runtime,'bin'),UV_LINK_MODE:'copy',UV_NO_MODIFY_PATH:'1'};
try{
 if(!existsSync(uvPath)){
  console.log('Preparando uv e Python portáteis…');
  const release=await fetch('https://api.github.com/repos/astral-sh/uv/releases/latest',{headers:{'User-Agent':'invisivel-setup'}});
  if(!release.ok)throw Error('Não foi possível consultar a versão oficial do uv.');
  const data=await release.json();
  const asset=data.assets.find(a=>a.name===`uv-${target}.${win?'zip':'tar.gz'}`);
  if(!asset)throw Error('Plataforma não suportada pelo instalador. Instale uv e execute uv sync --frozen.');
  const response=await fetch(asset.browser_download_url);
  if(!response.ok)throw Error('Falha ao baixar uv.');
  const bytes=Buffer.from(await response.arrayBuffer());
  const checksum=crypto.createHash('sha256').update(bytes).digest('hex');
  if(!asset.digest||asset.digest!==`sha256:${checksum}`)throw Error('A verificação SHA256 do uv falhou.');
  const archive=path.join(runtime,win?'uv.zip':'uv.tar.gz');
  await fs.writeFile(archive,bytes);await fs.mkdir(path.join(runtime,'uv'),{recursive:true});
  if(win)await run('powershell.exe',['-NoProfile','-NonInteractive','-Command',`Expand-Archive -LiteralPath '${archive.replaceAll("'","''")}' -DestinationPath '${path.join(runtime,'uv').replaceAll("'","''")}' -Force`]);
  else await run('tar',['-xzf',archive,'-C',path.join(runtime,'uv')]);
 }
 await run(uvPath,['sync','--frozen'],{env});
 await npm(['ci','--no-audit','--no-fund']);
 await npm(['ci','--no-audit','--no-fund'],{cwd:path.join(root,'apps/web')});
 await npm(['run','build'],{cwd:path.join(root,'apps/web')});
 console.log('\nPronto. Execute npm run dev. Os dados oficiais já estão incluídos; npm run sync:data atualiza o cache.');
}catch(e){console.error(e.message);process.exitCode=1}
