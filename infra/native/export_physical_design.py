"""Read-only schema export of P2 plus restoration in a disposable empty database."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,pwd,re,subprocess,uuid,urllib.request

ROOT=Path('/home/alecv/Parcial2_FashionStore')
DB='fashionstore_p2'
TAG='20261101_'+uuid.uuid4().hex[:8]
TARGET='fashionstore_p2_schema_check_'+TAG
OUT=ROOT/'schema-exports'/TAG
OUT.mkdir(parents=True,mode=0o700,exist_ok=False)
ENV=dict(os.environ,PGOPTIONS='-c statement_timeout=60000 -c lock_timeout=5000')

def run(args,**kw):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV,**kw)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8','replace')[:2500])
    return r.stdout

def psql(db,sql):
    return run(['runuser','-u','postgres','--','psql','-X','-qAt','--set=ON_ERROR_STOP=1','--dbname',db],input=sql.encode()).decode().strip()

def rows(db,sql):return json.loads(psql(db,'SELECT COALESCE(jsonb_agg(to_jsonb(t)),\'[]\'::jsonb) FROM ('+sql+') t;'))

NS="n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'"
def inventory(db):
    return {
      'schemas':rows(db,f"SELECT n.nspname,pg_get_userbyid(n.nspowner) AS owner FROM pg_namespace n WHERE {NS} ORDER BY 1"),
      'relations':rows(db,f"SELECT n.nspname AS schema,c.relname,c.relkind,c.relrowsecurity,c.relforcerowsecurity,pg_get_userbyid(c.relowner) AS owner,ARRAY(SELECT x::text FROM unnest(COALESCE(c.relacl,acldefault(CASE WHEN c.relkind='S' THEN 's'::\"char\" ELSE 'r'::\"char\" END,c.relowner))) x ORDER BY 1) AS acl FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE {NS} AND c.relkind IN ('r','p','v','m','S','f') ORDER BY 1,2"),
      'columns':rows(db,f"SELECT n.nspname AS schema,c.relname,a.attnum,a.attname,format_type(a.atttypid,a.atttypmod) AS type,a.attnotnull,pg_get_expr(d.adbin,d.adrelid) AS default_expr,a.attidentity,a.attgenerated FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum WHERE {NS} AND c.relkind IN ('r','p','v','m') AND a.attnum>0 AND NOT a.attisdropped ORDER BY 1,2,3"),
      'constraints':rows(db,f"SELECT n.nspname AS schema,c.relname,k.conname,k.contype,pg_get_constraintdef(k.oid,true) AS definition,k.condeferrable,k.condeferred,k.convalidated FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE {NS} ORDER BY 1,2,3"),
      'indexes':rows(db,f"SELECT n.nspname AS schema,c.relname AS table_name,i.relname,pg_get_indexdef(i.oid) AS definition,x.indisvalid FROM pg_index x JOIN pg_class c ON c.oid=x.indrelid JOIN pg_class i ON i.oid=x.indexrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE {NS} ORDER BY 1,2,3"),
      'functions':rows(db,f"SELECT n.nspname AS schema,p.proname,pg_get_function_identity_arguments(p.oid) AS args,pg_get_function_result(p.oid) AS result,p.prosecdef,p.provolatile,p.proconfig,pg_get_userbyid(p.proowner) AS owner,md5(pg_get_functiondef(p.oid)) AS definition_md5,ARRAY(SELECT x::text FROM unnest(COALESCE(p.proacl,acldefault('f',p.proowner))) x ORDER BY 1) AS acl FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE {NS} AND p.prokind IN ('f','p','w') ORDER BY 1,2,3"),
      'triggers':rows(db,f"SELECT n.nspname AS schema,c.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid,true) AS definition FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE {NS} AND NOT t.tgisinternal ORDER BY 1,2,3"),
      'policies':rows(db,f"SELECT n.nspname AS schema,c.relname,p.polname,p.polcmd,p.polpermissive,ARRAY(SELECT CASE WHEN r=0 THEN 'public' ELSE pg_get_userbyid(r) END FROM unnest(p.polroles) r ORDER BY 1) AS roles,pg_get_expr(p.polqual,p.polrelid) AS using_expr,pg_get_expr(p.polwithcheck,p.polrelid) AS check_expr FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE {NS} ORDER BY 1,2,3"),
      'views':rows(db,f"SELECT n.nspname AS schema,c.relname,pg_get_viewdef(c.oid,true) AS definition,c.reloptions FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE {NS} AND c.relkind IN ('v','m') ORDER BY 1,2"),
      'sequences':rows(db,f"SELECT n.nspname AS schema,c.relname,s.seqstart,s.seqincrement,s.seqmax,s.seqmin,s.seqcache,s.seqcycle FROM pg_sequence s JOIN pg_class c ON c.oid=s.seqrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE {NS} ORDER BY 1,2"),
      'enums':rows(db,f"SELECT n.nspname AS schema,t.typname,pg_get_userbyid(t.typowner) AS owner,array_agg(e.enumlabel ORDER BY e.enumsortorder) AS labels FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace JOIN pg_enum e ON e.enumtypid=t.oid WHERE {NS} GROUP BY n.nspname,t.typname,t.typowner ORDER BY 1,2"),
      'extensions':rows(db,"SELECT extname,extversion FROM pg_extension ORDER BY 1"),
    }

def health():
    result={}
    for name in ['fashionstore-p2-api','fashionstore-p2-tunnel','nginx','postgresql','cloudflared','tailscaled']:
        r=subprocess.run(['systemctl','show',name,'--property=ActiveState,SubState,NRestarts,MemoryCurrent,ExecMainStatus'],capture_output=True,text=True)
        result[name]=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
    for key,url in [('api','http://127.0.0.1:8002/health'),('web_proxy','http://127.0.0.1:2468/health'),('login','http://127.0.0.1:2468/login'),('pwa','http://127.0.0.1:2468/ngsw.json'),('tunnel','http://127.0.0.1:20245/ready')]:
        try:
            with urllib.request.urlopen(url,timeout=15) as response:
                result[key]={'status':response.status}
                if key in ('api','web_proxy'):result[key]['body']=response.read(1000).decode()
        except Exception as exc:result[key]={'error':str(exc)}
    result['database']=psql(DB,'SELECT 1;')=='1'
    return result

def literal(value):return "'"+value.replace("'","''")+"'"
def ident(value):return '"'+value.replace('"','""')+'"'

def compare_schema(source, restored, target):
    comparison={key:source[key]==restored[key] for key in source}
    reparsed_checks=[]
    # PostgreSQL may move a text[] cast onto each varchar array literal when
    # reparsing a CHECK. Compare those definitions with PostgreSQL's own parser,
    # in temporary tables in the disposable database, rather than rewriting SQL.
    if not comparison['constraints'] and len(source['constraints'])==len(restored['constraints']):
        valid=True
        for original, actual in zip(source['constraints'],restored['constraints']):
            if original==actual:continue
            metadata=lambda item:{k:v for k,v in item.items() if k!='definition'}
            if original['contype']!='c' or metadata(original)!=metadata(actual):
                valid=False;break
            sql=('BEGIN; CREATE TEMP TABLE physical_design_check (LIKE '+
                 ident(original['schema'])+'.'+ident(original['relname'])+
                 ' EXCLUDING ALL); ALTER TABLE pg_temp.physical_design_check ADD CONSTRAINT checked '+
                 original['definition']+'; SELECT pg_get_constraintdef(oid,true) FROM pg_constraint '+
                 "WHERE conrelid='pg_temp.physical_design_check'::regclass AND conname='checked'; ROLLBACK;")
            canonical=psql(target,sql)
            if canonical!=actual['definition']:
                valid=False;break
            reparsed_checks.append(dict(schema=original['schema'],table=original['relname'],
                constraint=original['conname'],source_definition=original['definition'],
                restored_definition=actual['definition'],postgresql_reparse_matches=True))
        comparison['constraints']=valid
    return comparison,reparsed_checks

before=health()
source=inventory(DB)
assert psql(DB,'SELECT count(*) FROM pg_user_mapping;')=='0','Revisar posibles credenciales en mapeos externos.'
raw=run(['runuser','-u','postgres','--','pg_dump','--schema-only','--lock-wait-timeout=5000','--dbname',DB]).decode('utf-8')
assert not re.search(r'(?m)^(COPY .* FROM stdin;|INSERT INTO )',raw),'La exportación contiene datos.'
assert not re.search(r'(?i)(sk_(?:test|live)_[A-Za-z0-9]{12,}|AIza[A-Za-z0-9_-]{25,}|BEGIN [A-Z ]*PRIVATE KEY|PASSWORD\s+\'(?!\'))',raw),'Revisar posibles secretos en definiciones.'
# Remove psql restriction metacommands so the delivered design is ordinary SQL.
ddl='\n'.join(line for line in raw.splitlines() if not line.startswith(('\\restrict ','\\unrestrict ')))+'\n'
assert not re.search(r'^\\',ddl,re.M),'Metacomando psql no previsto.'
roles=rows(DB,"SELECT rolname,rolsuper,rolcreaterole,rolcreatedb,rolcanlogin,rolreplication,rolbypassrls FROM pg_roles WHERE rolname LIKE 'fashionstore%' ORDER BY 1")
role_sql='-- Roles de propiedad y autorización; sin contraseñas. No altera roles existentes.\n'
for role in roles:
    assert not any(role[k] for k in ['rolsuper','rolcreaterole','rolcreatedb','rolreplication','rolbypassrls']),role['rolname']
    name=role['rolname']
    role_sql+="DO $roles$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname="+literal(name)+") THEN CREATE ROLE "+ident(name)+" NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; END IF; END $roles$;\n"
header='-- FASHIONSTORE: DISENO FISICO COMPLETO\n-- Fuente: PostgreSQL 17 del servidor P2. Solo estructura, sin filas ni credenciales.\n-- Aplicar conectado a una BASE VACIA, como administrador PostgreSQL.\n-- No contiene CREATE DATABASE, DROP DATABASE ni DROP TABLE para reemplazar una instalación.\n\n'
full=header+'BEGIN;\n'+role_sql+'\n'+ddl+'\nCOMMIT;\n'
path=OUT/'FASHIONSTORE_DISENO_FISICO_COMPLETO.sql'
path.write_text(full,encoding='utf-8')
(OUT/'00_ROLES_SIN_CREDENCIALES.sql').write_text(role_sql,encoding='utf-8')
(OUT/'01_CREAR_BASE_VACIA.sql').write_text("-- Ejecutar una sola vez conectado a postgres, fuera de una transacción.\nCREATE DATABASE fashionstore_diseno_fisico WITH TEMPLATE template0 OWNER fashionstore_p2_owner ENCODING 'UTF8';\n",encoding='utf-8')
(OUT/'INVENTARIO_ORIGEN.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
created=False
comparison={}
try:
    assert re.fullmatch(r'fashionstore_p2_schema_check_20261101_[0-9a-f]{8}',TARGET)
    assert TARGET!=DB
    run(['runuser','-u','postgres','--','createdb','--template=template0','--owner=fashionstore_p2_owner',TARGET]);created=True
    psql('postgres','REVOKE ALL ON DATABASE '+ident(TARGET)+' FROM PUBLIC;')
    # Exact delivered file, one transaction, only in the fresh isolated database.
    psql(TARGET,full)
    restored=inventory(TARGET)
    comparison,reparsed_checks=compare_schema(source,restored,TARGET)
    (OUT/'INVENTARIO_RESTAURADO.json').write_text(json.dumps(restored,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'DIFERENCIAS.json').write_text(json.dumps({k:{'source':source[k],'restored':restored[k]} for k,v in comparison.items() if not v},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'CHECKS_REINTERPRETADOS.json').write_text(json.dumps(reparsed_checks,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(comparison.values()),'Diferencias de estructura: '+', '.join(k for k,v in comparison.items() if not v)
finally:
    if created:
        assert TARGET.startswith('fashionstore_p2_schema_check_20261101_') and TARGET!=DB
        run(['runuser','-u','postgres','--','dropdb',TARGET])
after=health()
summary={k:len(v) for k,v in source.items()}
summary['tables']=sum(r['relkind'] in ['r','p'] for r in source['relations'])
summary['primary_keys']=sum(c['contype']=='p' for c in source['constraints'])
summary['foreign_keys']=sum(c['contype']=='f' for c in source['constraints'])
summary['rls_tables']=sum(r['relrowsecurity'] for r in source['relations'])
report=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),database=DB,server_version=psql(DB,'SHOW server_version;'),
            sql_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),summary=summary,comparison=comparison,
            restore_database=TARGET,restore_success=True,test_database_removed=True,schema_only=True,
            production_data_modified=False,service_restarts_requested=False,health_before=before,health_after=after,
            check_definitions_reparsed_by_postgresql=len(reparsed_checks),
            role_authentication='Los roles ausentes se crean NOLOGIN, sin contraseñas. La autenticación de despliegue se configura por separado.')
(OUT/'VALIDACION_DISENO_FISICO.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
account=pwd.getpwnam('alecv')
for file in OUT.iterdir():
    os.chown(file,account.pw_uid,account.pw_gid);file.chmod(0o600)
os.chown(OUT,account.pw_uid,account.pw_gid);OUT.chmod(0o700)
print(json.dumps(dict(directory=str(OUT),summary=summary,restore_success=True,test_database_removed=True,comparison=comparison,health_after=after),ensure_ascii=False))
