/* Ejecutar contra Compose local; las credenciales se leen sin imprimirlas. */
const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');const env=Object.fromEntries(fs.readFileSync(path.join(root,'.env'),'utf8').split(/\r?\n/).filter(l=>l.includes('=')&&!l.startsWith('#')).map(l=>{const i=l.indexOf('=');return[l.slice(0,i),l.slice(i+1).replace(/^['"]|['"]$/g,'')];}));
const out=path.join(root,'docs/evidencias/offline-web');fs.mkdirSync(out,{recursive:true});
const wait=async(fn,message)=>{for(let i=0;i<60;i++){if(await fn())return;await new Promise(r=>setTimeout(r,500));}throw new Error(message);};
(async()=>{
 const profile=path.join(root,'tmp/browser-offline-'+Date.now());let browser=await chromium.launchPersistentContext(profile,{channel:'msedge',headless:true,viewport:{width:1440,height:1000}});
 try{
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error('Error de pÃ¡gina:',e.message);});
 page.on('console',m=>{if(m.type()==='error')console.error('Navegador:',m.text().replace(/eyJ[\w.-]+/g,'[token]'));});
 await page.goto('http://localhost:8082/login');
 await page.evaluate(()=>{localStorage.removeItem('fashionstore_p2_token');});await page.goto('http://localhost:8082/login');
 await page.locator('#correo').fill('atelierandino@fashionstore.com');await page.locator('#password').fill(env.DEMO_PASSWORD);
 await page.locator('button[type=submit]').click();await page.waitForURL('**/panel/**');
 await page.goto('http://localhost:8082/offline');await page.screenshot({path:path.join(out,'diagnostico.png'),fullPage:true});console.log('Sesión local:',await page.evaluate(()=>({active:localStorage.getItem('fashionstore_p2_active'),token:!!localStorage.getItem('fashionstore_p2_token')})));await page.locator('#offline-branch option').nth(1).waitFor({state:'attached'});await page.locator('#offline-branch').selectOption({index:1});
 await page.getByRole('button',{name:'Actualizar catÃ¡logo'}).click();await page.getByText('CatÃ¡logo guardado.',{exact:false}).waitFor();
 await page.evaluate(async()=>{await navigator.serviceWorker.ready;});await page.reload();
 await wait(()=>page.evaluate(()=>!!navigator.serviceWorker.controller),'Service Worker sin controlar pÃ¡gina');
 const count=await page.locator('.products article').count();assert(count>0,'CatÃ¡logo vacÃ­o');
 await browser.setOffline(true);await page.getByText('Sin conexiÃ³n',{exact:true}).waitFor();
 await page.locator('.products article input').first().fill('1');await page.getByLabel('Efectivo realmente recibido').fill('1000');
 await page.getByRole('button',{name:'Guardar en el dispositivo'}).click();await page.getByText(/Venta de contado Â· PENDIENTE/).first().waitFor();
 const uuid=await page.locator('.history .uuid').first().innerText();await page.screenshot({path:path.join(out,'01-venta-local.png'),fullPage:true});
 await browser.close();browser=await chromium.launchPersistentContext(profile,{channel:'msedge',headless:true,viewport:{width:1440,height:1000}});await browser.setOffline(true);const reopened=await browser.newPage();await reopened.goto('http://localhost:8082/offline');
 await reopened.getByText(uuid,{exact:true}).waitFor();assert((await reopened.locator('.products article').count())===count);
 await reopened.screenshot({path:path.join(out,'02-reapertura-sin-red.png'),fullPage:true});
 await browser.setOffline(false);await reopened.getByRole('button',{name:'Sincronizar ahora'}).click();
 await wait(async()=>{const row=reopened.locator('.history article').filter({hasText:uuid});return /CONFIRMADA/.test(await row.innerText());},'La operaciÃ³n no fue confirmada');
 const result=await reopened.evaluate(async id=>{const active=localStorage.getItem('fashionstore_p2_active');const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('fashionstore-p2-'+active);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});const op=await new Promise((resolve,reject)=>{const r=db.transaction('operations').objectStore('operations').get(id);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});db.close();return {id:op.operation_id,state:op.state,result:op.result};},uuid);
 await reopened.screenshot({path:path.join(out,'03-confirmacion-central.png'),fullPage:true});
 assert.equal(result.state,'CONFIRMADA');assert.equal(errors.length,0,errors.join('\n'));
 fs.writeFileSync(path.join(out,'resultado.json'),JSON.stringify({fecha:new Date().toISOString(),catalogo_variantes:count,reapertura_sin_red:true,reinicio_proceso_navegador:true,service_worker:true,...result},null,2));console.log('PWA: descarga, desconexiÃ³n, persistencia al reabrir y sincronizaciÃ³n confirmadas.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
