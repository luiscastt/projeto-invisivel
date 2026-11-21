import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000}});
const page=await context.newPage(), errors=[];
page.on('pageerror',e=>errors.push(e.message));
const base=process.env.E2E_BASE_URL || 'http://127.0.0.1:8001';
async function visit(path){await page.goto(base+path);await page.locator('main').waitFor();}
async function signIn(admin=false){
 await visit('/entrar');await page.getByRole('button',{name:admin?'Moderação':'Cidadão',exact:true}).click();await page.getByRole('button',{name:'Entrar',exact:true}).click();await page.waitForURL(base+'/');
}
try{
 await visit('/');await page.getByText('520.653 pessoas',{exact:true}).first().waitFor();
 await page.locator('.map-canvas canvas').waitFor();
 assert((await page.locator('.map-canvas').boundingBox()).height>250,'MapLibre canvas must have a visible container');
 console.log('PASS dashboard + official indicators + map dimensions');
 await signIn(); await visit('/relatar');
 await page.getByLabel('Latitude',{exact:true}).fill('-20.2044');await page.getByLabel('Longitude',{exact:true}).fill('-40.2676');await page.getByRole('button',{name:'Continuar',exact:true}).click();
 const title='Verificação automatizada de iluminação '+Date.now();
 await page.getByLabel('Título',{exact:true}).fill(title);await page.getByLabel('Descrição',{exact:true}).fill('Relato de teste automatizado, isolado da base real: iluminação apagada na travessia próxima à praça.');await page.getByRole('button',{name:'Continuar',exact:true}).click();
 await page.getByRole('button',{name:'Continuar',exact:true}).click();await page.getByRole('button',{name:'Continuar',exact:true}).click();await page.getByRole('button',{name:'Enviar para moderação',exact:true}).click();await page.getByRole('heading',{name:'Relato recebido'}).waitFor();
 const privateList=await (await context.request.get(base+'/api/v1/issues')).json();assert.equal(privateList.total,0);
 console.log('PASS authenticated report wizard + pending privacy');
 await visit('/perfil');await page.getByRole('button',{name:'Sair',exact:true}).click();await signIn(true);await visit('/admin');
 await page.getByRole('heading',{name:title}).waitFor();await page.getByLabel('Justificativa (pública se o relato for aprovado)',{exact:true}).fill('Publicação revisada para teste automatizado em banco isolado.');await page.getByRole('button',{name:'Registrar decisão',exact:true}).click();
 await page.getByText('Fila de moderação em dia',{exact:true}).waitFor();
 const list=await(await context.request.get(base+'/api/v1/issues')).json();assert.equal(list.total,1);const issue=list.items[0];
 await visit('/problemas/'+issue.id);await page.getByRole('heading',{name:title}).waitFor();
 await page.getByRole('button',{name:/^Não resolvido/}).click();
 await page.getByRole('button',{name:/^Não resolvido/,pressed:true}).waitFor();
 await page.getByRole('button',{name:/^Resolvido/}).click();
 await page.getByRole('button',{name:/^Resolvido/,pressed:true}).waitFor();
 const changed=await(await context.request.get(base+'/api/v1/issues/'+issue.id)).json();assert.equal(changed.operational_status,'reported');assert.equal(changed.votes.unresolved,0);
 console.log('PASS moderation publication + vote replacement + independent verification');
 await visit('/simulador');await page.getByRole('button',{name:'Simular investimento',exact:true}).click();await page.getByRole('heading',{name:'Aplicação do orçamento',exact:true}).waitFor();assert.equal(await page.getByText('Problemas contemplados',{exact:true}).count(),2);
 console.log('PASS saved simulation + scenario comparison');
 for(const route of ['/explorar','/problemas','/fontes','/dados','/metodologia','/sobre','/privacidade','/perfil']){await visit(route);assert(!(await page.getByRole('heading',{name:'Algo não saiu como esperado'}).count()),route)}
 await visit('/dados');await page.getByRole('heading',{name:'Saúde · Serra',exact:true}).waitFor();await page.getByRole('tab',{name:'Educação',exact:true}).click();await page.getByRole('heading',{name:'Educação · Serra',exact:true}).waitFor();await page.getByRole('tab',{name:'Saneamento',exact:true}).click();await page.getByRole('heading',{name:'SINISA · Gestão Municipal',exact:true}).waitFor();await page.getByRole('tab',{name:'Ouvidoria',exact:true}).click();await page.getByRole('heading',{name:/^Ouvidoria estadual/}).waitFor();
 console.log('PASS official health, education, SINISA and ombudsman context tabs');
 await visit('/');await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:'work/mobile-final.png',fullPage:true});
 await page.setViewportSize({width:1440,height:1000});await page.screenshot({path:'work/desktop-final.png',fullPage:true});
 await page.evaluate(()=>navigator.serviceWorker.ready);await page.reload();await page.evaluate(()=>navigator.serviceWorker.ready);const cache=await page.evaluate(async()=>{let keys=[];for(const name of await caches.keys())for(const req of await(await caches.open(name)).keys())keys.push(new URL(req.url).pathname);return keys});assert(cache.length>10);assert(cache.every(p=>!p.startsWith('/api')));await context.setOffline(true);await page.reload();await page.getByText('INVISIVEL',{exact:true}).first().waitFor();await context.setOffline(false);
 assert.deepEqual(errors,[]);console.log('PASS mobile layout + public routes + offline PWA + no private cache + zero page errors');
}catch(e){await page.screenshot({path:'work/e2e-failure.png',fullPage:true});console.log('PAGE',await page.locator('body').innerText());throw e}
finally{await browser.close()}
