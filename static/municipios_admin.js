/**
 * Gestión del Catálogo de Municipios (Panel Administrativo)
 * Enfoque Orientado a Objetos con soporte para edición en la misma fila (inline).
 */

class MunicipiosAdmin {
    constructor() {
        this.municipios = [];
        this.editandoId = null;

        // Elementos del DOM
        this.tbody = document.getElementById("tbodyMunicipios");
        this.formCrear = document.getElementById("formCrearMunicipio");
        this.inputNuevoNombre = document.getElementById("nuevoNombreMunicipio");
        this.btnCrear = document.getElementById("btnCrearMunicipio");
        this.inputBuscar = document.getElementById("inputBuscar");
        this.selectFiltro = document.getElementById("selectFiltroEstado");
        this.conteoLabel = document.getElementById("conteoMunicipios");
        this.alertaBox = document.getElementById("mensajeAlerta");

        this.timeoutAlerta = null;
    }

    inicializar() {
        if (!this.tbody) return;

        // Eventos
        this.formCrear.addEventListener("submit", (e) => this.manejarCrear(e));
        this.inputBuscar.addEventListener("input", () => this.renderizar());
        this.selectFiltro.addEventListener("change", () => this.renderizar());

        // Carga inicial de datos
        this.cargarMunicipios();
    }

    mostrarMensaje(texto, tipo = "exito") {
        if (!this.alertaBox) return;

        if (this.timeoutAlerta) {
            clearTimeout(this.timeoutAlerta);
        }

        this.alertaBox.textContent = texto;
        this.alertaBox.className = `mensaje-alerta visible ${tipo}`;
        this.alertaBox.hidden = false;

        // Ocultar automáticamente tras 5 segundos
        this.timeoutAlerta = setTimeout(() => {
            this.alertaBox.hidden = true;
            this.alertaBox.className = "mensaje-alerta";
        }, 5000);
    }

    async cargarMunicipios() {
        this.tbody.innerHTML = `
            <tr>
                <td colspan="5" class="texto-cargando">Cargando municipios...</td>
            </tr>
        `;

        try {
            this.municipios = await ApiService.get("/api/admin/municipios");
            this.renderizar();
        } catch (error) {
            console.error("Error al cargar municipios:", error);
            this.tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="texto-error">
                        No se pudieron cargar los municipios. ${this.escaparHtml(error.message)}
                    </td>
                </tr>
            `;
            this.conteoLabel.textContent = "Error al cargar";
        }
    }

    obtenerFiltrados() {
        const busqueda = (this.inputBuscar.value || "").trim().toLowerCase();
        const filtroEstado = this.selectFiltro.value;

        return this.municipios.filter((m) => {
            const coincideNombre = m.nombre.toLowerCase().includes(busqueda);
            let coincideEstado = true;

            if (filtroEstado === "activos") {
                coincideEstado = m.activo === true;
            } else if (filtroEstado === "inactivos") {
                coincideEstado = m.activo === false;
            }

            return coincideNombre && coincideEstado;
        });
    }

    renderizar() {
        const filtrados = this.obtenerFiltrados();
        const total = this.municipios.length;

        this.conteoLabel.textContent = `Mostrando ${filtrados.length} de ${total} municipios`;

        if (filtrados.length === 0) {
            this.tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="texto-vacio">
                        No se encontraron municipios con los filtros aplicados.
                    </td>
                </tr>
            `;
            return;
        }

        const fragmento = document.createDocumentFragment();

        filtrados.forEach((m) => {
            const tr = document.createElement("tr");
            tr.id = `fila-municipio-${m.id_municipio}`;
            if (!m.activo) {
                tr.classList.add("fila-inactiva");
            }

            const estaEditando = this.editandoId === m.id_municipio;

            if (estaEditando) {
                tr.classList.add("fila-en-edicion");
                tr.innerHTML = `
                    <td class="col-id">${m.id_municipio}</td>
                    <td class="col-nombre">
                        <div class="inline-edit-container">
                            <input
                                type="text"
                                id="inputEdit-${m.id_municipio}"
                                class="input-inline-edit"
                                value="${this.escaparHtml(m.nombre)}"
                                maxlength="100"
                                autocomplete="off"
                            >
                        </div>
                    </td>
                    <td class="col-turno text-center">
                        <span class="badge-turno">${m.ultimo_turno}</span>
                    </td>
                    <td class="col-estado text-center">
                        <span class="badge-estado ${m.activo ? 'badge-activo' : 'badge-inactivo'}">
                            ${m.activo ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td class="col-acciones text-center">
                        <div class="acciones-inline">
                            <button
                                type="button"
                                class="btn-accion btn-guardar"
                                data-id="${m.id_municipio}"
                                title="Guardar cambios"
                            >
                                Guardar
                            </button>
                            <button
                                type="button"
                                class="btn-accion btn-cancelar"
                                data-id="${m.id_municipio}"
                                title="Cancelar edición"
                            >
                                Cancelar
                            </button>
                        </div>
                    </td>
                `;
            } else {
                tr.innerHTML = `
                    <td class="col-id">${m.id_municipio}</td>
                    <td class="col-nombre">
                        <span class="nombre-municipio">${this.escaparHtml(m.nombre)}</span>
                    </td>
                    <td class="col-turno text-center">
                        <span class="badge-turno" title="Turnos consecutivos asignados">${m.ultimo_turno}</span>
                    </td>
                    <td class="col-estado text-center">
                        <span class="badge-estado ${m.activo ? 'badge-activo' : 'badge-inactivo'}">
                            ${m.activo ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td class="col-acciones text-center">
                        <div class="acciones-inline">
                            <button
                                type="button"
                                class="btn-accion btn-editar"
                                data-id="${m.id_municipio}"
                            >
                                Editar
                            </button>
                            <button
                                type="button"
                                class="btn-accion ${m.activo ? 'btn-desactivar' : 'btn-activar'}"
                                data-id="${m.id_municipio}"
                                data-activo="${m.activo}"
                            >
                                ${m.activo ? 'Desactivar' : 'Activar'}
                            </button>
                        </div>
                    </td>
                `;
            }

            fragmento.appendChild(tr);
        });

        this.tbody.replaceChildren(fragmento);
        this.enlazarEventosTabla();

        // Si hay una fila en edición, enfocar el input
        if (this.editandoId !== null) {
            const inputEdit = document.getElementById(`inputEdit-${this.editandoId}`);
            if (inputEdit) {
                inputEdit.focus();
                inputEdit.select();
                // Permitir guardar con Enter y cancelar con Escape
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
        // Botones de editar
        this.tbody.querySelectorAll(".btn-editar").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = parseInt(btn.getAttribute("data-id"), 10);
                this.activarEdicionInline(id);
            });
        });

        // Botones de cancelar
        this.tbody.querySelectorAll(".btn-cancelar").forEach((btn) => {
            btn.addEventListener("click", () => {
                this.cancelarEdicionInline();
            });
        });

        // Botones de guardar
        this.tbody.querySelectorAll(".btn-guardar").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = parseInt(btn.getAttribute("data-id"), 10);
                this.guardarEdicionInline(id);
            });
        });

        // Botones de activar / desactivar
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
        const input = document.getElementById(`inputEdit-${id}`);
        if (!input) return;

        const nuevoNombre = input.value.trim();
        if (!nuevoNombre) {
            this.mostrarMensaje("El nombre del municipio no puede estar vacío.", "error");
            input.focus();
            return;
        }

        const btnGuardar = this.tbody.querySelector(`.btn-guardar[data-id="${id}"]`);
        if (btnGuardar) {
            btnGuardar.disabled = true;
            btnGuardar.textContent = "Guardando...";
        }

        try {
            const respuesta = await ApiService.put(`/api/admin/municipios/${id}`, {
                nombre: nuevoNombre,
            });

            // Actualizar registro local
            const index = this.municipios.findIndex((m) => m.id_municipio === id);
            if (index !== -1) {
                this.municipios[index] = respuesta.municipio;
            }

            this.editandoId = null;
            this.mostrarMensaje(respuesta.mensaje || "Municipio actualizado correctamente.", "exito");
            this.renderizar();
        } catch (error) {
            console.error("Error al actualizar municipio:", error);
            this.mostrarMensaje(error.message || "No se pudo actualizar el municipio.", "error");
            if (btnGuardar) {
                btnGuardar.disabled = false;
                btnGuardar.textContent = "Guardar";
            }
        }
    }

    async alternarEstado(id, nuevoEstado) {
        const municipio = this.municipios.find((m) => m.id_municipio === id);
        const nombre = municipio ? municipio.nombre : "este municipio";

        if (!nuevoEstado) {
            const confirmar = confirm(
                `¿Desea desactivar el municipio "${nombre}"?\n\n` +
                "Los usuarios ya no podrán seleccionarlo para nuevos turnos en el formulario público.\n" +
                "Los turnos y solicitudes históricas no se verán afectados."
            );
            if (!confirmar) return;
        }

        try {
            const respuesta = await ApiService.patch(`/api/admin/municipios/${id}/estado`, {
                activo: nuevoEstado,
            });

            // Actualizar estado en memoria
            const index = this.municipios.findIndex((m) => m.id_municipio === id);
            if (index !== -1) {
                this.municipios[index] = respuesta.municipio;
            }

            this.mostrarMensaje(respuesta.mensaje || "Estado actualizado correctamente.", "exito");
            this.renderizar();
        } catch (error) {
            console.error("Error al cambiar estado:", error);
            this.mostrarMensaje(error.message || "No se pudo cambiar el estado.", "error");
        }
    }

    async manejarCrear(evento) {
        evento.preventDefault();
        const nombre = this.inputNuevoNombre.value.trim();

        if (!nombre) {
            this.mostrarMensaje("Ingrese el nombre del municipio.", "error");
            this.inputNuevoNombre.focus();
            return;
        }

        this.btnCrear.disabled = true;
        const textoOriginal = this.btnCrear.innerHTML;
        this.btnCrear.innerHTML = "Guardando...";

        try {
            const respuesta = await ApiService.post("/api/admin/municipios", { nombre });

            // Agregar a la lista y re-ordenar alfabéticamente
            this.municipios.push(respuesta.municipio);
            this.municipios.sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

            this.inputNuevoNombre.value = "";
            this.mostrarMensaje(respuesta.mensaje || "Municipio registrado correctamente.", "exito");

            // Si el filtro estaba en "inactivos", cambiarlo a "todos" o "activos" para que se vea
            if (this.selectFiltro.value === "inactivos") {
                this.selectFiltro.value = "activos";
            }

            this.renderizar();
        } catch (error) {
            console.error("Error al registrar municipio:", error);
            this.mostrarMensaje(error.message || "No se pudo registrar el municipio.", "error");
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

document.addEventListener("DOMContentLoaded", () => {
    const admin = new MunicipiosAdmin();
    admin.inicializar();
});
