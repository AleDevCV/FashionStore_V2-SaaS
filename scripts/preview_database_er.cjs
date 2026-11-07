const path=require('node:path'),sharp=require('sharp');
const root=path.resolve(__dirname,'..');
const stem=path.join(root,'docs/diagrama_entidad_relacion/FashionStore_Diagrama_Entidad_Relacion_General');
(async()=>{
 await sharp(stem+'.svg',{density:144,limitInputPixels:false}).withMetadata({density:300}).png().toFile(stem+'.png');
 await sharp(stem+'.svg').resize({width:1900}).png().toFile(path.join(root,'tmp/er-general-preview.png'));
 await sharp(stem+'.svg').extract({left:40,top:930,width:1600,height:1100}).png().toFile(path.join(root,'tmp/er-general-detail.png'));
 console.log('PNG y vistas previas generados.');
})().catch(e=>{console.error(e);process.exitCode=1});
