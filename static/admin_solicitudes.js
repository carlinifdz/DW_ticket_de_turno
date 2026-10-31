const API = "/admin/api/solicitudes";

let paginaActual = 1;
let modoEdicion = null; // null = registrar; id = editar

const filtrosForm = document.getElementById("filtros");
const cuerpoTabla = document.getElementById("filas");
const sinDatos = document.getElementById("sinDatos");
const infoPagina = document.getElementById("infoPagina");
const btnPrev = document.getElementById("btnPrev");
const btnNext = document.getElementById("btnNext");

const modalForm = document.getElementById("modalForm");
const modalDetalle = document.getElementById("modalDetalle");
const formSolicitud = document.getElementById("formSolicitud");
const formTitulo = document.getElementById("formTitulo");
const formError = document.getElementById("formError");

const selMunicipio = document.getElementById("formMunicipio");
const campoEstatus = document.getElementById("formEstatus").closest(".campo-form");


// ---------- utilidades ----------
function esc(valor) {
    return String(valor == null ? "" : valor).replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
}

function boton(texto, clase, alHacerClic) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = clase;
    b.textContent = texto;
    b.addEventListener("click", alHacerClic);
    return b;
}

function abrir(modal) { modal.hidden = false; }
function cerrar(modal) { modal.hidden = true; }

async function llenarSelect(select, endpoint, conservarPrimera) {
    const registros = await ApiService.get(endpoint);
    if (!conservarPrimera) {
        select.innerHTML = "";
    }
    registros.forEach(r => select.add(new Option(r.nombre, r.nombre)));
}


// ---------- catálogos ----------
async function cargarCatalogos() {
    await Promise.all([
        llenarSelect(document.getElementById("fMunicipio"), "/api/municipios", true),
        llenarSelect(selMunicipio, "/api/municipios", false),
        llenarSelect(document.getElementById("formNivel"), "/api/niveles-educativos", false),
        llenarSelect(document.getElementById("formAsunto"), "/api/asuntos", false),
    ]);
}


// ---------- tabla ----------
async function cargarTabla(pagina) {
    const params = new URLSearchParams(new FormData(filtrosForm));
    params.set("pagina", pagina || 1);

    let datos;
    try {
        datos = await ApiService.get(API + "?" + params.toString());
    } catch (error) {
        if (/autorizado/i.test(error.message)) {
            window.location.href = "/admin/login";
            return;
        }
        cuerpoTabla.innerHTML = "";
        sinDatos.hidden = false;
        return;
    }

    paginaActual = datos.pagina;
    renderFilas(datos.solicitudes);
    infoPagina.textContent =
        `Página ${datos.pagina} de ${datos.paginas} · ${datos.total} solicitud(es)`;
    btnPrev.disabled = datos.pagina <= 1;
    btnNext.disabled = datos.pagina >= datos.paginas;
}

function renderFilas(lista) {
    cuerpoTabla.innerHTML = "";
    sinDatos.hidden = lista.length > 0;

    lista.forEach(s => {
        const tr = document.createElement("tr");
        const clase = s.estatus === "Resuelto" ? "resuelto" : "pendiente";

        tr.innerHTML = `
            <td>${esc(s.folio)}</td>
            <td>${esc(s.numero_turno)}</td>
            <td>${esc(s.nombre)}</td>
            <td>${esc(s.curp)}</td>
            <td>${esc(s.municipio)}</td>
            <td>${esc(s.asunto)}</td>
            <td><span class="estatus-chip ${clase}">${esc(s.estatus)}</span></td>
            <td>${esc(s.fecha)}</td>
            <td></td>`;

        const acciones = document.createElement("div");
        acciones.className = "acciones-fila";
        acciones.append(
            boton("Ver", "acc-btn", () => verDetalle(s.id)),
            boton("Editar", "acc-btn", () => abrirEditar(s.id)),
            boton("Eliminar", "acc-btn eliminar", () => eliminar(s.id, s.folio)),
        );
        tr.lastElementChild.append(acciones);
        cuerpoTabla.appendChild(tr);
    });
}


// ---------- detalle ----------
async function verDetalle(id) {
    let d;
    try {
        d = await ApiService.get(API + "/" + id);
    } catch (error) {
        alert("No se pudo cargar el detalle: " + error.message);
        return;
    }

    const campos = [
        ["Folio", d.folio], ["Número de turno", d.numero_turno],
        ["Responsable", d.responsable], ["CURP", d.curp],
        ["Nombre", d.nombre], ["Paterno", d.paterno], ["Materno", d.materno],
        ["Teléfono", d.telefono], ["Celular", d.celular], ["Correo", d.correo],
        ["Municipio", d.municipio], ["Nivel", d.nivel],
        ["Asunto", d.asunto], ["Estatus", d.estatus],
    ];

    const cont = document.getElementById("detalleContenido");
    cont.innerHTML = "";
    campos.forEach(([clave, valor]) => {
        const div = document.createElement("div");
        div.innerHTML = `<dt>${esc(clave)}</dt><dd>${esc(valor)}</dd>`;
        cont.appendChild(div);
    });

    abrir(modalDetalle);
}


// ---------- registrar / editar ----------
function abrirRegistrar() {
    modoEdicion = null;
    formTitulo.textContent = "Registrar solicitud";
    formSolicitud.reset();
    selMunicipio.disabled = false;
    campoEstatus.hidden = true; // el estatus no aplica al registrar (inicia en Pendiente)
    formError.hidden = true;
    abrir(modalForm);
}

async function abrirEditar(id) {
    modoEdicion = id;
    formTitulo.textContent = "Editar solicitud";
    formError.hidden = true;

    let d;
    try {
        d = await ApiService.get(API + "/" + id);
    } catch (error) {
        alert("No se pudo cargar la solicitud: " + error.message);
        return;
    }

    formSolicitud.responsable.value = d.responsable || "";
    formSolicitud.curp.value = d.curp || "";
    formSolicitud.nombre.value = d.nombre || "";
    formSolicitud.paterno.value = d.paterno || "";
    formSolicitud.materno.value = d.materno || "";
    formSolicitud.telefono.value = d.telefono || "";
    formSolicitud.celular.value = d.celular || "";
    formSolicitud.correo.value = d.correo || "";
    selMunicipio.value = d.municipio;
    selMunicipio.disabled = true; // el municipio define el turno: no se cambia al editar
    formSolicitud.nivel.value = d.nivel;
    formSolicitud.asunto.value = d.asunto;
    formSolicitud.estatus.value = d.estatus;
    campoEstatus.hidden = false;

    abrir(modalForm);
}

formSolicitud.addEventListener("submit", async (event) => {
    event.preventDefault();
    formError.hidden = true;

    const datos = Object.fromEntries(new FormData(formSolicitud));

    try {
        if (modoEdicion == null) {
            await ApiService.post(API, datos);
            cerrar(modalForm);
            cargarTabla(1);
        } else {
            await ApiService.put(API + "/" + modoEdicion, datos);
            cerrar(modalForm);
            cargarTabla(paginaActual);
        }
    } catch (error) {
        formError.textContent = error.message;
        formError.hidden = false;
    }
});


// ---------- eliminar ----------
async function eliminar(id, folio) {
    const ok = confirm(
        `¿Eliminar la solicitud ${folio}? Esta acción no se puede deshacer.`
    );
    if (!ok) {
        return;
    }
    try {
        await ApiService.delete(API + "/" + id);
        cargarTabla(paginaActual);
    } catch (error) {
        alert("No se pudo eliminar: " + error.message);
    }
}


// ---------- eventos ----------
filtrosForm.addEventListener("submit", (e) => {
    e.preventDefault();
    cargarTabla(1);
});

document.getElementById("btnLimpiar").addEventListener("click", () => {
    filtrosForm.reset();
    cargarTabla(1);
});

btnPrev.addEventListener("click", () => cargarTabla(paginaActual - 1));
btnNext.addEventListener("click", () => cargarTabla(paginaActual + 1));

document.getElementById("btnRegistrar").addEventListener("click", abrirRegistrar);
document.getElementById("cerrarForm").addEventListener("click", () => cerrar(modalForm));
document.getElementById("cerrarDetalle").addEventListener("click", () => cerrar(modalDetalle));

[modalForm, modalDetalle].forEach(m => {
    m.addEventListener("click", (e) => {
        if (e.target === m) {
            cerrar(m);
        }
    });
});

formSolicitud.curp.addEventListener("input", function () {
    this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 18);
});
["telefono", "celular"].forEach(nombre => {
    formSolicitud[nombre].addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "").slice(0, 10);
    });
});


// ---------- inicio ----------
(async function iniciar() {
    await cargarCatalogos();
    cargarTabla(1);
})();
