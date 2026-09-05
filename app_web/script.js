// NeuroSync - script.js
const API_URL = "http://127.0.0.1:8000";
const INTERVALO_MS = 2500;

// Utilidad global de formateo de hora
function formatearHora(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleTimeString("es-NI", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// ===============================================================
// 1. DASHBOARD DEL ORIENTADOR (index.html)
// ===============================================================
if (document.getElementById("tabla-usuarios")) {
  const tbody = document.querySelector("#tabla-usuarios tbody") || document.getElementById("cuerpo-tabla");
  const alertasLista = document.getElementById("contenedor-alertas") || document.getElementById("alertas-lista");
  const selector = document.getElementById("selector-estudiante") || document.getElementById("selector-usuario");
  
  // KPIs
  const kpiTotal = document.getElementById("kpi-total");
  const kpiAlertas = document.getElementById("kpi-alertas");
  const kpiEstables = document.getElementById("kpi-estables");
  const kpiFcPromedio = document.getElementById("kpi-fc-promedio");

  let chart = null;

  async function cargarUsuarios() {
    try {
      const resp = await fetch(`${API_URL}/usuarios`);
      const usuarios = await resp.json();

      // Actualizar métricas KPI superiores
      if (kpiTotal) kpiTotal.textContent = usuarios.length;
      if (kpiAlertas) {
        const enAlerta = usuarios.filter(u => u.en_alerta).length;
        kpiAlertas.textContent = enAlerta;
        kpiAlertas.style.color = enAlerta > 0 ? "#dc2626" : "#0f172a";
      }
      if (kpiEstables) {
        kpiEstables.textContent = usuarios.filter(u => !u.en_alerta).length;
      }
      if (kpiFcPromedio && usuarios.length > 0) {
        const conFc = usuarios.filter(u => u.ultima_fc !== null && u.ultima_fc !== undefined);
        if (conFc.length > 0) {
          const prom = conFc.reduce((acc, u) => acc + u.ultima_fc, 0) / conFc.length;
          kpiFcPromedio.textContent = `${prom.toFixed(1)} bpm`;
        }
      }

      // Renderizar filas de telemetría en la tabla
      if (usuarios.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #64748b; padding: 1.5rem;">
          Esperando telemetría... Ejecuta simulador_hardware/simulador.py para comenzar.</td></tr>`;
        return;
      }

      tbody.innerHTML = usuarios.map(u => `
        <tr style="${u.en_alerta ? 'background: #fef2f2;' : ''}">
          <td style="font-weight: 600;">${u.nombre}</td>
          <td>${u.ultima_fc !== null ? `${u.ultima_fc.toFixed(1)} bpm` : "-"}</td>
          <td>${u.ultima_gsr !== null ? `${u.ultima_gsr.toFixed(2)} µS` : "-"}</td>
          <td>${formatearHora(u.ultimo_timestamp)}</td>
          <td>
            <span class="${u.en_alerta ? 'badge-alerta' : 'badge-normal'}">
              ${u.en_alerta ? "🚨 En alerta" : "● Normal"}
            </span>
          </td>
        </tr>`).join("");

      // Sincronizar el desplegable de estudiantes
      if (selector) {
        const idsActuales = Array.from(selector.options).map(o => o.value);
        usuarios.forEach(u => {
          if (!idsActuales.includes(u.usuario_id)) {
            const opt = document.createElement("option");
            opt.value = u.usuario_id;
            opt.textContent = `${u.nombre} (${u.usuario_id})`;
            selector.appendChild(opt);
          }
        });

        if (!selector.value && usuarios[0]) {
          selector.value = usuarios[0].usuario_id;
          cargarGrafico(selector.value);
        }
      }
    } catch (e) {
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #dc2626; padding: 1.5rem;">
          No se pudo conectar con el servidor en ${API_URL}. Revisa que uvicorn esté corriendo.</td></tr>`;
      }
    }
  }

  async function cargarAlertas() {
    if (!alertasLista) return;
    try {
      const resp = await fetch(`${API_URL}/alertas?solo_activas=true`);
      const alertas = await resp.json();
      
      if (alertas.length === 0) {
        alertasLista.innerHTML = `<p style="color: #64748b; font-size: 0.9rem;">Sin alertas fisiológicas activas por el momento.</p>`;
        return;
      }

      alertasLista.innerHTML = alertas.map(a => `
        <div class="item-alerta">
          <div>
            <strong style="color: #991b1b; font-size: 0.95rem;">[${a.usuario_id}]</strong> 
            <span style="color: #7f1d1d; font-size: 0.9rem;">${a.mensaje}</span>
          </div>
          <button class="btn-atender" onclick="atenderAlerta(${a.id})">Marcar atendida</button>
        </div>`).join("");
    } catch (e) { /* Error de conexión gestionado por la tabla */ }
  }

  window.atenderAlerta = async function (id) {
    try {
      await fetch(`${API_URL}/alertas/${id}/atender`, { method: "POST" });
      cargarAlertas();
      cargarUsuarios();
    } catch (e) {
      console.error("Error al marcar alerta:", e);
    }
  };

  async function cargarGrafico(usuarioId) {
    if (!usuarioId) return;
    const canvas = document.getElementById("grafico-fc") || document.getElementById("grafico");
    if (!canvas) return;

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

      chart = new Chart(canvas, {
        type: "line",
        data: {
          labels: etiquetas,
          datasets: [{
            label: "Frecuencia Cardíaca (bpm)",
            data: valoresFc,
            borderColor: "#1e3a8a",
            backgroundColor: "rgba(30, 58, 138, 0.12)",
            borderWidth: 2.5,
            tension: 0.3,
            fill: true,
            pointBackgroundColor: "#1e3a8a"
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { suggestedMin: 50, suggestedMax: 140, grid: { color: "#e2e8f0" } },
            x: { grid: { display: false } }
          }
        },
      });
    } catch (e) { /* Sin registros históricos suficientes */ }
  }

  if (selector) {
    selector.addEventListener("change", () => cargarGrafico(selector.value));
  }

  cargarUsuarios();
  cargarAlertas();
  setInterval(() => {
    cargarUsuarios();
    cargarAlertas();
    if (selector && selector.value) cargarGrafico(selector.value);
  }, INTERVALO_MS);
}

// ===============================================================
// 2. PORTAL DEL ESTUDIANTE (estudiante.html)
// ===============================================================
if (document.getElementById("fc-valor") || document.getElementById("selector-usuario")) {
  const selectorUsuario = document.getElementById("selector-usuario");
  const fcValor = document.getElementById("fc-valor");
  const gsrValor = document.getElementById("gsr-valor");
  const estadoValor = document.getElementById("estado-valor");
  const bannerAlerta = document.getElementById("alerta");
  const circulo = document.getElementById("circulo");
  const instruccion = document.getElementById("instruccion-respiracion");

  let usuariosCargados = false;
  let cicloRespiracion = null;
  let inhalando = true;

  function hablar(texto) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = "es-ES";
    utterance.rate = 0.85;
    window.speechSynthesis.speak(utterance);
  }

  function iniciarRespiracionGuiada() {
    if (cicloRespiracion) return;
    if (instruccion) instruccion.textContent = "Inhala...";
    if (circulo) circulo.style.transform = "scale(1.25)";
    hablar("Inhala profundamente");

    cicloRespiracion = setInterval(() => {
      inhalando = !inhalando;
      if (instruccion) instruccion.textContent = inhalando ? "Inhala..." : "Exhala...";
      if (circulo) circulo.style.transform = inhalando ? "scale(1.25)" : "scale(0.85)";
      hablar(inhalando ? "Inhala" : "Exhala");
    }, 4000);
  }

  function detenerRespiracionGuiada() {
    if (!cicloRespiracion) return;
    clearInterval(cicloRespiracion);
    cicloRespiracion = null;
    if (instruccion) instruccion.textContent = "Ritmo estable";
    if (circulo) circulo.style.transform = "scale(1)";
    window.speechSynthesis.cancel();
  }

  async function cargarSelectEstudiantes() {
    try {
      const resp = await fetch(`${API_URL}/usuarios`);
      const usuarios = await resp.json();

      if (usuarios.length > 0 && !usuariosCargados && selectorUsuario) {
        selectorUsuario.innerHTML = usuarios.map(u => 
          `<option value="${u.usuario_id}">${u.nombre} (${u.usuario_id})</option>`
        ).join("");
        usuariosCargados = true;
      }
    } catch (e) { /* Reintento en el siguiente ciclo */ }
  }

  async function actualizarTelemetriaEstudiante() {
    if (!selectorUsuario || !selectorUsuario.value) return;
    try {
      const resp = await fetch(`${API_URL}/usuarios`);
      const usuarios = await resp.json();
      const actual = usuarios.find(u => u.usuario_id === selectorUsuario.value);

      if (!actual) return;

      // Actualizar valores numéricos
      if (fcValor) {
        fcValor.innerHTML = `${actual.ultima_fc !== null ? actual.ultima_fc.toFixed(1) : "--"} <span style="font-size: 1rem; font-weight: 600; color: #64748b;">bpm</span>`;
      }
      if (gsrValor) {
        gsrValor.innerHTML = `${actual.ultima_gsr !== null ? actual.ultima_gsr.toFixed(2) : "--"} <span style="font-size: 1rem; font-weight: 600; color: #64748b;">µS</span>`;
      }

      // Evaluar estado de alerta o normalidad
      if (actual.en_alerta) {
        if (estadoValor) {
          estadoValor.textContent = "🚨 Alerta de Estrés";
          estadoValor.style.color = "#dc2626";
        }
        if (bannerAlerta) {
          bannerAlerta.style.display = "block";
          bannerAlerta.innerHTML = `
            <h3>⚠️ Elevación Fisiológica Detectada</h3>
            <p>Se registraron picos superiores a tu línea base (FC: ${actual.ultima_fc?.toFixed(1)} bpm · GSR: ${actual.ultima_gsr?.toFixed(2)} µS). Inicia el ejercicio respiratorio para estabilizar tu ritmo.</p>
          `;
        }
        iniciarRespiracionGuiada();
      } else {
        if (estadoValor) {
          estadoValor.textContent = "● Tranquilo (Basal)";
          estadoValor.style.color = "#10b981";
        }
        if (bannerAlerta) bannerAlerta.style.display = "none";
        detenerRespiracionGuiada();
      }
    } catch (e) {
      if (estadoValor) estadoValor.textContent = "Sin conexión";
    }
  }

  if (selectorUsuario) {
    selectorUsuario.addEventListener("change", () => {
      detenerRespiracionGuiada();
      actualizarTelemetriaEstudiante();
    });
  }

  cargarSelectEstudiantes().then(actualizarTelemetriaEstudiante);
  setInterval(() => {
    cargarSelectEstudiantes();
    actualizarTelemetriaEstudiante();
  }, INTERVALO_MS);
}