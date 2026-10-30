
class ApiService {

    static getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute("content") : null;
    }

    static async solicitar(ruta, opciones = {}) {
        const headers = {
            "Accept": "application/json",
            ...(opciones.headers || {})
        };

        const metodo = (opciones.method || "GET").toUpperCase();
        if (["POST", "PUT", "PATCH", "DELETE"].includes(metodo) && !headers["X-CSRF-Token"]) {
            const token = this.getCsrfToken();
            if (token) {
                headers["X-CSRF-Token"] = token;
            }
        }

        const configuracion = {
            credentials: "same-origin",
            ...opciones,
            headers
        };

        const respuesta = await fetch(ruta, configuracion);

        const tipo = respuesta.headers.get("content-type") || "";

        let datos = null;

        if (tipo.includes("application/json")) {
            datos = await respuesta.json();
        } else {
            datos = await respuesta.text();
        }

        if (!respuesta.ok) {
            const mensaje =
                datos &&
                typeof datos === "object" &&
                datos.error
                    ? datos.error
                    : `Error HTTP ${respuesta.status}`;

            throw new Error(mensaje);
        }

        return datos;
    }

    static get(ruta) {
        return this.solicitar(ruta, {
            method: "GET"
        });
    }

    static post(ruta, datos) {
        return this.solicitar(ruta, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });
    }

    static put(ruta, datos) {
        return this.solicitar(ruta, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });
    }

    static patch(ruta, datos) {
        return this.solicitar(ruta, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });
    }

    static delete(ruta) {
        return this.solicitar(ruta, {
            method: "DELETE"
        });
    }
}
