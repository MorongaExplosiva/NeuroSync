from statistics import mean
from sqlalchemy.orm import Session
from app import models

# Umbrales de respaldo, solo mientras el usuario no tiene historial suficiente
UMBRAL_FC_RESPALDO = 100
UMBRAL_GSR_RESPALDO = 3.5

LECTURAS_CONSECUTIVAS = 3      # cuántas lecturas seguidas evaluamos para la alerta
MINIMO_PARA_LINEA_BASE = 10    # cuántas lecturas necesita un usuario antes de tener línea base
MARGEN_FC = 1.20               # 20% arriba de su promedio personal
MARGEN_GSR = 1.30              # 30% arriba de su promedio personal


def calcular_linea_base(db: Session, usuario_id: str):
    """Devuelve (promedio_fc, promedio_gsr) del historial de este usuario,
    o None si todavía no tiene suficientes lecturas."""
    historial = (
        db.query(models.Medicion)
        .filter(models.Medicion.usuario_id == usuario_id)
        .order_by(models.Medicion.id.asc())
        .all()
    )

    # Excluimos las últimas LECTURAS_CONSECUTIVAS: son las que vamos a evaluar,
    # no queremos que un episodio de estrés actual "contamine" su propio promedio
    base = historial[:-LECTURAS_CONSECUTIVAS] if len(historial) > LECTURAS_CONSECUTIVAS else []

    if len(base) < MINIMO_PARA_LINEA_BASE:
        return None

    promedio_fc = mean(m.frecuencia_cardiaca for m in base)
    promedio_gsr = mean(m.gsr for m in base)
    return promedio_fc, promedio_gsr


def evaluar_anomalia(db: Session, usuario_id: str) -> bool:
    ultimas = (
        db.query(models.Medicion)
        .filter(models.Medicion.usuario_id == usuario_id)
        .order_by(models.Medicion.id.desc())
        .limit(LECTURAS_CONSECUTIVAS)
        .all()
    )

    if len(ultimas) < LECTURAS_CONSECUTIVAS:
        return False

    base = calcular_linea_base(db, usuario_id)

    if base is None:
        # Todavía no hay línea base: usamos el umbral fijo como respaldo
        fuera_de_rango = all(
            m.frecuencia_cardiaca > UMBRAL_FC_RESPALDO and m.gsr > UMBRAL_GSR_RESPALDO
            for m in ultimas
        )
    else:
        promedio_fc, promedio_gsr = base
        fuera_de_rango = all(
            m.frecuencia_cardiaca > promedio_fc * MARGEN_FC
            and m.gsr > promedio_gsr * MARGEN_GSR
            for m in ultimas
        )

    if not fuera_de_rango:
        return False

    alerta_activa = (
        db.query(models.Alerta)
        .filter(models.Alerta.usuario_id == usuario_id, models.Alerta.atendida == False)
        .first()
    )
    if alerta_activa:
        return True

    nueva_alerta = models.Alerta(
        usuario_id=usuario_id,
        mensaje="Posible estrés prolongado: variación significativa respecto a su patrón habitual",
    )
    db.add(nueva_alerta)
    db.commit()
    return True