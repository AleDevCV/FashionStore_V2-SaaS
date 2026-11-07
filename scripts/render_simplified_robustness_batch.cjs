const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const sharp=require('sharp');
const ROOT=path.resolve(__dirname,'..');
const BASE=path.join(ROOT,'docs/diagramas_robustez');
const manifest=JSON.parse(fs.readFileSync(path.join(BASE,'MANIFIESTO_CU07_CU16_SIMPLIFICADOS.json'),'utf8'));
const template=fs.readFileSync(path.join(__dirname,'enterprise_architect_robustness_template.js'),'utf8');

function validate(code,model){
 let id=1000;const elements=[],connectors=[],diagrams=[],queries=[];
 function collection(factory){const values=[];return {get Count(){return values.length},GetAt:i=>values[i],Refresh(){},AddNew(...a){const x=factory(...a);values.push(x);return x}}}
 function upd(x){x.Update=()=>true;x.GetLastError=()=>'';return x}
 function elem(name,type){const x=upd({Name:name,Type:type,ElementID:id++});x.Connectors=collection((name,type)=>{const c=upd({Name:name,Type:type,ClientID:x.ElementID,ConnectorID:id++});connectors.push(c);return c});elements.push(x);return x}
 function pkg(name){const x=upd({Name:name,PackageID:id++});x.Packages=collection(pkg);x.Elements=collection(elem);x.Diagrams=collection((name,type)=>{const d=upd({Name:name,Type:type,DiagramID:id++});d.DiagramObjects=collection(()=>upd({}));d.DiagramLinks=collection(()=>upd({}));diagrams.push(d);return d});return x}
 const parent=pkg('Destino de prueba');
 vm.runInNewContext(code,{Repository:{GetTreeSelectedPackage:()=>parent,EnsureOutputVisible(){},WriteOutput(){},Execute(q){queries.push(q);return true},ReloadDiagram(){},RefreshModelView(){},OpenDiagram(){}},Session:{Prompt(m){throw Error(m)}}},{timeout:10000});
 const ms=connectors.filter(c=>c.Type==='Collaboration');
 if(diagrams.length!==1||ms.length!==model.messages.length)throw Error(model.case+': generación incompleta');
 const byElement=new Map(elements.map(e=>[e.ElementID,e]));
 for(const c of ms){
  const m=model.messages[c.SequenceNo-1];
  if(!m||c.Name!==m.text)throw Error('Número o texto divergente');
  const reverse=c.Direction==='Destination -> Source';
  const a=byElement.get(reverse?c.SupplierID:c.ClientID),b=byElement.get(reverse?c.ClientID:c.SupplierID);
  if(a.Name!==model.nodes[m.a].name||b.Name!==model.nodes[m.b].name)throw Error('Flecha EA invertida: '+model.case+' '+m.n);
  const q=queries.find(q=>q.endsWith('Connector_ID='+c.ConnectorID));
  if(!q||!q.includes("PDATA4='"+m.n+"'"))throw Error('Número explícito no conservado');
 }
 return {sintaxis_y_generacion_simulada:true,diagramas:1,mensajes:ms.length,textos_numeros_y_sentidos_coinciden:true,ejecucion_real_en_EA:false};
}

async function generate(entry){
 const dir=path.join(ROOT,entry.folder),stem=path.join(dir,entry.stem);
 const model=JSON.parse(fs.readFileSync(stem+'_Modelo.json','utf8'));
 const code=template.replace(/CU06/g,entry.caso).replace('__'+entry.caso+'_MODEL__',()=>JSON.stringify({nodes:model.nodes,messages:model.messages,views:model.views},null,2));
 fs.writeFileSync(path.join(dir,'JScript_Generar_Robustez_'+entry.caso+'.js'),'\uFEFF'+code,'utf8');
 const report=validate(code,model);
 fs.writeFileSync(path.join(dir,'VALIDACION_JSCRIPT.json'),JSON.stringify(report,null,2));
 await sharp(stem+'_General.svg',{limitInputPixels:false}).withMetadata({density:300}).png().toFile(stem+'_General.png');
 await sharp(stem+'_General.svg',{limitInputPixels:false}).resize({width:1800}).png().toFile(path.join(ROOT,'tmp/robustez-'+entry.caso+'.png'));
 console.log(entry.caso+': JScript validado; PNG y vista previa generados.');
}

(async()=>{
 for(let i=0;i<manifest.length;i+=2)await Promise.all(manifest.slice(i,i+2).map(generate));
 const thumbnails=[];
 for(let i=0;i<manifest.length;i++){
  const e=manifest[i];
  const input=await sharp(path.join(ROOT,'tmp/robustez-'+e.caso+'.png')).resize({width:600,height:440,fit:'contain',background:'white'}).toBuffer();
  thumbnails.push({input,left:(i%3)*600,top:Math.floor(i/3)*440});
 }
 await sharp({create:{width:1800,height:1320,channels:3,background:'#dce1e5'}}).composite(thumbnails).png().toFile(path.join(ROOT,'tmp/robustez-contacto.png'));
})().catch(e=>{console.error(e);process.exitCode=1});
