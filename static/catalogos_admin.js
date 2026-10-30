/**
 * Gestión Orientada a Objetos para Catálogos Administrativos (Niveles Educativos y Asuntos).
 * Componente modular con soporte para múltiples instancias, pestañas y edición en la misma fila (inline edit).
 */

class CatalogoModulo {
    constructor(config) {
        this.nombre = config.nombre; // Ej: 'nivel', 'asunto'
        this.endpoint = config.endpoint; // Ej: '/api/admin/niveles'
        this.idTbody = config.idTbody;
        this.idForm = config.idForm;
        this.idInputNuevo = config.idInputNuevo;
        this.idBtnCrear = config.idBtnCrear;
        this.idBuscar = config.idBuscar;
        this.idFiltro = config.idFiltro;
        this.idConteo = config.idConteo;
        this.onMensaje = config.onMensaje; // Función para disparar alertas globales

        this.items = [];
        this.editandoId = null;

        // Referencias del DOM
        this.tbody = document.getElementById(this.idTbody);
        this.form = document.getElementById(this.idForm);
        this.inputNuevo = document.getElementById(this.idInputNuevo);
        this.btnCrear = document.getElementById(this.idBtnCrear);
        this.inputBuscar = document.getElementById(this.idBuscar);
        this.selectFiltro = document.getElementById(this.idFiltro);
        this.conteoLabel = document.getElementById(this.idConteo);
    }

    inicializar() {
        if (!this.tbody) return;

        this.form.addEventListener("submit", (e) => this.manejarCrear(e));
        this.inputBuscar.addEventListener("input", () => this.renderizar());
        this.selectFiltro.addEventListener("change", () => this.renderizar());

        this.cargarDatos();
    }

    async cargarDatos() {
        this.tbody.innerHTML = `
            <tr>
                <td colspan="4" class="texto-cargando">Cargando registros...</td>
            </tr>
        `;

        try {
            this.items = await ApiService.get(this.endpoint);
            this.renderizar();
        } catch (error) {
            console.error(`Error al cargar ${this.nombre}:`, error);
            this.tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="texto-error">
                        No se pudieron cargar los registros. ${this.escaparHtml(error.message)}
                    </td>
                </tr>
            `;
            if (this.conteoLabel) this.conteoLabel.textContent = "Error al cargar";
        }
    }

    obtenerFiltrados() {
        const busqueda = (this.inputBuscar.value || "").trim().toLowerCase();
        const filtro = this.selectFiltro.value;

        return this.items.filter((item) => {
            const coincideNombre = item.nombre.toLowerCase().includes(busqueda);
            let coincideEstado = true;

            if (filtro === "activos") {
                coincideEstado = item.activo === true;
            } else if (filtro === "inactivos") {
                coincideEstado = item.activo === false;
            }

            return coincideNombre && coincideEstado;
        });
    }

    renderizar() {
        const filtrados = this.obtenerFiltrados();
        const total = this.items.length;

        if (this.conteoLabel) {
            this.conteoLabel.textContent = `Mostrando ${filtrados.length} de ${total} registros`;
        }

        if (filtrados.length === 0) {
            this.tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="texto-vacio">
                        No se encontraron registros con los filtros aplicados.
                    </td>
                </tr>
            `;
            return;
        }

        const fragmento = document.createDocumentFragment();

        filtrados.forEach((item) => {
            const tr = document.createElement("tr");
            tr.id = `fila-${this.nombre}-${item.id}`;
            if (!item.activo) {
                tr.classList.add("fila-inactiva");
            }

            const estaEditando = this.editandoId === item.id;

            if (estaEditando) {
                tr.classList.add("fila-en-edicion");
                tr.innerHTML = `
                    <td class="col-id">${item.id}</td>
                    <td class="col-nombre">
                        <div class="inline-edit-container">
                            <input
                                type="text"
                                id="inputEdit-${this.nombre}-${item.id}"
                                class="input-inline-edit"
                                value="${this.escaparHtml(item.nombre)}"
                                autocomplete="off"
                            >
                        </div>
                    </td>
                    <td class="col-estado text-center">
                        <span class="badge-estado ${item.activo ? 'badge-activo' : 'badge-inactivo'}">
                            ${item.activo ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td class="col-acciones text-center">
                        <div class="acciones-inline">
                            <button
                                type="button"
                                class="btn-accion btn-guardar"
                                data-id="${item.id}"
                                title="Guardar cambios"
                            >
                                Guardar
                            </button>
                            <button
                                type="button"
                                class="btn-accion btn-cancelar"
                                data-id="${item.id}"
                                title="Cancelar edición"
                            >
                                Cancelar
                            </button>
                        </div>
                    </td>
                `;
            } else {
                tr.innerHTML = `
                    <td class="col-id">${item.id}</td>
                    <td class="col-nombre">
                        <span class="nombre-municipio">${this.escaparHtml(item.nombre)}</span>
                    </td>
                    <td class="col-estado text-center">
                        <span class="badge-estado ${item.activo ? 'badge-activo' : 'badge-inactivo'}">
                            ${item.activo ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td class="col-acciones text-center">
                        <div class="acciones-inline">
                            <button
                                type="button"
                                class="btn-accion btn-editar"
                                data-id="${item.id}"
                            >
                                Editar
                            </button>
                            <button
                                type="button"
                                class="btn-accion ${item.activo ? 'btn-desactivar' : 'btn-activar'}"
                                data-id="${item.id}"
                                data-activo="${item.activo}"
                            >
                                ${item.activo ? 'Desactivar' : 'Activar'}
                            </button>
                        </div>
                    </td>
                `;
            }

            fragmento.appendChild(tr);
        });

        this.tbody.replaceChildren(fragmento);
        this.enlazarEventosTabla();

        if (this.editandoId !== null) {
            const inputEdit = document.getElementById(`inputEdit-${this.nombre}-${this.editandoId}`);
            if (inputEdit) {
                inputEdit.focus();
                inputEdit.select();
                inputEdit.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") {
                        e.preventDefault();
                        this.guardarEdicionInline(this.editandoId);
                    } else if (e.key === "Escape") {
                        e.preventDefault();
                        this.cancelarEdicionInline();
                    }
                });
            }
        }
    }

    enlazarEventosTabla() {
        this.tbody.querySelectorAll(".btn-editar").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = parseInt(btn.getAttribute("data-id"), 10);
                this.activarEdicionInline(id);
            });
        });

        this.tbody.querySelectorAll(".btn-cancelar").forEach((btn) => {
            btn.addEventListener("click", () => {
                this.cancelarEdicionInline();
            });
        });

        this.tbody.querySelectorAll(".btn-guardar").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = parseInt(btn.getAttribute("data-id"), 10);
                this.guardarEdicionInline(id);
            });
        });

        this.tbody.querySelectorAll(".btn-desactivar, .btn-activar").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = parseInt(btn.getAttribute("data-id"), 10);
                const activoActual = btn.getAttribute("data-activo") === "true";
                this.alternarEstado(id, !activoActual);
            });
        });
    }

    activarEdicionInline(id) {
        this.editandoId = id;
        this.renderizar();
    }

    cancelarEdicionInline() {
        this.editandoId = null;
        this.renderizar();
    }

    async guardarEdicionInline(id) {
        const input = document.getElementById(`inputEdit-${this.nombre}-${id}`);
        if (!input) return;

        const nuevoNombre = input.value.trim();
        if (!nuevoNombre) {
            this.onMensaje(`El nombre de ${this.nombre} no puede estar vacío.`, "error");
            input.focus();
            return;
        }

        const btnGuardar = this.tbody.querySelector(`.btn-guardar[data-id="${id}"]`);
        if (btnGuardar) {
            btnGuardar.disabled = true;
            btnGuardar.textContent = "Guardando...";
        }

        try {
            const respuesta = await ApiService.put(`${this.endpoint}/${id}`, {
                nombre: nuevoNombre,
            });

            const index = this.items.findIndex((item) => item.id === id);
            if (index !== -1) {
                this.items[index] = respuesta.registro;
            }

            this.editandoId = null;
            this.onMensaje(respuesta.mensaje || "Registro actualizado correctamente.", "exito");
            this.renderizar();
        } catch (error) {
            console.error(`Error al actualizar ${this.nombre}:`, error);
            this.onMensaje(error.message || `No se pudo actualizar el registro.`, "error");
            if (btnGuardar) {
                btnGuardar.disabled = false;
                btnGuardar.textContent = "Guardar";
            }
        }
    }

    async alternarEstado(id, nuevoEstado) {
        const item = this.items.find((i) => i.id === id);
        const nombre = item ? item.nombre : "este elemento";

        if (!nuevoEstado) {
            const confirmar = confirm(
                `¿Desea desactivar "${nombre}"?\n\n` +
                "Ya no aparecerá como opción disponible en los formularios públicos.\n" +
                "Las solicitudes anteriores conservarán su referencia histórica sin cambios."
            );
            if (!confirmar) return;
        }

        try {
            const respuesta = await ApiService.patch(`${this.endpoint}/${id}/estado`, {
                activo: nuevoEstado,
            });

            const index = this.items.findIndex((i) => i.id === id);
            if (index !== -1) {
                this.items[index] = respuesta.registro;
            }

            this.onMensaje(respuesta.mensaje || "Estado actualizado con éxito.", "exito");
            this.renderizar();
        } catch (error) {
            console.error(`Error al alternar estado en ${this.nombre}:`, error);
            this.onMensaje(error.message || "No se pudo cambiar el estado.", "error");
        }
    }

    async manejarCrear(evento) {
        evento.preventDefault();
        const nombre = this.inputNuevo.value.trim();

        if (!nombre) {
            this.onMensaje(`Ingrese el nombre para ${this.nombre}.`, "error");
            this.inputNuevo.focus();
            return;
        }

        this.btnCrear.disabled = true;
        const textoOriginal = this.btnCrear.innerHTML;
        this.btnCrear.innerHTML = "Guardando...";

        try {
            const respuesta = await ApiService.post(this.endpoint, { nombre });

            this.items.push(respuesta.registro);
            this.items.sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

            this.inputNuevo.value = "";
            this.onMensaje(respuesta.mensaje || "Registrado correctamente.", "exito");

            if (this.selectFiltro.value === "inactivos") {
                this.selectFiltro.value = "activos";
            }

            this.renderizar();
        } catch (error) {
            console.error(`Error al registrar en ${this.nombre}:`, error);
            this.onMensaje(error.message || "No se pudo registrar.", "error");
        } finally {
            this.btnCrear.disabled = false;
            this.btnCrear.innerHTML = textoOriginal;
        }
    }

    escaparHtml(cadena) {
        if (!cadena) return "";
        const div = document.createElement("div");
        div.textContent = cadena;
        return div.innerHTML;
    }
}

/**
 * Gestor Maestro de la pantalla de Catálogos (Tabs y Alertas)
 */
class CatalogosAdmin {
    constructor() {
        this.alertaBox = document.getElementById("mensajeAlerta");
        this.timeoutAlerta = null;
        this.tabBtns = document.querySelectorAll(".tab-btn");
        this.tabPanels = document.querySelectorAll(".tab-panel");

        this.moduloNiveles = new CatalogoModulo({
            nombre: "nivel educativo",
            endpoint: "/api/admin/niveles",
            idTbody: "tbodyNiveles",
            idForm: "formCrearNivel",
            idInputNuevo: "nuevoNombreNivel",
            idBtnCrear: "btnCrearNivel",
            idBuscar: "inputBuscarNiveles",
            idFiltro: "selectFiltroNiveles",
            idConteo: "conteoNiveles",
            onMensaje: (texto, tipo) => this.mostrarMensaje(texto, tipo),
        });

        this.moduloAsuntos = new CatalogoModulo({
            nombre: "asunto",
            endpoint: "/api/admin/asuntos",
            idTbody: "tbodyAsuntos",
            idForm: "formCrearAsunto",
            idInputNuevo: "nuevoNombreAsunto",
            idBtnCrear: "btnCrearAsunto",
            idBuscar: "inputBuscarAsuntos",
            idFiltro: "selectFiltroAsuntos",
            idConteo: "conteoAsuntos",
            onMensaje: (texto, tipo) => this.mostrarMensaje(texto, tipo),
        });
    }

    inicializar() {
        this.enlazarTabs();
        this.moduloNiveles.inicializar();
        this.moduloAsuntos.inicializar();

        // Si la URL trae #asuntos, activar esa pestaña de inmediato
        if (window.location.hash === "#asuntos") {
            this.activarTab("asuntos");
        }
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
        }, 5000);
    }

    enlazarTabs() {
        this.tabBtns.forEach((btn) => {
            btn.addEventListener("click", () => {
                const tab = btn.getAttribute("data-tab");
                this.activarTab(tab);
            });
        });
    }

    activarTab(nombreTab) {
        this.tabBtns.forEach((b) => {
            b.classList.toggle("active", b.getAttribute("data-tab") === nombreTab);
        });

        this.tabPanels.forEach((panel) => {
            const esActivo = panel.id === (nombreTab === "asuntos" ? "panelAsuntos" : "panelNiveles");
            panel.classList.toggle("active", esActivo);
        });

        window.history.replaceState(null, null, `#${nombreTab}`);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const admin = new CatalogosAdmin();
    admin.inicializar();
});
