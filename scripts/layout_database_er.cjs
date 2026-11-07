const fs=require('node:fs'),path=require('node:path');
const {instance}=require('@viz-js/viz');
const base=path.resolve(__dirname,'../docs/diagrama_entidad_relacion');
(async()=>{
 const viz=await instance();
 const dot=fs.readFileSync(path.join(base,'layout.dot'),'utf8');
 const result=viz.render(dot,{format:'json',engine:'dot'});
 if(result.status!=='success')throw Error(JSON.stringify(result.errors));
 fs.writeFileSync(path.join(base,'layout.json'),result.output);
 const obj=JSON.parse(result.output);
 console.log(JSON.stringify({bounds:obj.bb,nodes:obj.objects.filter(o=>o.pos).length,edges:obj.edges.length,warnings:result.errors}));
})().catch(e=>{console.error(e);process.exitCode=1});
