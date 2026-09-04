from statistics import mean
from sqlalchemy.orm import Session
from app import models

# ---------- 1. Umbrales numéricos normales y críticos ----------
UMBRALES = {
    "frecuencia_cardiaca": {
        "normal_max": 100,   # arriba de esto ya es señal de alerta
        "critico": 120,      # arriba de esto es urgente, sin esperar patrón sostenido
    },
    "gsr": {
        "normal_max": 3.5,
        "critico": 5.0,
    },
}

LECTURAS_CONSECUTIVAS = 3
MINIMO_PARA_LINEA_BASE = 10
MARGEN_FC = 1.20   # 20% arriba del promedio personal
MARGEN_GSR = 1.30  # 30% arriba del promedio personal


def calcular_linea_base(db: Session, usuario_id: str):
    historial = (
        db.query(models.Medicion)
        .filter(models.Medicion.usuario_id == usuario_id)
        .order_by(models.Medicion.id.asc())
        .all()
    )
    base = historial[:-LECTURAS_CONSECUTIVAS] if len(historial) > LECTURAS_CONSECUTIVAS else []
    if len(base) < MINIMO_PARA_LINEA_BASE:
        return None
    return mean(m.frecuencia_cardiaca for m in base), mean(m.gsr for m in base)


# ---------- 2. Reglas modulares (el "motor de inferencia") ----------
def regla_fc_fuera_de_rango(medicion, referencia_fc):
    return medicion.frecuencia_cardiaca > referencia_fc


def regla_gsr_fuera_de_rango(medicion, referencia_gsr):
    return medicion.gsr > referencia_gsr


def regla_fc_critica(medicion):
    return medicion.frecuencia_cardiaca > UMBRALES["frecuencia_cardiaca"]["critico"]


def regla_gsr_critica(medicion):
    return medicion.gsr > UMBRALES["gsr"]["critico"]


def motor_inferencia(medicion, referencia_fc, referencia_gsr) -> str:
    """Evalúa las reglas de estado para UNA medición."""
    if regla_fc_critica(medicion) or regla_gsr_critica(medicion):
        return "critico"
    if regla_fc_fuera_de_rango(medicion, referencia_fc) and regla_gsr_fuera_de_rango(medicion, referencia_gsr):
        return "elevado"
    return "normal"


# ---------- 3. Evaluación modular: cambia el estado a "anomalia" ----------
def evaluar_estado(db: Session, usuario_id: str) -> str:
    ultimas = (
        db.query(models.Medicion)
        .filter(models.Medicion.usuario_id == usuario_id)
        .order_by(models.Medicion.id.desc())
        .limit(LECTURAS_CONSECUTIVAS)
        .all()
    )
    if not ultimas:
        return "normal"

    base = calcular_linea_base(db, usuario_id)
    if base is None:
        referencia_fc = UMBRALES["frecuencia_cardiaca"]["normal_max"]
        referencia_gsr = UMBRALES["gsr"]["normal_max"]
    else:
        promedio_fc, promedio_gsr = base
        referencia_fc = promedio_fc * MARGEN_FC
        referencia_gsr = promedio_gsr * MARGEN_GSR

    # Condición crítica: la lectura MÁS RECIENTE ya es urgente, no espera patrón sostenido
    if motor_inferencia(ultimas[0], referencia_fc, referencia_gsr) == "critico":
        return "anomalia"

    # Patrón sostenido: las últimas N lecturas seguidas "elevadas"
    if len(ultimas) < LECTURAS_CONSECUTIVAS:
        return "normal"
    estados = [motor_inferencia(m, referencia_fc, referencia_gsr) for m in ultimas]
    if all(e == "elevado" for e in estados):
        return "anomalia"

    return "normal"


def evaluar_anomalia(db: Session, usuario_id: str) -> bool:
    """Punto de entrada que ya usa main.py: True si el estado cambió a 'anomalia'."""
    if evaluar_estado(db, usuario_id) != "anomalia":
        return False

    alerta_activa = (
        db.query(models.Alerta)
        .filter(models.Alerta.usuario_id == usuario_id, models.Alerta.atendida == False)
        .first()
    )
    if alerta_activa:
        return True

    # Determinar severidad según la lectura más reciente
    ultima = (
        db.query(models.Medicion)
        .filter(models.Medicion.usuario_id == usuario_id)
        .order_by(models.Medicion.id.desc())
        .first()
    )
    es_critica = regla_fc_critica(ultima) or regla_gsr_critica(ultima)
    gravedad = "CRÍTICA" if es_critica else "ELEVADA"

    nueva_alerta = models.Alerta(
        usuario_id=usuario_id,
        mensaje=f"[{gravedad}] Posible estrés prolongado: variación significativa respecto a su patrón habitual",
    )
    db.add(nueva_alerta)
    db.commit()
    return True