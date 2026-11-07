"""Extract the application's own Python classifiers without importing the app."""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'tmp/class-model'


def code(n):
    return ast.unparse(n) if n is not None else ''


def visibility(name):
    return '-' if name.startswith('__') and not name.endswith('__') else '#' if name.startswith('_') and not name.startswith('__') else '+'


def inferred(n):
    if isinstance(n,ast.Constant):
        return '' if n.value is None else type(n.value).__name__
    if isinstance(n,(ast.List,ast.ListComp)):return 'list'
    if isinstance(n,(ast.Dict,ast.DictComp)):return 'dict'
    if isinstance(n,(ast.Set,ast.SetComp)):return 'set'
    if isinstance(n,ast.Tuple):return 'tuple'
    if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute)):
        name=code(n.func)
        return name if name.rsplit('.',1)[-1][:1].isupper() or name in ('list','dict','set','tuple','str','int','float','bool') else ''
    return ''


def operation(n,static=False):
    args=[]
    positional=n.args.posonlyargs+n.args.args
    default_count=len(n.args.defaults)
    for i,a in enumerate(positional):
        if a.arg in ('self','cls'):continue
        args.append({'name':a.arg,'type':code(a.annotation),'optional':i>=len(positional)-default_count})
    if n.args.vararg:args.append({'name':'*'+n.args.vararg.arg,'type':code(n.args.vararg.annotation)})
    for a,default in zip(n.args.kwonlyargs,n.args.kw_defaults):
        args.append({'name':a.arg,'type':code(a.annotation),'optional':default is not None})
    if n.args.kwarg:args.append({'name':'**'+n.args.kwarg.arg,'type':code(n.args.kwarg.annotation)})
    decorators=[code(d) for d in n.decorator_list]
    return {'name':n.name,'params':args,'return':code(n.returns),'line':n.lineno,
            'visibility':visibility(n.name),'static':static or 'staticmethod' in decorators or 'classmethod' in decorators,
            'kind':'getter' if 'property' in decorators else 'method','async':isinstance(n,ast.AsyncFunctionDef)}


def attributes(body):
    fields={}
    for n in body:
        if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name):
            fields[n.target.id]={'name':n.target.id,'type':code(n.annotation),'line':n.lineno,'static':False,'visibility':visibility(n.target.id)}
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name):
                    fields.setdefault(t.id,{'name':t.id,'type':inferred(n.value),'line':n.lineno,'static':True,'visibility':visibility(t.id)})
    for top in body:
        if not isinstance(top,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        for n in ast.walk(top):
            if not isinstance(n,(ast.Assign,ast.AnnAssign)):continue
            targets=n.targets if isinstance(n,ast.Assign) else [n.target]
            for t in targets:
                if isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self':
                    fields.setdefault(t.attr,{'name':t.attr,'type':code(n.annotation) if isinstance(n,ast.AnnAssign) else inferred(n.value),'line':n.lineno,'static':False,'visibility':visibility(t.attr)})
    return list(fields.values())


def main():
    nodes=[];files=[]
    paths=sorted((ROOT/'Parcial2_backend/app').rglob('*.py'))+[ROOT/'Parcial2_backend/ml/train.py']
    for p in paths:
        src=p.relative_to(ROOT).as_posix();files.append(src)
        tree=ast.parse(p.read_text(encoding='utf-8-sig'));imports=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom):
                imports.append({'path':n.module or '', 'level':n.level,'names':{a.asname or a.name:a.name for a in n.names}})
            elif isinstance(n,ast.Import):
                imports.extend({'path':a.name,'names':{a.asname or a.name:a.name}} for a in n.names)
        for n in tree.body:
            if isinstance(n,ast.ClassDef):
                nodes.append({'id':src+'::'+n.name,'name':n.name,'source':src,'line':n.lineno,'end':n.end_lineno,
                              'language':'Python','kind':'class','attributes':attributes(n.body),
                              'methods':[operation(m) for m in n.body if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef))],
                              'bases':[{'name':code(b),'kind':'extends'} for b in n.bases],'imports':imports})
        functions=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        if functions:
            nodes.append({'id':src+'::$module','name':p.name,'source':src,'line':1,'end':len(p.read_text(encoding='utf-8-sig').splitlines()),
                          'language':'Python','kind':'module','attributes':[dict(a,static=True) for a in attributes(tree.body)],'methods':[operation(n,True) for n in functions],
                          'bases':[],'imports':imports})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'python.json').write_text(json.dumps({'nodes':nodes,'refs':[],'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Python:',len(nodes),'classifiers;',sum(len(n['methods']) for n in nodes),'operations')


if __name__=='__main__':main()
