"""La misma transformación, sin mirar el día objetivo, para entrenamiento e inferencia."""
import math
from statistics import mean
FEATURES=['media_7','media_28','ayer','hace_7','dia_sin','dia_cos','mes_sin','mes_cos','precio','oferta']
def demand_features(history,target_day,price,offer=False):
    if len(history)<28:raise ValueError('Se requieren 28 días anteriores al objetivo.')
    return [mean(history[-7:]),mean(history[-28:]),history[-1],history[-7],math.sin(2*math.pi*target_day.weekday()/7),math.cos(2*math.pi*target_day.weekday()/7),math.sin(2*math.pi*(target_day.month-1)/12),math.cos(2*math.pi*(target_day.month-1)/12),float(price),int(offer)]
