class CatalogoService {

    static async obtener(endpoint) {
        const respuesta = await fetch(endpoint, {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!respuesta.ok) {
            throw new Error(
                "No se pudo cargar el catálogo"
            );
        }

        return await respuesta.json();
    }

    static async cargarSelect(id, endpoint, mensaje) {
        const select = document.getElementById(id);

        select.disabled = true;
        select.replaceChildren(
            new Option("Cargando opciones...", "")
        );

        try {
            const registros = await this.obtener(endpoint);

            select.replaceChildren(
                new Option(mensaje, "")
            );

            registros.forEach(registro => {
                const opcion = new Option(
                    registro.nombre,
                    registro.nombre
                );

                select.add(opcion);
            });

            select.disabled = false;

        } catch (error) {
            console.error(error);

            select.replaceChildren(
                new Option(
                    "Error al cargar opciones",
                    ""
                )
            );

            // Permanece deshabilitado si falla la API
        }
    }

    static async cargarTodos() {
        await Promise.all([
            this.cargarSelect(
                "municipio",
                "/api/municipios",
                "Seleccione un municipio"
            ),

            this.cargarSelect(
                "nivel",
                "/api/niveles-educativos",
                "Seleccione un nivel educativo"
            ),

            this.cargarSelect(
                "asunto",
                "/api/asuntos",
                "Seleccione un asunto"
            )
        ]);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    CatalogoService.cargarTodos();
});