import requests
import random

URL = "http://127.0.0.1:8000/mediciones"
USUARIO = "u003"

print("Enviando 13 lecturas normales para construir la línea base...")
for i in range(13):
    payload = {
        "usuario_id": USUARIO,
        "nombre": "Estudiante Base",
        "frecuencia_cardiaca": round(random.uniform(65, 85), 1),
        "gsr": round(random.uniform(1.5, 2.5), 2),
    }
    r = requests.post(URL, json=payload)
    print(f"  Lectura {i+1}: FC={payload['frecuencia_cardiaca']} GSR={payload['gsr']} -> {r.json()}")

print("\nAhora enviando 3 lecturas elevadas (para SU patrón, no el umbral fijo)...")
for i in range(3):
    payload = {
        "usuario_id": USUARIO,
        "nombre": "Estudiante Base",
        "frecuencia_cardiaca": round(random.uniform(93, 98), 1),
        "gsr": round(random.uniform(2.7, 3.0), 2),
    }
    r = requests.post(URL, json=payload)
    print(f"  Lectura elevada {i+1}: FC={payload['frecuencia_cardiaca']} GSR={payload['gsr']} -> {r.json()}")