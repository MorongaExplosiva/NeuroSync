import time
import random
import requests

API_URL = "http://127.0.0.1:8000/mediciones"

# Perfiles de simulación
ESTUDIANTES = [
    {"id": "u001", "nombre": "Carlos Mendoza"},
    {"id": "u002", "nombre": "Andrea Silva"},
    {"id": "u003", "nombre": "Fernando Arauz"},
]

def enviar_lectura(usuario_id: str, nombre: str, fc: float, gsr: float):
    payload = {
        "usuario_id": usuario_id,
        "nombre": nombre,
        "frecuencia_cardiaca": round(fc, 1),
        "gsr": round(gsr, 2),
    }
    try:
        resp = requests.post(API_URL, json=payload, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            alerta = " 🚨 [ALERTA DISPARADA]" if data.get("alerta_generada") else ""
            print(f"[{usuario_id}] {nombre} | FC: {payload['frecuencia_cardiaca']} bpm | GSR: {payload['gsr']}{alerta}")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar con el backend en {API_URL}. ¿Está Uvicorn encendido?")

def simular_flujo():
    print("=" * 60)
    print("📡 SIMULADOR DE WEARABLE / HARDWARE BIOMÉTRICO (NeuroSync)")
    print("=" * 60)
    print("Opciones de escenario:")
    print(" 1. Monitoreo regular (todos los estudiantes en rangos basales normales)")
    print(" 2. Simulación de episodio de estrés sostenido (usuario u003)")
    print(" 3. Simulación de crisis crítica instantánea (usuario u003 - FC > 120 bpm)")
    print("=" * 60)

    modo = input("Selecciona un escenario (1, 2 o 3) [default: 1]: ").strip() or "1"
    intervalo = 2.5  # segundos entre envíos

    print(f"\nIniciando transmisión hacia {API_URL} (Presiona Ctrl+C para detener)...\n")

    contador = 0
    while True:
        contador += 1
        for est in ESTUDIANTES:
            if est["id"] == "u003" and modo == "2" and contador > 4:
                # Disparo de estrés sostenido tras lecturas iniciales
                fc = random.uniform(98.0, 108.0)
                gsr = random.uniform(3.6, 4.2)
            elif est["id"] == "u003" and modo == "3" and contador > 2:
                # Crisis crítica aguda
                fc = random.uniform(122.0, 135.0)
                gsr = random.uniform(5.1, 5.8)
            else:
                # Patrón fisiológico habitual/tranquilo
                fc = random.uniform(68.0, 82.0)
                gsr = random.uniform(1.6, 2.4)

            enviar_lectura(est["id"], est["nombre"], fc, gsr)
            time.sleep(0.4)

        time.sleep(intervalo)

if __name__ == "__main__":
    try:
        simular_flujo()
    except KeyboardInterrupt:
        print("\n\nSimulación detenida por el usuario.")