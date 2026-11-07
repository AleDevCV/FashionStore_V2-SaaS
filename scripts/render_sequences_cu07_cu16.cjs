const fs=require('node:fs'),path=require('node:path'),sharp=require('sharp');
const ROOT=path.resolve(__dirname,'..'),BASE=path.join(ROOT,'docs/diagramas_secuencia');
const reports=JSON.parse(fs.readFileSync(path.join(BASE,'MANIFIESTO_SECUENCIAS_CU07_CU16.json'),'utf8'));
(async()=>{
 for(let i=0;i<reports.length;i+=2){
  await Promise.all(reports.slice(i,i+2).map(async r=>{
   const stem=path.join(BASE,r.cu,r.cu+'_Diagrama_Secuencia');
   await sharp(stem+'.svg',{density:144,limitInputPixels:false}).withMetadata({density:300}).png().toFile(stem+'.png');
   await sharp(stem+'.svg',{limitInputPixels:false}).resize({width:1500}).png().toFile(path.join(ROOT,'tmp/secuencia-'+r.cu+'.png'));
   console.log(r.cu+': PNG y vista previa generados.');
  }));
 }
 const tiles=[];
 for(let i=0;i<reports.length;i++){
  const buffer=await sharp(path.join(ROOT,'tmp/secuencia-'+reports[i].cu+'.png')).resize({width:600,height:900,fit:'contain',background:'white'}).toBuffer();
  tiles.push({input:buffer,left:(i%3)*600,top:Math.floor(i/3)*900});
 }
 await sharp({create:{width:1800,height:2700,channels:3,background:'#e5e9eb'}}).composite(tiles).png().toFile(path.join(ROOT,'tmp/secuencias-contacto.png'));
})().catch(e=>{console.error(e);process.exitCode=1});
