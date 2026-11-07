const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const sharp=require('sharp');
const ROOT=path.resolve(__dirname,'..');
const OUT=path.join(ROOT,process.argv[2]||'docs/diagramas_robustez/CU06_Numerado');
const STEM=process.argv[3]||'CU06_Robustez_Numerada';
const model=JSON.parse(fs.readFileSync(path.join(OUT,STEM+'_Modelo.json'),'utf8'));
const template=fs.readFileSync(path.join(__dirname,'enterprise_architect_robustness_template.js'),'utf8');
const generated=template.replace('__CU06_MODEL__',JSON.stringify({nodes:model.nodes,messages:model.messages,views:model.views},null,2));
fs.writeFileSync(path.join(OUT,'JScript_Generar_Robustez_CU06.js'),'\uFEFF'+generated,'utf8');

function validateJScript(){
  // Exercise the complete artifact against a strict local substitute of the EA API.
  let id=1000;const connectors=[],diagrams=[],elements=[],sql=[],opened=[],writes=[];
  function collection(factory){const items=[];return {get Count(){return items.length},GetAt:n=>items[n],Refresh(){},AddNew(...args){const v=factory(...args);items.push(v);return v}}}
  function updateable(obj){obj.Update=()=>true;obj.GetLastError=()=>'';return obj}
  function element(name,type){const v=updateable({Name:name,Type:type,ElementID:id++});v.Connectors=collection((name,type)=>{const c=updateable({Name:name,Type:type,ClientID:v.ElementID,ConnectorID:id++});connectors.push(c);return c});elements.push(v);return v}
  function pkg(name){const p=updateable({Name:name,PackageID:id++});p.Packages=collection(pkg);p.Elements=collection(element);p.Diagrams=collection((name,type)=>{const d=updateable({Name:name,Type:type,DiagramID:id++});d.DiagramObjects=collection(()=>updateable({}));d.DiagramLinks=collection(()=>updateable({}));diagrams.push(d);return d});return p}
  const selected=pkg('Paquete de prueba');
  const context={Repository:{EnsureOutputVisible(){},GetTreeSelectedPackage(){return selected},Execute(q){sql.push(q);return true},ReloadDiagram(){},WriteOutput(...a){writes.push(a)},RefreshModelView(){},OpenDiagram(n){opened.push(n)}},Session:{Prompt(m){throw new Error(m)}}};
  vm.runInNewContext(generated,context,{timeout:10000});
  const messages=connectors.filter(c=>c.Type==='Collaboration');
  const expected=model.views.reduce((sum,v)=>sum+v.groups.reduce((n,g)=>n+g.rows.length,0),0);
  if(messages.length!==expected)throw Error('Cantidad EA de mensajes incorrecta');
  if(diagrams.length!==model.views.length||opened.length!==1)throw Error('Vistas EA incompletas');
  const nodeByElement=new Map(elements.map(e=>[e.ElementID,e]));
  for(let vi=0;vi<diagrams.length;vi++){
    const actual=messages.filter(m=>m.DiagramID===diagrams[vi].DiagramID);
    const wanted=model.views[vi].groups.flatMap(g=>g.rows.map(r=>r.n)).sort((a,b)=>a-b);
    if(JSON.stringify(actual.map(m=>m.SequenceNo).sort((a,b)=>a-b))!==JSON.stringify(wanted))throw Error('Numeración EA divergente');
    for(const connector of actual){
      const m=model.messages[connector.SequenceNo-1];
      const reverse=connector.Direction==='Destination -> Source';
      const from=nodeByElement.get(reverse?connector.SupplierID:connector.ClientID);
      const to=nodeByElement.get(reverse?connector.ClientID:connector.SupplierID);
      if(from.Name!==model.nodes[m.a].name||to.Name!==model.nodes[m.b].name)throw Error('Dirección EA invertida en '+m.n);
      if(connector.Name!==m.text)throw Error('Texto EA divergente');
      const query=sql.find(s=>s.endsWith('Connector_ID='+connector.ConnectorID));
      if(!query||!query.includes("PDATA4='"+m.n+"'"))throw Error('Número explícito EA ausente');
    }
  }
  const report={sintaxis_jscript_validada:true,generacion_simulada_completa:true,diagramas:diagrams.length,mensajes_creados_incluyendo_vistas:messages.length,direcciones_verificadas:true,textos_y_numeracion_coinciden_con_drawio:true,ejecucion_en_Enterprise_Architect_real:false};
  fs.writeFileSync(path.join(OUT,'VALIDACION_JSCRIPT.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
}

(async()=>{
 validateJScript();
 const variants=model.exports||['General','Categorias','Temporadas','Prendas'];
 for(const name of variants){
   const base=path.join(OUT,STEM+'_'+name);
   await sharp(base+'.svg',{density:72,limitInputPixels:false}).withMetadata({density:300}).png().toFile(base+'.png');
   await sharp(base+'.svg',{density:72,limitInputPixels:false}).resize({width:1800}).png().toFile(path.join(ROOT,'tmp/CU06_'+name+'_numerado_preview.png'));
 }
 console.log('Draw.io, JScript y '+variants.length+' vista(s) PNG listos.');
})().catch(e=>{console.error(e);process.exitCode=1});
