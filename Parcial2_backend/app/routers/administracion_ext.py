"""Ampliaciones CU 06 a 08 que complementan las pantallas heredadas."""
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.database import get_db
from app.services.auth_service import requiere_rol

router=APIRouter(tags=['Administración de empresa'])
admin=requiere_rol(['Administrador'])

class RoleCreate(BaseModel):
    nombre:str=Field(min_length=2,max_length=50)
    descripcion:str=Field(default='',max_length=255)

class BranchAssignments(BaseModel):
    sucursales:list[int]=Field(max_length=100)

@router.post('/roles',status_code=201)
def create_role(data:RoleCreate,_=Depends(admin),cur=Depends(get_db)):
    cur.execute('SELECT 1 FROM rol WHERE nombre=%s',(data.nombre,))
    if cur.fetchone():raise HTTPException(409,'El rol ya existe en esta empresa.')
    cur.execute('INSERT INTO rol(nombre,descripcion) VALUES(%s,%s) RETURNING id_rol,nombre,descripcion',(data.nombre,data.descripcion));return cur.fetchone()

@router.put('/usuarios/{user_id}/sucursales')
def assign_branches(user_id:int,data:BranchAssignments,_=Depends(admin),cur=Depends(get_db)):
    if any(x<=0 for x in data.sucursales) or len(set(data.sucursales))!=len(data.sucursales):raise HTTPException(422,'Sucursales positivas y sin duplicados requeridas.')
    cur.execute('SELECT id_usuario FROM usuario WHERE id_usuario=%s FOR UPDATE',(user_id,))
    if not cur.fetchone():raise HTTPException(404,'Usuario no encontrado.')
    cur.execute('SELECT id_sucursal FROM sucursal WHERE id_sucursal=ANY(%s) AND activa',(data.sucursales,))
    if len(cur.fetchall())!=len(data.sucursales):raise HTTPException(404,'Una sucursal no está disponible en esta empresa.')
    cur.execute('DELETE FROM usuario_sucursal WHERE id_usuario=%s',(user_id,))
    for branch in data.sucursales:cur.execute('INSERT INTO usuario_sucursal(id_usuario,id_sucursal) VALUES(%s,%s)',(user_id,branch))
    return {'id_usuario':user_id,'sucursales':data.sucursales}

@router.patch('/sucursales/{branch_id}/estado')
def branch_state(branch_id:int,activa:bool,_=Depends(admin),cur=Depends(get_db)):
    cur.execute('UPDATE sucursal SET activa=%s WHERE id_sucursal=%s RETURNING id_sucursal,nombre,activa',(activa,branch_id));row=cur.fetchone()
    if not row:raise HTTPException(404,'Sucursal no encontrada.')
    return row
