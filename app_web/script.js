// NeuroSync - script.js
// Se conecta al backend (FastAPI) y actualiza el dashboard o la vista
// de estudiante segun la pagina en la que estemos. Sin frameworks,
// sin instalacion: solo abrir el .html en el navegador.

const API_URL = "http://127.0.0.1:8000";
const INTERVALO_MS = 3000;

// ---------------------------------------------------------------
// DASHBOARD DEL ORIENTADOR (index.html)
// ---------------------------------------------------------------
if (document.getElementById("tabla-usuarios")) {
  const tbody = document.querySelector("#tabla-usuarios tbody");
  const alertasLista = document.getElementById("alertas-lista");
  const selector = document.getElementById("selector-usuario");
  let usuariosPrevios = [];
  let chart = null;

  async function cargarUsuarios() {
    try {
      const resp = await fetch(`${API_URL}/usuarios`);
      const usuarios = await resp.json();
      usuariosPrevios = usuarios;

      if (usuarios.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="muted">
          Aun no hay datos. Corre el simulador_hardware para empezar a ver informacion aqui.</td></tr>`;
        return;
      }

      tbody.innerHTML = usuarios.map(u => `
        <tr class="${u.en_alerta ? "fila-alerta" : ""}">
          <td>${u.nombre}</td>
          <td>${u.ultima_fc ?? "-"}</td>
          <td>${u.ultima_gsr ?? "-"}</td>
          <td>${formatearHora(u.ultimo_timestamp)}</td>
          <td><span class="badge ${u.en_alerta ? "alerta" : "normal"}">
            ${u.en_alerta ? "En alerta" : "Normal"}</span></td>
        </tr>`).join("");

      // mantener el selector de usuarios sincronizado
      const idsActuales = Array.from(selector.options).map(o => o.value);
      usuarios.forEach(u => {
        if (!idsActuales.includes(u.usuario_id)) {
          const opt = document.createElement("option");
          opt.value = u.usuario_id;
          opt.textContent = u.nombre;
          selector.appendChild(opt);
        }
      });
      if (!selector.value && usuarios[0]) {
        selector.value = usuarios[0].usuario_id;
        cargarGrafico(selector.value);
      }
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="5" class="muted">
        No se pudo conectar al backend en ${API_URL}. ¿Esta corriendo 'uvicorn main:app --port 8000'?</td></tr>`;
    }
  }

  async function cargarAlertas() {
    try {
      const resp = await fetch(`${API_URL}/alertas?solo_activas=true`);
      const alertas = await resp.json();
      if (alertas.length === 0) {
        alertasLista.innerHTML = `<p class="muted">Sin alertas por ahora.</p>`;
        return;
      }
      alertasLista.innerHTML = alertas.map(a => `
        <div class="alerta-item">
          <span><strong>${a.usuario_id}</strong> — ${a.mensaje}</span>
          <button onclick="atenderAlerta(${a.id})">Marcar atendida</button>
        </div>`).join("");
    } catch (e) { /* el mensaje de la tabla ya avisa que no hay conexion */ }
  }

  window.atenderAlerta = async function (id) {
    await fetch(`${API_URL}/alertas/${id}/atender`, { method: "POST" });
    cargarAlertas();
    cargarUsuarios();
  };

  async function cargarGrafico(usuarioId) {
    try {
      const resp = await fetch(`${API_URL}/mediciones/${usuarioId}?limite=20`);
      const datos = await resp.json();
      const etiquetas = datos.map(d => formatearHora(d.timestamp));
      const valoresFc = datos.map(d => d.frecuencia_cardiaca);

      if (chart) {
        chart.data.labels = etiquetas;
        chart.data.datasets[0].data = valoresFc;
        chart.update();
        return;
      }
      const ctx = document.getElementById("grafico");
      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: etiquetas,
          datasets: [{
            label: "Frecuencia cardiaca (bpm)",
            data: valoresFc,
            borderColor: "#2e75b6",
            backgroundColor: "rgba(46,117,182,0.15)",
            tension: 0.3,
            fill: true,
          }],
        },
        options: { scales: { y: { suggestedMin: 50, suggestedMax: 140 } } },
      });
    } catch (e) { /* sin datos aun */ }
  }

  selector.addEventListener("change", () => cargarGrafico(selector.value));

  function formatearHora(iso) {
    if (!iso) return "-";
    const d = new Date(iso);
    return d.toLocaleTimeString("es-NI", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  cargarUsuarios();
  cargarAlertas();
  setInterval(() => {
    cargarUsuarios();
    cargarAlertas();
    if (selector.value) cargarGrafico(selector.value);
  }, INTERVALO_MS);
}

// ---------------------------------------------------------------
// VISTA DEL ESTUDIANTE (estudiante.html)
// ---------------------------------------------------------------
if (document.getElementById("estado-card")) {
  const usuarioSelect = document.getElementById("usuario-select");
  const estadoCard = document.getElementById("estado-card");
  const estadoTexto = estadoCard.querySelector(".estado-texto");
  const estadoDetalle = estadoCard.querySelector(".estado-detalle");
  const intervencion = document.getElementById("intervencion");
  const instruccion = document.getElementById("instruccion");

  let opcionesListas = false;
  let cicloRespiracion = null;

  async function cargarOpcionesUsuario() {
    try {
      const resp = await fetch(`${API_URL}/usuarios`);
      const usuarios = await resp.json();
      if (usuarios.length > 0 && !opcionesListas) {
        usuarioSelect.innerHTML = usuarios
          .map(u => `<option value="${u.usuario_id}">${u.nombre}</option>`).join("");
        opcionesListas = true;
      }
    } catch (e) { /* seguimos intentando en el proximo ciclo */ }
  }

  async function actualizarEstado() {
    if (!usuarioSelect.value) return;
    try {
      const resp = await fetch(`${API_URL}/usuarios`);
      const usuarios = await resp.json();
      const yo = usuarios.find(u => u.usuario_id === usuarioSelect.value);
      if (!yo) return;

      if (yo.en_alerta) {
        estadoCard.className = "estado-card alerta";
        estadoTexto.textContent = "Hemos notado señales de estrés";
        estadoDetalle.textContent = `FC: ${yo.ultima_fc} bpm · GSR: ${yo.ultima_gsr}`;
        mostrarIntervencion();
      } else {
        estadoCard.className = "estado-card normal";
        estadoTexto.textContent = "Todo tranquilo por ahora";
        estadoDetalle.textContent = yo.ultima_fc ? `FC: ${yo.ultima_fc} bpm · GSR: ${yo.ultima_gsr}` : "";
        ocultarIntervencion();
      }
    } catch (e) {
      estadoTexto.textContent = "Sin conexion al backend";
    }
  }


  function hablar(texto) {
  if (!sonidoActivado || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel(); // corta cualquier frase anterior que siga sonando
  const utterance = new SpeechSynthesisUtterance(texto);
  utterance.lang = "es-ES";
  utterance.rate = 0.85; // un poco más lento, tono más relajante
  window.speechSynthesis.speak(utterance);
}

let sonidoActivado = true;
 function mostrarIntervencion() {
  intervencion.classList.remove("oculto");
  if (cicloRespiracion) return;
  let inhalando = true;
  instruccion.textContent = "Inhala...";
  hablar("Inhala profundamente");
  cicloRespiracion = setInterval(() => {
    inhalando = !inhalando;
    const texto = inhalando ? "Inhala..." : "Exhala...";
    instruccion.textContent = texto;
    hablar(inhalando ? "Inhala" : "Exhala");
  }, 3000);
}
function ocultarIntervencion() {
  intervencion.classList.add("oculto");
  clearInterval(cicloRespiracion);
  cicloRespiracion = null;
  window.speechSynthesis.cancel();
}

  cargarOpcionesUsuario().then(actualizarEstado);
  setInterval(() => {
    cargarOpcionesUsuario();
    actualizarEstado();
  }, INTERVALO_MS);
}
