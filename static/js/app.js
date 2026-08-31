/**
 * app.js
 * Lógica del frontend — Generador de Documentos de Pago UNMSM
 *
 * Responsabilidades:
 *   1. Navegación entre pantallas (inicio / declaración / asistencia / informe)
 *   2. Generación de folios visuales aleatorios
 *   3. Preview de archivos subidos (nombre + miniatura de firma)
 *   4. Galería de evidencias con límite de 20 fotos y eliminación individual
 *   5. Lista dinámica de actividades (agregar / quitar filas)
 *   6. Envío de formularios al backend y manejo del overlay de procesamiento
 *   7. Autollenado de perfil vía localStorage (persistencia entre sesiones)
 */

(function () {
  "use strict";

  /* ============================================================
   * 1. NAVEGACIÓN ENTRE PANTALLAS
   * ============================================================ */
  const screens   = document.querySelectorAll(".screen");
  const btnVolver = document.getElementById("btnVolver");

  function mostrarPantalla(id) {
    screens.forEach((s) => s.classList.toggle("active", s.id === "screen-" + id));
    btnVolver.hidden = id === "inicio";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  document.querySelectorAll(".folio-card").forEach((card) => {
    card.addEventListener("click", () => mostrarPantalla(card.dataset.target));
  });

  btnVolver.addEventListener("click", () => mostrarPantalla("inicio"));

  /* ============================================================
   * 2. FOLIOS AUTOGENERADOS (visual — el backend puede reasignar el real)
   * ============================================================ */
  document.querySelectorAll(".folio[data-folio]").forEach((el) => {
    const year   = new Date().getFullYear();
    const random = String(Math.floor(Math.random() * 90000) + 10000);
    el.textContent = `UNMSM-${year}-${random}`;
  });

  /* ============================================================
   * 3. PREVIEW DE ARCHIVOS (nombre en dropzone + miniatura de firma)
   * ============================================================ */
  document.querySelectorAll("input[type=file]").forEach((input) => {
    input.addEventListener("change", () => {
      const label = document.querySelector(`[data-filename-for="${input.id}"]`);

      if (label && input.files.length === 1) {
        label.textContent = input.files[0].name;
      } else if (label && input.files.length > 1) {
        label.textContent = `${input.files.length} archivos seleccionados`;
      }

      // Miniatura para inputs de firma
      const preview = document.getElementById(input.id + "-preview");
      if (preview && input.files[0]) {
        preview.src = URL.createObjectURL(input.files[0]);
        preview.classList.add("show");
      }
    });
  });

  /* ============================================================
   * 4. GALERÍA DE EVIDENCIAS — máximo 20 fotos, eliminación individual
   * ============================================================ */
  const MAX_FOTOS       = 20;
  const inputEvidencias = document.getElementById("inf-evidencias");
  const galeria         = document.getElementById("galeria-evidencias");
  const contador        = document.getElementById("contador-fotos");
  let archivosEvidencia = [];

  function renderGaleria() {
    galeria.innerHTML = "";

    archivosEvidencia.forEach((file, idx) => {
      const item = document.createElement("div");
      item.className = "galeria-item";

      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.alt = `Evidencia ${idx + 1}`;
      item.appendChild(img);

      const btnQuitar = document.createElement("button");
      btnQuitar.type = "button";
      btnQuitar.textContent = "×";
      btnQuitar.setAttribute("aria-label", `Quitar evidencia ${idx + 1}`);
      btnQuitar.addEventListener("click", () => {
        archivosEvidencia.splice(idx, 1);
        renderGaleria();
      });
      item.appendChild(btnQuitar);

      galeria.appendChild(item);
    });

    contador.textContent = `${archivosEvidencia.length} de ${MAX_FOTOS} fotos seleccionadas`;
    contador.classList.toggle("limite", archivosEvidencia.length >= MAX_FOTOS);
  }

  if (inputEvidencias) {
    inputEvidencias.addEventListener("change", () => {
      const nuevos     = Array.from(inputEvidencias.files);
      const espacioLibre = MAX_FOTOS - archivosEvidencia.length;

      if (nuevos.length > espacioLibre) {
        anunciar(`Solo se agregaron ${espacioLibre} fotos; el límite es ${MAX_FOTOS}.`);
      }

      archivosEvidencia = archivosEvidencia.concat(nuevos.slice(0, espacioLibre));
      inputEvidencias.value = "";
      renderGaleria();
    });
  }

  /* ============================================================
   * 5. LISTA DINÁMICA DE ACTIVIDADES (Informe de Actividades)
   * ============================================================ */
  const listaActividades    = document.getElementById("lista-actividades");
  const btnAgregarActividad = document.getElementById("btn-agregar-actividad");
  let contadorActividad     = 0;

  function agregarActividad(valorInicial) {
    contadorActividad++;

    const row = document.createElement("div");
    row.className = "actividad-row";

    const textarea       = document.createElement("textarea");
    textarea.name        = "actividad_" + contadorActividad;
    textarea.placeholder = "Describe una actividad realizada durante el mes…";
    textarea.value       = valorInicial || "";
    textarea.setAttribute("aria-label", "Actividad");
    textarea.addEventListener("input", () => {
      row.classList.remove("invalid");
      const existingMarker = row.querySelector(".field-error-marker");
      if (existingMarker) existingMarker.remove();
    });
    row.appendChild(textarea);

    const btnQuitar   = document.createElement("button");
    btnQuitar.type    = "button";
    btnQuitar.className = "actividad-quitar";
    btnQuitar.textContent = "×";
    btnQuitar.setAttribute("aria-label", "Quitar esta actividad");
    btnQuitar.addEventListener("click", () => {
      if (listaActividades.children.length > 1) {
        row.remove();
      } else {
        textarea.value = ""; // No eliminar la última fila, solo limpiarla
      }
    });
    row.appendChild(btnQuitar);

    listaActividades.appendChild(row);
  }

  if (btnAgregarActividad) {
    btnAgregarActividad.addEventListener("click", () => agregarActividad());
    // Arranca con 3 filas, como un informe típico
    agregarActividad();
    agregarActividad();
    agregarActividad();
  }

  /* ============================================================
   * 6. OVERLAY DE PROCESAMIENTO (spinner → sello → descarga)
   * ============================================================ */
  const overlay          = document.getElementById("overlay");
  const sello            = document.getElementById("sello");
  const spinner          = document.getElementById("overlay-spinner");
  const overlayEstado    = document.getElementById("overlay-estado");
  const overlayTitulo    = document.getElementById("overlay-titulo");
  const overlayDesc      = document.getElementById("overlay-desc");
  const btnDescargar     = document.getElementById("btn-descargar");
  const btnCerrarOverlay = document.getElementById("btn-cerrar-overlay");
  const selloFecha       = document.getElementById("sello-fecha");

  function anunciar(msg) {
    const el = document.getElementById("anuncios");
    if (el) el.textContent = msg;
  }

  function abrirOverlay() {
    overlay.classList.add("active");
    spinner.style.display = "block";
    sello.classList.remove("golpe");
    sello.style.opacity      = "0";
    overlayEstado.textContent = "Generando documento…";
    overlayTitulo.textContent = "Sellando tu expediente";
    overlayDesc.textContent   = "Esto toma solo unos segundos.";
    btnDescargar.classList.remove("show");
    btnCerrarOverlay.classList.remove("show");
  }

  function mostrarExito(urlDescarga, nombreArchivo) {
    spinner.style.display = "none";
    selloFecha.textContent = new Date().toLocaleDateString("es-PE");
    sello.classList.add("golpe");

    overlayEstado.textContent = "Documento generado";
    overlayTitulo.textContent = "¡Listo!";
    overlayDesc.textContent   = "Tu documento fue sellado correctamente.";

    btnDescargar.classList.add("show");
    btnCerrarOverlay.classList.add("show");

    btnDescargar.onclick = () => {
      const a    = document.createElement("a");
      a.href     = urlDescarga;
      a.download = nombreArchivo || "documento.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
    };

    anunciar("El documento se generó correctamente y está listo para descargar.");
  }

  function mostrarError(mensaje) {
    spinner.style.display = "none";
    overlayEstado.textContent = "No se pudo generar";
    overlayTitulo.textContent = "Ocurrió un problema";
    overlayDesc.textContent   = mensaje || "Intenta nuevamente en unos segundos.";
    btnCerrarOverlay.classList.add("show");
    anunciar("Ocurrió un problema al generar el documento.");
  }

  function obtenerEtiquetaCampo(campo) {
    const label = campo.closest(".campo")?.querySelector("label");
    if (label) {
      return label.textContent.replace(/\*+\s*$/, "").trim();
    }

    if (campo.dataset.label) return campo.dataset.label;
    return campo.name || "campo";
  }

  function limpiarMarcadores(form) {
    form.querySelectorAll(".invalid, .field-error-marker").forEach((el) => {
      el.classList.remove("invalid");
      if (el.classList.contains("field-error-marker")) {
        el.remove();
      }
    });
  }

  function marcarCampoFaltante(campo) {
    const contenedor = campo.closest(".campo") || campo.closest(".dropzone");
    if (!contenedor) return;

    contenedor.classList.add("invalid");
    if (!contenedor.querySelector(".field-error-marker")) {
      const marcador = document.createElement("span");
      marcador.className = "field-error-marker";
      marcador.textContent = "?";
      marcador.setAttribute("title", "Falta completar este campo");
      marcador.setAttribute("aria-label", "Falta completar este campo");
      contenedor.appendChild(marcador);
    }
  }

  function validarFormulario(form) {
    limpiarMarcadores(form);
    const camposRequeridos = form.querySelectorAll("[required]");

    for (const campo of camposRequeridos) {
      const esArchivo = campo.type === "file";
      const tieneValor = esArchivo ? Boolean(campo.files && campo.files.length > 0) : String(campo.value || "").trim() !== "";

      if (!tieneValor) {
        const etiqueta = obtenerEtiquetaCampo(campo);
        marcarCampoFaltante(campo);
        campo.focus();
        campo.scrollIntoView({ behavior: "smooth", block: "center" });
        throw new Error(`Falta completar: ${etiqueta}.`);
      }
    }

    if (form.id === "form-informe") {
      const filas = Array.from(document.querySelectorAll("#lista-actividades .actividad-row"));
      const actividades = filas
        .map((row) => row.querySelector("textarea")?.value.trim() || "")
        .filter(Boolean);

      if (actividades.length === 0) {
        filas.forEach((row) => {
          row.classList.add("invalid");
          if (!row.querySelector(".field-error-marker")) {
            const marcador = document.createElement("span");
            marcador.className = "field-error-marker";
            marcador.textContent = "?";
            marcador.setAttribute("title", "Debes escribir al menos una actividad");
            row.appendChild(marcador);
          }
        });

        const primeraFila = filas[0];
        const primerTextarea = primeraFila?.querySelector("textarea");
        if (primerTextarea) {
          primerTextarea.focus();
          primerTextarea.scrollIntoView({ behavior: "smooth", block: "center" });
        }

        const bloque = document.getElementById("lista-actividades");
        bloque.classList.add("invalid");
        throw new Error("Debes escribir al menos una actividad antes de generar el informe.");
      }

      if (archivosEvidencia.length === 0) {
        const dropzoneEvidencias = document.getElementById("inf-evidencias").closest(".dropzone");
        if (dropzoneEvidencias) {
          dropzoneEvidencias.classList.add("invalid");
          if (!dropzoneEvidencias.querySelector(".field-error-marker")) {
            const marcador = document.createElement("span");
            marcador.className = "field-error-marker";
            marcador.textContent = "?";
            marcador.setAttribute("title", "Debes seleccionar al menos una evidencia");
            dropzoneEvidencias.appendChild(marcador);
          }
        }
        throw new Error("Debes seleccionar al menos una foto de evidencia.");
      }
    }

    return true;
  }

  btnCerrarOverlay.addEventListener("click", () => {
    overlay.classList.remove("active");
  });

  /**
   * Envía un FormData al endpoint indicado y maneja la respuesta.
   * El backend debe devolver el PDF como body (Content-Type: application/pdf)
   * sin guardarlo en disco — se descarga directamente desde el blob en memoria.
   *
   * Endpoints esperados (FastAPI):
   *   POST /api/declaracion-jurada
   *   POST /api/reporte-asistencia
   *   POST /api/informe-actividades
   */
  async function enviarFormulario(endpoint, formData, nombreArchivoSalida) {
    abrirOverlay();
    try {
      const respuesta = await fetch(endpoint, { method: "POST", body: formData });

      if (!respuesta.ok) {
        let msjError = `Error del servidor (${respuesta.status})`;
        try {
          const errData = await respuesta.json();
          if (errData && errData.detail) {
            msjError = errData.detail;
          }
        } catch (_) {}
        throw new Error(msjError);
      }

      const blob = await respuesta.blob();
      const url  = URL.createObjectURL(blob);
      const disposition = respuesta.headers.get("Content-Disposition") || "";
      const nombreServidor = disposition.match(/filename=([^;]+)/i);
      const nombreArchivo = nombreServidor
        ? nombreServidor[1].trim().replace(/^['"]|['"]$/g, "")
        : nombreArchivoSalida;
      mostrarExito(url, nombreArchivo);

    } catch (err) {
      mostrarError(err.message || "Revisa tu conexión e inténtalo nuevamente.");
      console.error("Error al generar el documento:", err);
    }
  }

  /* ============================================================
   * 7. LISTENERS DE FORMULARIOS → ENDPOINTS DE LA API
   * ============================================================ */

  // --- Declaración Jurada ---
  const formDeclaracion = document.getElementById("form-declaracion");
  if (formDeclaracion) {
    formDeclaracion.addEventListener("submit", (e) => {
      e.preventDefault();
      try {
        validarFormulario(e.target);
        guardarPerfilDesdeFormulario(e.target);
        enviarFormulario("/api/declaracion-jurada", new FormData(e.target), "declaracion_jurada.pdf");
      } catch (err) {
        mostrarError(err.message || "Completa todos los campos requeridos.");
      }
    });
  }

  // --- Reporte de Asistencia ---
  const formAsistencia = document.getElementById("form-asistencia");
  if (formAsistencia) {
    formAsistencia.addEventListener("submit", (e) => {
      e.preventDefault();
      try {
        validarFormulario(e.target);
        enviarFormulario("/api/reporte-asistencia", new FormData(e.target), "reporte_asistencia.pdf");
      } catch (err) {
        mostrarError(err.message || "Completa todos los campos requeridos.");
      }
    });
  }

  // --- Informe de Actividades ---
  const formInforme = document.getElementById("form-informe");
  if (formInforme) {
    formInforme.addEventListener("submit", (e) => {
      e.preventDefault();
      try {
        validarFormulario(e.target);
        const formData = new FormData(e.target);

        // Actividades: una por línea (compatible con pdf_generator.py que hace split("\n"))
        const textos = Array.from(document.querySelectorAll("#lista-actividades textarea"))
          .map((t) => t.value.trim())
          .filter(Boolean);
        formData.append("actividades", textos.join("\n"));

        // Evidencias gestionadas manualmente (array propio, no el input directamente)
        archivosEvidencia.forEach((file) => formData.append("evidencias", file));

        guardarPerfilDesdeFormulario(e.target);
        enviarFormulario("/api/informe-actividades", formData, "informe_actividades.pdf");
      } catch (err) {
        mostrarError(err.message || "Completa todos los campos requeridos.");
      }
    });
  }

  /* ============================================================
   * 8. AUTOLLENADO DE PERFIL VÍA localStorage
   *    Campos compartidos entre formularios: nombres, apellidos, DNI, etc.
   *    Se guardan al enviar y se restauran al cargar la página.
   * ============================================================ */
  const PERFIL_KEY = "bolsista_perfil_v1";

  /** Campos que se persisten (atributo name del input como clave). */
  const CAMPOS_PERFIL = [
    "ap_paterno", "ap_materno", "nombres", "dni",
    "domicilio",  "distrito",   "telefono", "email",
    "condicion",  "facultad",
    // Informe
    "para_nombre", "para_cargo", "de_nombre", "fecha_inicio",
  ];

  function cargarPerfil() {
    try {
      const raw = localStorage.getItem(PERFIL_KEY);
      if (!raw) return;
      const perfil = JSON.parse(raw);

      CAMPOS_PERFIL.forEach((nombre) => {
        if (!perfil[nombre]) return;
        document.querySelectorAll(`[name="${nombre}"]`).forEach((el) => {
          if (el.tagName === "SELECT") {
            el.value = perfil[nombre];
          } else if (el.type !== "file" && el.type !== "date") {
            el.value = perfil[nombre];
          }
        });
      });
    } catch (_) {
      // localStorage puede no estar disponible en contextos privados
    }
  }

  function guardarPerfilDesdeFormulario(form) {
    try {
      const raw    = localStorage.getItem(PERFIL_KEY);
      const perfil = raw ? JSON.parse(raw) : {};
      const data   = new FormData(form);

      CAMPOS_PERFIL.forEach((nombre) => {
        const valor = data.get(nombre);
        if (valor) perfil[nombre] = valor;
      });

      localStorage.setItem(PERFIL_KEY, JSON.stringify(perfil));
    } catch (_) { /* silencioso */ }
  }

  // Cargar perfil al iniciar
  cargarPerfil();

})();
