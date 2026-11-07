const fs=require('node:fs'),path=require('node:path'),sharp=require('sharp');
const ROOT=path.resolve(__dirname,'..'),OUT=path.join(ROOT,'docs/diagrama_clases');
(async()=>{
 const manifest=JSON.parse(fs.readFileSync(path.join(OUT,'MANIFIESTO_LAMINAS.json'),'utf8'));
 for(let i=0;i<manifest.laminas.length;i+=2){
  await Promise.all(manifest.laminas.slice(i,i+2).map(async plate=>{
   const stem=path.join(OUT,'laminas',plate.archivo);
   if(fs.existsSync(stem+'.png')&&fs.statSync(stem+'.png').mtimeMs>=fs.statSync(stem+'.svg').mtimeMs)return;
   await sharp(stem+'.svg',{density:72,limitInputPixels:false}).resize({width:2400}).withMetadata({density:300}).png().toFile(stem+'.png');
  }));
  if(i%20===0)console.log('PNG:',Math.min(i+2,manifest.laminas.length),'/',manifest.laminas.length);
 }
 const imgs=manifest.laminas.map(p=>'<img id="lamina-'+p.numero+'" src="laminas/'+p.archivo+'.svg" width="'+p.ancho+'" height="'+p.alto+'" loading="lazy" alt="Lámina '+p.numero+'">').join('');
 const html='<!doctype html><html lang="es"><meta charset="utf-8"><title>FashionStore · Clases UML acopladas</title><style>body{margin:0;background:#e7ebef;font-family:Arial}nav{position:sticky;top:0;padding:12px;background:#17384c;color:white;z-index:2}main{width:'+manifest.ancho+'px;background:white;margin:auto}img{display:block;margin:0;padding:0;border:0}select{font-size:16px;margin-left:16px}</style><nav>Diagrama de clases UML — '+manifest.laminas.length+' láminas continuas<select onchange="document.getElementById(this.value).scrollIntoView()">'+manifest.laminas.map(p=>'<option value="lamina-'+p.numero+'">'+p.numero+'</option>').join('')+'</select></nav><main>'+imgs+'</main></html>';
 fs.writeFileSync(path.join(OUT,'VISTA_ACOPLADA.html'),html);
 const checks=path.join(ROOT,'tmp/class-model/qa');fs.mkdirSync(checks,{recursive:true});
 for(const at of [0,8,30,60,manifest.laminas.length-2]){
  if(at<0||at+1>=manifest.laminas.length)continue;
  const a=manifest.laminas[at],b=manifest.laminas[at+1];
  const bottom=await sharp(path.join(OUT,'laminas',a.archivo+'.png')).extract({left:0,top:a.alto*2-180,width:2400,height:180}).toBuffer();
  const top=await sharp(path.join(OUT,'laminas',b.archivo+'.png')).extract({left:0,top:0,width:2400,height:180}).toBuffer();
  const combined=await sharp({create:{width:2400,height:360,channels:3,background:'white'}}).composite([{input:bottom,top:0,left:0},{input:top,top:180,left:0}]).png().toBuffer();
  await sharp(combined).resize({width:1600}).png().toFile(path.join(checks,'union-'+(at+1)+'.png'));
 }
 console.log('All PNG plates and aligned viewer generated.');
})().catch(e=>{console.error(e);process.exitCode=1;});
