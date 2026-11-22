import path from 'node:path';
import {root, python, run} from './python.mjs';

// Keep the local demo database and its .env untouched.
process.loadEnvFile(path.join(root, 'work/supabase-production.env'));
process.env.APP_ENV = 'development';
const port = process.env.PORT || '8000';
process.env.PUBLIC_ORIGIN = 'http://127.0.0.1:' + port;
process.env.PYTHONPATH = [path.join(root, 'apps/api'), root].join(path.delimiter);
console.log('INVISIVEL + Supabase: ' + process.env.PUBLIC_ORIGIN + ' (autenticacao real; dados remotos)');
await run(python, ['-m', 'uvicorn', 'app.main:app', '--app-dir', 'apps/api', '--host', '127.0.0.1', '--port', port]);
