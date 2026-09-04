from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import engine, get_db, Base
from app import models, schemas, deteccion

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NeuroSync API")

# Habilitar CORS para permitir que los archivos HTML se comuniquen con la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.post("/mediciones", response_model=schemas.MedicionOut)
def recibir_medicion(m: schemas.MedicionCreate, db: Session = Depends(get_db)):
    if not m.usuario_id or not m.usuario_id.strip():
        raise HTTPException(status_code=400, detail="usuario_id no puede estar vacío")
    if m.frecuencia_cardiaca <= 0 or m.frecuencia_cardiaca > 250:
        raise HTTPException(status_code=400, detail="frecuencia_cardiaca fuera de rango válido")
    if m.gsr < 0:
        raise HTTPException(status_code=400, detail="gsr no puede ser negativo")

    usuario = db.query(models.Usuario).filter(models.Usuario.id == m.usuario_id).first()
    if not usuario:
        usuario = models.Usuario(id=m.usuario_id, nombre=m.nombre or m.usuario_id)
        db.add(usuario)
        db.commit()

    medicion = models.Medicion(
        usuario_id=m.usuario_id,
        frecuencia_cardiaca=m.frecuencia_cardiaca,
        gsr=m.gsr,
    )
    db.add(medicion)
    db.commit()
    db.refresh(medicion)

    alerta = deteccion.evaluar_anomalia(db, m.usuario_id)

    return {
        "id": medicion.id,
        "usuario_id": medicion.usuario_id,
        "timestamp": medicion.timestamp,
        "frecuencia_cardiaca": medicion.frecuencia_cardiaca,
        "gsr": medicion.gsr,
        "alerta_generada": alerta,
    }

# --- Endpoints que consume script.js ---

@app.get("/usuarios")
def obtener_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).all()
    resultado = []
    for u in usuarios:
        ultima_med = (
            db.query(models.Medicion)
            .filter(models.Medicion.usuario_id == u.id)
            .order_by(models.Medicion.timestamp.desc())
            .first()
        )
        alerta_activa = (
            db.query(models.Alerta)
            .filter(models.Alerta.usuario_id == u.id, models.Alerta.atendida == False)
            .first()
        )
        resultado.append({
            "usuario_id": u.id,
            "nombre": u.nombre,
            "ultima_fc": ultima_med.frecuencia_cardiaca if ultima_med else None,
            "ultima_gsr": ultima_med.gsr if ultima_med else None,
            "ultimo_timestamp": ultima_med.timestamp.isoformat() if ultima_med else None,
            "en_alerta": alerta_activa is not None,
        })
    return resultado

@app.get("/alertas")
def obtener_alertas(solo_activas: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Alerta)
    if solo_activas:
        query = query.filter(models.Alerta.atendida == False)
    alertas = query.order_by(models.Alerta.timestamp.desc()).all()
    return [
        {
            "id": a.id,
            "usuario_id": a.usuario_id,
            "mensaje": a.mensaje,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "atendida": a.atendida,
        }
        for a in alertas
    ]

@app.post("/alertas/{alerta_id}/atender")
def atender_alerta(alerta_id: int, db: Session = Depends(get_db)):
    alerta = db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    alerta.atendida = True
    db.commit()
    return {"status": "ok", "mensaje": "Alerta atendida"}

@app.get("/mediciones/{usuario_id}")
def obtener_historial_mediciones(usuario_id: str, limite: int = 20, db: Session = Depends(get_db)):
    mediciones = (
        db.query(models.Medicion)
        .filter(models.Medicion.usuario_id == usuario_id)
        .order_by(models.Medicion.timestamp.desc())
        .limit(limite)
        .all()
    )
    mediciones.reverse()
    return [
        {
            "id": m.id,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "frecuencia_cardiaca": m.frecuencia_cardiaca,
            "gsr": m.gsr,
        }
        for m in mediciones
    ]