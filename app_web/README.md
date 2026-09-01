# app_web — Capa de Usuario (UX/UI)

HTML/CSS/JS puro (sin build, sin instalación) que se conecta al backend en `http://127.0.0.1:8000`.

## Páginas
- **`index.html`** — Dashboard del orientador: tabla de estudiantes en tiempo real, alertas activas con botón "Marcar atendida", y gráfico de historial de FC (Chart.js vía CDN).
- **`estudiante.html`** — Vista del estudiante: estado actual (tranquilo / señales de estrés) y, si hay alerta activa, una micro-intervención con animación de respiración guiada.

## Cómo usar
Solo abre cualquiera de los dos `.html` directamente en el navegador (doble clic). Ambas páginas hacen `fetch` al backend cada 3 segundos.

Si el backend corre en otra URL/puerto, cambia la constante `API_URL` al inicio de `script.js`.

## Pendiente
- [ ] Ajustar diseño/identidad visual final de NeuroSync
- [ ] Agregar login real por estudiante (hoy se elige de una lista desplegable)
