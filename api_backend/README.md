# api_backend — Capa Lógica (Cibernética)

Procesamiento de datos, base de datos y algoritmos de detección de anomalías.

## Contenido esperado
- API que recibe los datos biométricos enviados desde `simulador_hardware`.
- Modelo de base de datos: usuarios, mediciones (FC, GSR), alertas.
- Algoritmo de detección de anomalías (ej. umbral de FC/GSR sostenido en el tiempo).
- Lógica de alertas tempranas hacia el dashboard de orientadores.

## Estructura sugerida
```
api_backend/
├── app/
│   ├── modelos/
│   ├── rutas/
│   └── servicios/         # lógica de detección de anomalías
├── requirements.txt        # o package.json, según el stack elegido
└── .env.example
```

## Pendiente
- [ ] Definir stack (Python/Flask/FastAPI, Node/Express, etc.)
- [ ] Diseñar esquema de base de datos
- [ ] Endpoint de recepción de datos (`POST /mediciones`)
- [ ] Endpoint de alertas (`GET /alertas`)
