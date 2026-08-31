from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Orientador(Base):
    __tablename__ = "orientadores"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=True)

    usuarios = relationship("Usuario", back_populates="orientador")
    alertas = relationship("Alerta", back_populates="orientador")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=True)
    orientador_id = Column(String, ForeignKey("orientadores.id"))

    orientador = relationship("Orientador", back_populates="usuarios")
    mediciones = relationship("Medicion", back_populates="usuario")
    alertas = relationship("Alerta", back_populates="usuario")


class Medicion(Base):
    __tablename__ = "mediciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    frecuencia_cardiaca = Column(Float)
    gsr = Column(Float)

    usuario = relationship("Usuario", back_populates="mediciones")


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False)
    orientador_id = Column(String, ForeignKey("orientadores.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    mensaje = Column(String)
    atendida = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="alertas")
    orientador = relationship("Orientador", back_populates="alertas")