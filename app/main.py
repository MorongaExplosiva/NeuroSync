from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uvicorn

from app.database import engine, get_db, Base
from app import models, schemas
from app import deteccion
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NeuroSync API")


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