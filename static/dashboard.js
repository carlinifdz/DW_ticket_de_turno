
class ObservadorTarjetas {

    actualizar(datos) {
        document.getElementById("totalSolicitudes")
            .textContent = datos.total;

        document.getElementById("totalPendientes")
            .textContent = datos.pendientes;

        document.getElementById("totalResueltas")
            .textContent = datos.resueltas;
    }
}


class ObservadorGraficaEstados {

    constructor() {
        const contexto = document.getElementById(
            "graficaEstados"
        );

        this.grafica = new Chart(contexto, {
            type: "doughnut",
            data: {
                labels: ["Pendientes", "Resueltas"],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: [
                        "#f59e0b",
                        "#10b981"
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    actualizar(datos) {
        this.grafica.data.datasets[0].data = [
            datos.pendientes,
            datos.resueltas
        ];

        this.grafica.update();
    }
}


class ObservadorGraficaMunicipios {

    constructor() {
        const contexto = document.getElementById(
            "graficaMunicipios"
        );

        this.grafica = new Chart(contexto, {
            type: "bar",
            data: {
                labels: [],
                datasets: [{
                    label: "Solicitudes",
                    data: [],
                    backgroundColor: "#2563eb",
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    actualizar(datos) {
        this.grafica.data.labels =
            datos.por_municipio.map(
                item => item.municipio
            );

        this.grafica.data.datasets[0].data =
            datos.por_municipio.map(
                item => item.total
            );

        this.grafica.update();
    }
}


// ==========================================
// INICIALIZACIÓN DEL DASHBOARD
// ==========================================

document.addEventListener("DOMContentLoaded", async () => {

    const subject = new EstadisticasObserver();

    const tarjetas = new ObservadorTarjetas();
    const graficaEstados =
        new ObservadorGraficaEstados();

    const graficaMunicipios =
        new ObservadorGraficaMunicipios();

    // Suscribir los tres observadores.
    subject.suscribir(tarjetas);
    subject.suscribir(graficaEstados);
    subject.suscribir(graficaMunicipios);

    const selector = document.getElementById(
        "filtroMunicipio"
    );

    // Cargar los municipios desde la API existente.
    try {
        const municipios = await ApiService.get(
            "/api/municipios"
        );

        municipios.forEach(municipio => {
            const opcion = document.createElement("option");

            opcion.value = municipio.id;
            opcion.textContent = municipio.nombre;

            selector.appendChild(opcion);
        });

    } catch (error) {
        console.error(
            "Error al cargar municipios:",
            error
        );
    }

    // Aplicar el filtro seleccionado.
    selector.addEventListener("change", event => {
        subject.cambiarMunicipio(event.target.value);
    });

    // Comenzar a observar cambios.
    subject.iniciar();

    // Actualizar al regresar a la pestaña.
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            subject.consultar();
        }
    });

    window.addEventListener("pagehide", () => {
        subject.detener();
    });
});
