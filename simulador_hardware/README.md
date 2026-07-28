# simulador_hardware — Capa Física (Mecatrónica / Electromédica)

Scripts que simulan la transmisión de datos biométricos, ya que el proyecto no depende de hardware físico real durante el sprint.

## Contenido esperado
- Script que genere valores simulados de **Frecuencia Cardíaca (FC)**.
- Script que genere valores simulados de **Respuesta Galvánica de la Piel (GSR)**.
- Formato de datos (JSON) que se envía hacia `api_backend`.
- Documentación del protocolo de comunicación usado (HTTP, WebSocket, etc.).

## Estructura sugerida
```
simulador_hardware/
├── simulador_fc.py
├── simulador_gsr.py
├── enviar_datos.py     # envía el JSON simulado al backend
└── formato_datos.md    # especificación del payload
```

## Ejemplo de payload (JSON)
```json
{
  "usuario_id": "u001",
  "timestamp": "2026-07-31T10:15:00Z",
  "frecuencia_cardiaca": 92,
  "gsr": 3.4
}
```

## Pendiente
- [ ] Definir rango de valores normal vs. estrés para las pruebas
- [ ] Probar el envío hacia `api_backend`
