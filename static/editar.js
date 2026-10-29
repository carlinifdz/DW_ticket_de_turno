const formConsulta = document.getElementById("formularioConsulta");
const formEdicion = document.getElementById("formularioEdicion");
const mensajeConsulta = document.getElementById("mensajeConsulta");
const mensajeEdicion = document.getElementById("mensajeEdicion");

const CAMPOS = [
    "responsable", "nombre", "paterno",
    "materno", "telefono", "celular", "correo"
];

let folioActual = null;
let curpActual = null;


// Cargar municipios en el selector al abrir la pagina.
async function cargarMunicipios() {
    const select = document.getElementById("municipio");

    try {
        const municipios = await ApiService.get("/api/municipios");

        select.replaceChildren(new Option("Seleccione un municipio", ""));
        municipios.forEach(m => select.add(new Option(m.nombre, m.nombre)));
    } catch (error) {
        select.replaceChildren(new Option("No se pudieron cargar", ""));
    }
}

function mostrarMensaje(elemento, texto, tipo) {
    elemento.textContent = texto;
    elemento.className = "mensaje visible " + tipo;
}

function limpiarMensaje(elemento) {
    elemento.textContent = "";
    elemento.className = "mensaje";
}

function llenarFormulario(solicitud) {
    folioActual = solicitud.folio;
    curpActual = solicitud.curp;

    document.getElementById("resumenFolio").textContent = solicitud.folio;
    document.getElementById("resumenTurno").textContent = solicitud.numero_turno;
    document.getElementById("resumenMunicipio").textContent = solicitud.municipio;

    CAMPOS.forEach(campo => {
        document.getElementById(campo).value = solicitud[campo] || "";
    });
}


// Formateo basico de las entradas.
document.getElementById("curpConsulta").addEventListener("input", function () {
    this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 18);
});

["telefono", "celular"].forEach(id => {
    document.getElementById(id).addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "").slice(0, 10);
    });
});


// Paso 1: consultar la solicitud.
formConsulta.addEventListener("submit", async function (event) {
    event.preventDefault();
    limpiarMensaje(mensajeConsulta);

    const datos = Object.fromEntries(new FormData(formConsulta));

    try {
        const solicitud = await ApiService.post(
            "/api/solicitudes/consulta",
            datos
        );

        llenarFormulario(solicitud);
        formEdicion.hidden = false;
        limpiarMensaje(mensajeEdicion);
    } catch (error) {
        formEdicion.hidden = true;
        mostrarMensaje(mensajeConsulta, error.message, "error");
    }
});


// Paso 2: guardar los cambios.
formEdicion.addEventListener("submit", async function (event) {
    event.preventDefault();
    limpiarMensaje(mensajeEdicion);

    const datos = Object.fromEntries(new FormData(formEdicion));
    datos.curp = curpActual;

    try {
        const resultado = await ApiService.put(
            "/api/solicitudes/" + encodeURIComponent(folioActual),
            datos
        );

        mostrarMensaje(mensajeEdicion, resultado.mensaje, "exito");
    } catch (error) {
        mostrarMensaje(mensajeEdicion, error.message, "error");
    }
});


cargarMunicipios();
