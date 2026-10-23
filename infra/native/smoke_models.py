"""Prueba privada de inferencia y OpenCV con datos artificiales, sin levantar HTTP."""
from pathlib import Path
from datetime import date
import json
import math
import resource
import sys


def main():
    root=Path(sys.argv[1]).resolve(strict=True)
    if root.parent != Path('/home/alecv/Parcial2_FashionStore/releases'):
        raise SystemExit('Usar una versión de P2 previamente verificada.')
    sys.path.insert(0,str(root/'Parcial2_backend'))
    import numpy as np
    import cv2,sklearn
    from threadpoolctl import threadpool_limits
    from app.ml_features import demand_features
    from app.services.analytics import artifact
    with threadpool_limits(limits=1):
        demand=float(artifact('demand.joblib')['model'].predict([demand_features([1]*28,date.today(),50,False)])[0])
        segment=int(artifact('segments.joblib')['model'].predict(np.log1p([[10,2,100]]))[0])
    if not math.isfinite(demand) or demand<0 or segment not in {0,1,2}:
        raise RuntimeError('Resultado de inferencia fuera del contrato.')
    image=cv2.cvtColor(np.zeros((4,4,3),dtype=np.uint8),cv2.COLOR_BGR2RGB)
    print(json.dumps({'artificial_inputs':True,'numpy':np.__version__,'sklearn':sklearn.__version__,
                      'demand_prediction':demand,'segment':segment,'opencv_shape':list(image.shape),
                      'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))


if __name__=='__main__':main()
