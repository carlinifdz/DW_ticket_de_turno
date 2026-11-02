
class EstadisticasObserver {

    constructor() {
        this.observadores = new Set();
        this.datos = null;
        this.municipio = "";
        this.intervalo = null;
        this.actualizando = false;
        this.version = 0;
    }

    // Registrar un observador
    suscribir(observador) {
        this.observadores.add(observador);

        // Si ya existen datos, entregarlos inmediatamente.
        if (this.datos !== null) {
            observador.actualizar(this.datos);
        }
    }

    // Eliminar un observador
    desuscribir(observador) {
        this.observadores.delete(observador);
    }

    // Notificar a todos los observadores
    notificar() {
        this.observadores.forEach(observador => {
            observador.actualizar(this.datos);
        });
    }

    // Consultar la API REST
    async consultar() {
        if (this.actualizando) return;

        this.actualizando = true;
        const versionActual = this.version;

        try {
            const ruta = this.municipio
                ? `/api/admin/estadisticas?municipio=${encodeURIComponent(this.municipio)}`
                : "/api/admin/estadisticas";

            const datos = await ApiService.get(ruta);

            // Descartar respuestas de un filtro anterior.
            if (versionActual !== this.version) return;

            const anteriores = JSON.stringify(this.datos);
            const nuevos = JSON.stringify(datos);

            // Solo notificar cuando los datos cambian.
            if (anteriores !== nuevos) {
                this.datos = datos;
                this.notificar();
            }

        } catch (error) {
            console.error(
                "Error al actualizar estadísticas:",
                error
            );

            // Una sesión expirada requiere iniciar sesión otra vez.
            if (/no autorizado|sesión inválida|expirada/i.test(
                error.message
            )) {
                this.detener();
                window.location.href = "/admin/login";
            }

        } finally {
            this.actualizando = false;
        }
    }

    // Cambiar el municipio seleccionado
    async cambiarMunicipio(idMunicipio) {
        this.municipio = idMunicipio;
        this.version++;
        this.datos = null;

        await this.consultar();
    }

    // Activar las actualizaciones automáticas
    iniciar() {
        if (this.intervalo !== null) return;

        this.consultar();

        this.intervalo = setInterval(() => {
            if (!document.hidden) {
                this.consultar();
            }
        }, 3000);
    }

    detener() {
        if (this.intervalo !== null) {
            clearInterval(this.intervalo);
            this.intervalo = null;
        }
    }
}
