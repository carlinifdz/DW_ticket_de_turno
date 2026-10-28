
const formulario = document.getElementById("formularioTurno");

// Desactivar validaciones automáticas del navegador
formulario.noValidate = true;

// ======================================
// 1. PREPARAR LOS MENSAJES DE ERROR
// ======================================

// Crear un contenedor para cada input/select
// para que el error aparezca DEBAJO del campo.
formulario.querySelectorAll(".campo input, .campo select").forEach(campo => {
    const contenedor = document.createElement("div");
    contenedor.className = "control-campo";

    campo.parentNode.insertBefore(contenedor, campo);
    contenedor.appendChild(campo);
});

// ======================================
// 2. SOLO NÚMEROS EN TELÉFONO Y CELULAR
// ======================================

["telefono", "celular"].forEach(id => {
    const campo = document.getElementById(id);

    campo.setAttribute("inputmode", "numeric");
    campo.setAttribute("maxlength", "10");

    campo.addEventListener("input", function() {
        this.value = this.value.replace(/\D/g, "").slice(0, 10);
        limpiarError(this);
    });
});

// ======================================
// 3. CURP EN MAYÚSCULAS
// ======================================

const curp = document.getElementById("curp");

curp.setAttribute("maxlength", "18");

curp.addEventListener("input", function() {
    this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
    limpiarError(this);
});

// ======================================
// 4. MOSTRAR Y LIMPIAR ERRORES
// ======================================

function mostrarError(campo, texto) {
    limpiarError(campo);

    campo.classList.add("campo-error");
    campo.setAttribute("aria-invalid", "true");

    const mensaje = document.createElement("span");
    mensaje.className = "mensaje-error";
    mensaje.textContent = texto;
    mensaje.setAttribute("role", "alert");

    campo.parentElement.appendChild(mensaje);
}

function limpiarError(campo) {
    campo.classList.remove("campo-error");
    campo.removeAttribute("aria-invalid");

    const mensaje = campo.parentElement.querySelector(".mensaje-error");

    if (mensaje) {
        mensaje.remove();
    }
}

function limpiarErrores() {
    formulario.querySelectorAll("input, select").forEach(campo => {
        limpiarError(campo);
    });
}

// ======================================
// 5. VALIDAR FORMATO DE CURP MEXICANA
// ======================================

function validarCURP(valor) {
    // Formato general de los 18 caracteres
    const expresionCURP =
        /^[A-Z][AEIOUX][A-Z]{2}(\d{2})(\d{2})(\d{2})([HM])(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d$/;

    const coincidencia = valor.match(expresionCURP);

    if (!coincidencia) {
        return false;
    }

    // Revisar que el mes y día sean posibles
    const anio = Number(coincidencia[1]);
    const mes = Number(coincidencia[2]);
    const dia = Number(coincidencia[3]);

    if (mes < 1 || mes > 12) {
        return false;
    }

    // Febrero se valida tomando como referencia
    // un año del calendario; el siglo real no se
    // determina únicamente con los 2 dígitos.
    const fecha = new Date(Date.UTC(2000 + anio, mes - 1, dia));

    if (
        fecha.getUTCMonth() !== mes - 1 ||
        fecha.getUTCDate() !== dia
    ) {
        return false;
    }

    return true;
}

// ======================================
// 6. VALIDAR TODOS LOS CAMPOS
// ======================================

function validarFormulario() {
    let esValido = true;

    const campos = formulario.querySelectorAll("input, select");

    campos.forEach(campo => {
        const valor = campo.value.trim();
        let error = "";

        // Campos obligatorios
        if (valor === "") {
            error = "Este campo es obligatorio";
        }

        // Validar CURP
        else if (campo.id === "curp") {
            if (!validarCURP(valor)) {
                error = "La CURP no tiene un formato válido";
            }
        }

        // Validar teléfono y celular
        else if (
            campo.id === "telefono" ||
            campo.id === "celular"
        ) {
            if (!/^[0-9]{10}$/.test(valor)) {
                error = "Debe contener exactamente 10 números";
            }
        }

        // Validar correo
        else if (campo.id === "correo") {
            const expresionCorreo = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (!expresionCorreo.test(valor)) {
                error = "Ingrese un correo electrónico válido";
            }
        }

        // Mostrar error, si existe
        if (error !== "") {
            mostrarError(campo, error);
            esValido = false;
        } else {
            limpiarError(campo);
        }
    });

    return esValido;
}

// ======================================
// 7. LIMPIAR ERRORES AL CORREGIR CAMPOS
// ======================================

formulario.querySelectorAll("input, select").forEach(campo => {
    campo.addEventListener("input", function() {
        limpiarError(this);
    });

    campo.addEventListener("change", function() {
        limpiarError(this);
    });
});

// ======================================
// 8. ENVIAR DATOS A FLASK
// ======================================

formulario.addEventListener("submit", async function(event) {
    event.preventDefault();

    limpiarErrores();

    const esValido = validarFormulario();

    // No enviar si existen errores
    if (!esValido) {
        const primerError = formulario.querySelector(".campo-error");

        if (primerError) {
            primerError.focus();
        }

        return;
    }

    const datos = Object.fromEntries(new FormData(formulario));

    const boton = formulario.querySelector('button[type="submit"]');

    try {
        boton.disabled = true;
        boton.textContent = "Generando turno...";

        const respuesta = await fetch("/generar-turno", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "Error al generar turno");
        }

        alert(
            resultado.mensaje +
            "\nFolio: " +
            resultado.folio
        );

        formulario.reset();
        limpiarErrores();

    } catch (error) {
        console.error("Error:", error);
        alert("Ocurrió un error: " + error.message);

    } finally {
        boton.disabled = false;
        boton.textContent = "Generar Turno";
    }
});
