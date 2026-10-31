/**
 * Gestor de Estatus de Solicitudes (Panel Administrativo)
 * Enfoque Orientado a Objetos: cambios inmediatos de estado mediante API REST (PATCH),
 * filtros combinados, métricas en vivo y actualización del DOM sin recargar la página.
 */

class EstatusAdmin {
    constructor() {
        this.paginaActual = 1;
        this.solicitudes = [];
        this.totalSolicitudes = 0;
        this.totalPaginas = 1;

        // Referencias del DOM
        this.formFiltros = document.getElementById("formFiltros");
        this.fCurp = document.getElementById("fCurp");
        this.fNombre = document.getElementById("fNombre");
        this.fFolio = document.getElementById("fFolio");
        this.fMunicipio = document.getElementById("fMunicipio");
        this.fEstatus = document.getElementById("fEstatus");
        this.btnLimpiar = document.getElementById("btnLimpiar");

        this.tbody = document.getElementById("tbodyEstatus");
        this.conteoRegistros = document.getElementById("conteoRegistros");
        this.alertaBox = document.getElementById("mensajeAlerta");

        this.btnPrev = document.getElementById("btnPrev");
        this.btnNext = document.getElementById("btnNext");
        this.infoPagina = document.getElementById("infoPagina");

        // Métricas
        this.statTotal = document.getElementById("statTotal");
        this.statPendientes = document.getElementById("statPendientes");
        this.statResueltos = document.getElementById("statResueltos");

        this.timeoutAlerta = null;
        this.timeoutDebounce = null;
    }

    inicializar() {
        if (!this.tbody) return;

        // Cargar municipios en el filtro
        this.cargarMunicipiosFiltro();

        // Enlazar eventos de filtros
        this.formFiltros.addEventListener("submit", (e) => {
            e.preventDefault();
            this.paginaActual = 1;
            this.cargarSolicitudes();
        });

        this.btnLimpiar.addEventListener("click", () => {
            this.formFiltros.reset();
            this.paginaActual = 1;
            this.cargarSolicitudes();
        });

        // Filtro en tiempo real con debounce
        [this.fCurp, this.fNombre, this.fFolio].forEach((input) => {
            input.addEventListener("input", () => {
                clearTimeout(this.timeoutDebounce);
                this.timeoutDebounce = setTimeout(() => {
                    this.paginaActual = 1;
                    this.cargarSolicitudes();
                }, 350);
            });
        });

        [this.fMunicipio, this.fEstatus].forEach((select) => {
            select.addEventListener("change", () => {
                this.paginaActual = 1;
                this.cargarSolicitudes();
            });
        });

        // Paginación
        this.btnPrev.addEventListener("click", () => {
            if (this.paginaActual > 1) {
                this.paginaActual--;
                this.cargarSolicitudes();
            }
        });

        this.btnNext.addEventListener("click", () => {
            if (this.paginaActual < this.totalPaginas) {
                this.paginaActual++;
                this.cargarSolicitudes();
            }
        });

        // Carga inicial
        this.cargarSolicitudes();
    }

    mostrarMensaje(texto, tipo = "exito") {
        if (!this.alertaBox) return;

        if (this.timeoutAlerta) {
            clearTimeout(this.timeoutAlerta);
        }

        this.alertaBox.textContent = texto;
        this.alertaBox.className = `mensaje-alerta visible ${tipo}`;
        this.alertaBox.hidden = false;

        this.timeoutAlerta = setTimeout(() => {
            this.alertaBox.hidden = true;
            this.alertaBox.className = "mensaje-alerta";
        }, 4500);
    }

    async cargarMunicipiosFiltro() {
        try {
            const municipios = await ApiService.get("/api/municipios");
            municipios.forEach((m) => {
                const opt = document.createElement("option");
                opt.value = m.nombre;
                opt.textContent = m.nombre;
                this.fMunicipio.appendChild(opt);
            });
        } catch (error) {
            console.error("No se pudieron cargar los municipios para el filtro:", error);
        }
    }

    construirParams() {
        const params = new URLSearchParams();
        params.set("pagina", this.paginaActual);

        const curp = (this.fCurp.value || "").trim();
        const nombre = (this.fNombre.value || "").trim();
        const folio = (this.fFolio.value || "").trim();
        const municipio = this.fMunicipio.value;
        const estatus = this.fEstatus.value;

        if (curp) params.set("curp", curp);
        if (nombre) params.set("nombre", nombre);
        if (folio) params.set("folio", folio);
        if (municipio) params.set("municipio", municipio);
        if (estatus) params.set("estatus", estatus);

        return params.toString();
    }

    async cargarSolicitudes() {
        this.tbody.innerHTML = `
            <tr>
                <td colspan="8" class="texto-cargando">Cargando solicitudes...</td>
            </tr>
        `;

        try {
            const query = this.construirParams();
            const data = await ApiService.get(`/api/admin/solicitudes?${query}`);

            this.solicitudes = data.solicitudes || [];
            this.totalSolicitudes = data.total || 0;
            this.paginaActual = data.pagina || 1;
            this.totalPaginas = data.paginas || 1;

            this.actualizarMetricas();
            this.renderizar();
        } catch (error) {
            console.error("Error al cargar solicitudes:", error);
            if (/autorizado/i.test(error.message)) {
                window.location.href = "/admin/login";
                return;
            }
            this.tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="texto-error">
                        Error al cargar las solicitudes: ${this.escaparHtml(error.message)}
                    </td>
                </tr>
            `;
            this.conteoRegistros.textContent = "Error de carga";
        }
    }

    actualizarMetricas() {
        // Métricas de la página actual o acumulado
        const pendientes = this.solicitudes.filter((s) => s.estatus === "Pendiente").length;
        const resueltos = this.solicitudes.filter((s) => s.estatus === "Resuelto").length;

        this.statTotal.textContent = this.totalSolicitudes;
        this.statPendientes.textContent = pendientes;
        this.statResueltos.textContent = resueltos;

        this.infoPagina.textContent = `Página ${this.paginaActual} de ${this.totalPaginas}`;
        this.conteoRegistros.textContent = `Mostrando ${this.solicitudes.length} de ${this.totalSolicitudes} solicitud(es) registrada(s)`;

        this.btnPrev.disabled = this.paginaActual <= 1;
        this.btnNext.disabled = this.paginaActual >= this.totalPaginas;
    }

    renderizar() {
        if (this.solicitudes.length === 0) {
            this.tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="texto-vacio">
                        No se encontraron solicitudes con los criterios de búsqueda seleccionados.
                    </td>
                </tr>
            `;
            return;
        }

        const fragmento = document.createDocumentFragment();

        this.solicitudes.forEach((s) => {
            const tr = document.createElement("tr");
            tr.id = `fila-solicitud-${s.id}`;

            const esResuelto = s.estatus === "Resuelto";
            const claseChip = esResuelto ? "resuelto" : "pendiente";
            const siguienteEstatus = esResuelto ? "Pendiente" : "Resuelto";
            const btnClase = esResuelto ? "btn-marcar-pendiente" : "btn-marcar-resuelto";
            const btnIcono = esResuelto ? "↩ Marcar Pendiente" : "✓ Marcar Resuelto";

            tr.innerHTML = `
                <td class="col-folio"><strong>${this.escaparHtml(s.folio)}</strong></td>
                <td class="col-turno text-center">
                    <span class="badge-turno">${s.numero_turno}</span>
                </td>
                <td class="col-nombre">
                    <strong>${this.escaparHtml(s.nombre)}</strong>
                </td>
                <td class="col-curp"><code>${this.escaparHtml(s.curp)}</code></td>
                <td class="col-municipio">${this.escaparHtml(s.municipio)}</td>
                <td class="col-asunto">${this.escaparHtml(s.asunto)}</td>
                <td class="col-estatus text-center" id="celda-chip-${s.id}">
                    <span class="badge-estatus-chip ${claseChip}" id="chip-estatus-${s.id}">
                        <span class="badge-dot"></span>
                        <span class="chip-texto">${this.escaparHtml(s.estatus)}</span>
                    </span>
                </td>
                <td class="col-acciones text-center" id="celda-accion-${s.id}">
                    <button
                        type="button"
                        class="btn-toggle-estatus ${btnClase}"
                        id="btn-cambiar-${s.id}"
                        data-id="${s.id}"
                        data-siguiente="${siguienteEstatus}"
                    >
                        ${btnIcono}
                    </button>
                </td>
            `;

            fragmento.appendChild(tr);
        });

        this.tbody.replaceChildren(fragmento);
        this.enlazarBotonesAccion();
    }

    enlazarBotonesAccion() {
        this.tbody.querySelectorAll(".btn-toggle-estatus").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = parseInt(btn.getAttribute("data-id"), 10);
                const nuevoEstatus = btn.getAttribute("data-siguiente");
                this.cambiarEstatus(id, nuevoEstatus);
            });
        });
    }

    async cambiarEstatus(id, nuevoEstatus) {
        const btn = document.getElementById(`btn-cambiar-${id}`);
        const chip = document.getElementById(`chip-estatus-${id}`);
        const fila = document.getElementById(`fila-solicitud-${id}`);

        if (btn) {
            btn.disabled = true;
            btn.textContent = "Actualizando...";
        }

        try {
            // Petición REST PATCH protegida (con token CSRF automático vía ApiService)
            const respuesta = await ApiService.patch(`/api/admin/solicitudes/${id}/estatus`, {
                estatus: nuevoEstatus,
            });

            // 1. Actualizar el registro en memoria local
            const sol = this.solicitudes.find((s) => s.id === id);
            if (sol) {
                sol.estatus = respuesta.solicitud.estatus;
            }

            // 2. Actualizar el DOM directamente SIN recargar la página completa
            const esResuelto = respuesta.solicitud.estatus === "Resuelto";
            const siguienteEstatus = esResuelto ? "Pendiente" : "Resuelto";

            if (chip) {
                chip.className = `badge-estatus-chip ${esResuelto ? "resuelto" : "pendiente"}`;
                chip.querySelector(".chip-texto").textContent = respuesta.solicitud.estatus;
            }

            if (btn) {
                btn.disabled = false;
                btn.className = `btn-toggle-estatus ${esResuelto ? "btn-marcar-pendiente" : "btn-marcar-resuelto"}`;
                btn.setAttribute("data-siguiente", siguienteEstatus);
                btn.innerHTML = esResuelto ? "↩ Marcar Pendiente" : "✓ Marcar Resuelto";
            }

            // 3. Efecto visual de fila actualizada
            if (fila) {
                fila.classList.remove("fila-actualizada");
                void fila.offsetWidth; // Forzar reflujo CSS
                fila.classList.add("fila-actualizada");
            }

            // 4. Actualizar contadores
            this.actualizarMetricas();

            // 5. Mostrar feedback visual
            this.mostrarMensaje(
                `Solicitud ${respuesta.solicitud.folio}: estatus cambiado a "${respuesta.solicitud.estatus}".`,
                "exito"
            );
        } catch (error) {
            console.error(`Error al actualizar estatus de solicitud ${id}:`, error);
            this.mostrarMensaje(
                error.message || "No se pudo actualizar el estatus de la solicitud.",
                "error"
            );
            if (btn) {
                btn.disabled = false;
                const esResueltoActual = chip && chip.classList.contains("resuelto");
                btn.innerHTML = esResueltoActual ? "↩ Marcar Pendiente" : "✓ Marcar Resuelto";
            }
        }
    }

    escaparHtml(cadena) {
        if (!cadena) return "";
        const div = document.createElement("div");
        div.textContent = cadena;
        return div.innerHTML;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const adminEstatus = new EstatusAdmin();
    adminEstatus.inicializar();
});
