from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MedicionCreate(BaseModel):
    usuario_id: str
    nombre: Optional[str] = None
    frecuencia_cardiaca: float
    gsr: float

class MedicionOut(BaseModel):
    id: int
    usuario_id: str
    timestamp: datetime
    frecuencia_cardiaca: float
    gsr: float
    alerta_generada: bool = False

    class Config:
        from_attributes = True