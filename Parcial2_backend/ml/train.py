"""Entrenamiento local reproducible. No se conecta a PostgreSQL ni usa datos comerciales."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from pathlib import Path
import csv,json,hashlib,sys,math
from datetime import date,timedelta,datetime,timezone
import numpy as np
import sklearn,joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error,root_mean_squared_error,silhouette_score
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.ml_features import FEATURES,demand_features
SEED=262026

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dataset(directory):
    directory.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(SEED);records=[];X=[];y=[];dates=[];baseline=[]
    start=date(2025,1,1)
    for product in range(12):
        price=round(float(rng.uniform(50,300)),2)
        for branch in range(2):
            level=float(rng.uniform(1,9));history=[]
            for day in range(420):
                stamp=start+timedelta(days=day);offer=(day//14+product)%5==0
                weekly=1+.48*math.sin(2*math.pi*stamp.weekday()/7)
                seasonal=1+.17*math.cos(2*math.pi*(stamp.month-1)/12)
                demand=int(rng.poisson(max(.1,level*weekly*seasonal*(1.3 if offer else 1)*(1+day/2100))))
                records.append([stamp.isoformat(),f'SYNTH-{product:02}',f'SYNTH-B{branch}',price,int(offer),demand,'sintetico'])
                if len(history)>=28:X.append(demand_features(history,stamp,price,offer));y.append(demand);dates.append(day);baseline.append(float(np.mean(history[-7:])))
                history.append(demand)
    path=directory/'demanda_sintetica.csv'
    with path.open('w',newline='',encoding='utf-8') as f:writer=csv.writer(f);writer.writerow(['fecha','producto_sintetico','sucursal_sintetica','precio','oferta','unidades','origen']);writer.writerows(records)
    return np.array(X),np.array(y),np.array(dates),np.array(baseline),path

def train():
    output=ROOT/'ml/artifacts/v1';output.mkdir(parents=True,exist_ok=True)
    X,y,days,baseline,demand_path=dataset(ROOT/'ml/datasets')
    training=days<294;validation=(days>=294)&(days<357);test=days>=357
    candidates=[]
    with threadpool_limits(limits=1):
        for leaves in (15,31):
            model=HistGradientBoostingRegressor(loss='poisson',max_iter=120,max_leaf_nodes=leaves,learning_rate=.07,l2_regularization=1,early_stopping=False,random_state=SEED)
            model.fit(X[training],y[training]);mae=float(mean_absolute_error(y[validation],model.predict(X[validation])));candidates.append((mae,leaves))
        best=min(candidates)[1];model=HistGradientBoostingRegressor(loss='poisson',max_iter=120,max_leaf_nodes=best,learning_rate=.07,l2_regularization=1,early_stopping=False,random_state=SEED)
        model.fit(X[~test],y[~test]);prediction=model.predict(X[test])
        metrics={'MAE':float(mean_absolute_error(y[test],prediction)),'RMSE':float(root_mean_squared_error(y[test],prediction)),'baseline_MAE':float(mean_absolute_error(y[test],baseline[test])),'baseline_RMSE':float(root_mean_squared_error(y[test],baseline[test]))}
        rng=np.random.default_rng(SEED+1);rfm=np.column_stack([rng.integers(1,365,600),rng.lognormal(1.8,.9,600).clip(1,150).round(),rng.lognormal(7.5,1,600).clip(20,80000)])
        pipeline=make_pipeline(StandardScaler(),KMeans(n_clusters=3,n_init=20,random_state=SEED));log_rfm=np.log1p(rfm);labels=pipeline.fit_predict(log_rfm)
        scores={int(k):float(np.mean(rfm[labels==k,1])*np.mean(rfm[labels==k,2])/(1+np.mean(rfm[labels==k,0]))) for k in range(3)}
        ordered=sorted(scores,key=scores.get);names={ordered[0]:'Ocasionales',ordered[1]:'Habituales',ordered[2]:'Mayor actividad'}
        silhouette=float(silhouette_score(pipeline[0].transform(log_rfm),labels))
    rfm_path=ROOT/'ml/datasets/rfm_sintetico.csv'
    with rfm_path.open('w',newline='',encoding='utf-8') as f:writer=csv.writer(f);writer.writerow(['recencia_dias','frecuencia','monetario','origen']);writer.writerows([*row,'sintetico'] for row in rfm)
    joblib.dump({'model':model,'features':FEATURES},output/'demand.joblib',compress=3)
    joblib.dump({'model':pipeline,'labels':names},output/'segments.joblib',compress=3)
    metadata={'version':'v1','seed':SEED,'trained_at':datetime.now(timezone.utc).isoformat(),'sklearn':sklearn.__version__,'numpy':np.__version__,'joblib':joblib.__version__,'source':'Exclusivamente datos sintéticos reproducibles; sin información de clientes reales.','features':FEATURES,'horizon':'Un día; unidades por producto y sucursal','minimum_history_days':28,'split':{'training_days':[28,293],'validation_days':[294,356],'test_days':[357,419],'training_rows':int(training.sum()),'validation_rows':int(validation.sum()),'test_rows':int(test.sum()),'rule':'Cortes temporales comunes a todas las series. Las variables solo observan días anteriores al objetivo. Selección en validación y refit train+validación antes del test final.'},'demand':{'algorithm':'HistGradientBoostingRegressor','loss':'poisson','selected_max_leaf_nodes':best,'validation_candidates':[{'leaves':l,'MAE':m} for m,l in candidates],'metrics':metrics,'baseline':'Media de unidades de los siete días anteriores'},'segments':{'algorithm':'KMeans','k':3,'rows':600,'transformation':'log1p(R,F,M), StandardScaler ajustado únicamente sobre el dataset sintético','silhouette':silhouette,'labels':names,'interpretation':'Nombres descriptivos relativos a los centroides; no son etiquetas verificadas ni juicios sobre personas.'},'datasets':{demand_path.name:digest(demand_path),rfm_path.name:digest(rfm_path)},'artifacts':{p.name:digest(p) for p in output.glob('*.joblib')},'limitations':['El patrón simulado no prueba precisión en una tienda real.','La demanda observada está afectada por faltantes de stock y devoluciones.','La inferencia debe evaluarse con datos reales antes de decisiones de compra.','No se entrenan modelos en el servidor doméstico.','No se aceptan archivos de modelos subidos por clientes.']}
    (output/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'version':'v1','test':metrics,'silhouette':silhouette,'rows':len(y)},indent=2))
if __name__=='__main__':train()
