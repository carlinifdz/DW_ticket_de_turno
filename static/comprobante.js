// Intenta iniciar la descarga automatica del PDF al llegar desde el registro.
(function () {
    const parametros = new URLSearchParams(window.location.search);

    if (!parametros.has("descarga")) {
        return;
    }

    const seccion = document.querySelector(".comprobante");
    const url = seccion ? seccion.dataset.pdf : null;

    if (!url) {
        return;
    }

    // Descarga sin salir de la pagina usando un iframe oculto.
    const marco = document.createElement("iframe");
    marco.style.display = "none";
    marco.src = url;
    document.body.appendChild(marco);

    // Limpia el parametro para no repetir la descarga al recargar.
    parametros.delete("descarga");

    const limpia = window.location.pathname +
        (parametros.toString() ? "?" + parametros.toString() : "");

    window.history.replaceState({}, "", limpia);
})();
