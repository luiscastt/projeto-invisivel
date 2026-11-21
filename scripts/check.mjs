import {run,npm,python,root} from './python.mjs';
import path from 'node:path';
import fs from 'node:fs';
// Keep temporary compiler/test files inside the project, including on restricted Windows hosts.
const temp=path.join(root,'work/tmp'); fs.mkdirSync(temp,{recursive:true});
process.env.TMP=temp; process.env.TEMP=temp;
await run(python,['-m','pytest','-q','apps/api/tests','pipelines/tests']);
await npm(['test'],{cwd:path.join(root,'apps/web')});
await npm(['run','build'],{cwd:path.join(root,'apps/web')});
