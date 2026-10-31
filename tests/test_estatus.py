import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models.usuario import Usuario
from models.municipio import Municipio
from models.catalogos import NivelEducativo, Asunto
from models.solicitud import Solicitud
from models.turno import Turno
from services.admin_solicitud_service import (
    AdminSolicitudService,
    SolicitudNoExiste,
    DatosInvalidos,
)


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret-key-estatus"
    WTF_CSRF_ENABLED = False


class TestEstatus(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Crear datos de soporte
        self.admin = Usuario(
            nombre="Admin Estatus",
            usuario="adminestatus",
            password_hash=generate_password_hash("password123"),
            activo=True
        )
        self.municipio = Municipio(nombre="Saltillo", ultimo_turno=1, activo=True)
        self.nivel = NivelEducativo(nombre="Primaria", activo=True)
        self.asunto = Asunto(nombre="Inscripción", activo=True)

        db.session.add_all([self.admin, self.municipio, self.nivel, self.asunto])
        db.session.commit()

        # Crear una solicitud de prueba con su turno
        self.solicitud = Solicitud(
            responsable="Juan Pérez",
            curp="PERJ000101HDFRRN01",
            nombre="Carlos",
            paterno="Pérez",
            materno="Gómez",
            telefono="8441112233",
            celular="8449998877",
            correo="carlos@example.com",
            id_nivel=self.nivel.id_nivel,
            id_asunto=self.asunto.id_asunto,
            id_municipio=self.municipio.id_municipio,
            estatus="Pendiente"
        )
        db.session.add(self.solicitud)
        db.session.commit()

        self.turno = Turno(
            id_solicitud=self.solicitud.id_solicitud,
            id_municipio=self.municipio.id_municipio,
            numero_turno=1,
            folio="M1-000001"
        )
        db.session.add(self.turno)
        db.session.commit()

        self.csrf_token = "token-csrf-estatus-12345"

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def iniciar_sesion_admin(self):
        with self.client.session_transaction() as sess:
            sess["admin_id"] = self.admin.id_usuario
            sess["admin_nombre"] = self.admin.nombre
            sess["logout_csrf"] = self.csrf_token

    # ----------------------------------------------------
    # Pruebas Unitarias de AdminSolicitudService.cambiar_estatus
    # ----------------------------------------------------

    def test_cambiar_estatus_a_resuelto_exitoso(self):
        resultado = AdminSolicitudService.cambiar_estatus(
            self.solicitud.id_solicitud, "Resuelto"
        )
        self.assertEqual(resultado["estatus"], "Resuelto")

        # Verificar persistencia en base de datos
        sol_bd = db.session.get(Solicitud, self.solicitud.id_solicitud)
        self.assertEqual(sol_bd.estatus, "Resuelto")

    def test_cambiar_estatus_a_pendiente_exitoso(self):
        # Primero cambiar a Resuelto
        AdminSolicitudService.cambiar_estatus(self.solicitud.id_solicitud, "Resuelto")

        # Regresar a Pendiente
        resultado = AdminSolicitudService.cambiar_estatus(
            self.solicitud.id_solicitud, "Pendiente"
        )
        self.assertEqual(resultado["estatus"], "Pendiente")

        sol_bd = db.session.get(Solicitud, self.solicitud.id_solicitud)
        self.assertEqual(sol_bd.estatus, "Pendiente")

    def test_cambiar_estatus_valor_invalido_falla(self):
        with self.assertRaises(DatosInvalidos):
            AdminSolicitudService.cambiar_estatus(
                self.solicitud.id_solicitud, "Cancelado"
            )

        with self.assertRaises(DatosInvalidos):
            AdminSolicitudService.cambiar_estatus(
                self.solicitud.id_solicitud, ""
            )

    def test_cambiar_estatus_solicitud_inexistente_falla(self):
        with self.assertRaises(SolicitudNoExiste):
            AdminSolicitudService.cambiar_estatus(99999, "Resuelto")

    # ----------------------------------------------------
    # Pruebas del Endpoint PATCH /api/admin/solicitudes/<id>/estatus
    # ----------------------------------------------------

    def test_api_patch_sin_autenticacion_retorna_401(self):
        resp = self.client.patch(
            f"/api/admin/solicitudes/{self.solicitud.id_solicitud}/estatus",
            json={"estatus": "Resuelto"}
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("error", resp.get_json())

    def test_api_patch_sin_token_csrf_retorna_403(self):
        self.iniciar_sesion_admin()
        resp = self.client.patch(
            f"/api/admin/solicitudes/{self.solicitud.id_solicitud}/estatus",
            json={"estatus": "Resuelto"}
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("CSRF", resp.get_json()["error"])

    def test_api_patch_con_autenticacion_y_csrf_exitoso(self):
        self.iniciar_sesion_admin()
        resp = self.client.patch(
            f"/api/admin/solicitudes/{self.solicitud.id_solicitud}/estatus",
            json={"estatus": "Resuelto"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("mensaje", data)
        self.assertEqual(data["solicitud"]["estatus"], "Resuelto")

    def test_api_patch_estatus_invalido_retorna_400(self):
        self.iniciar_sesion_admin()
        resp = self.client.patch(
            f"/api/admin/solicitudes/{self.solicitud.id_solicitud}/estatus",
            json={"estatus": "En Proceso"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("inválido", resp.get_json()["error"])

    def test_api_patch_solicitud_no_existe_retorna_404(self):
        self.iniciar_sesion_admin()
        resp = self.client.patch(
            "/api/admin/solicitudes/99999/estatus",
            json={"estatus": "Resuelto"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 404)

    # ----------------------------------------------------
    # Pruebas de la Vista HTML /admin/estatus
    # ----------------------------------------------------

    def test_vista_estatus_requiere_login(self):
        resp = self.client.get("/admin/estatus")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp.headers["Location"])

    def test_vista_estatus_autenticada(self):
        self.iniciar_sesion_admin()
        resp = self.client.get("/admin/estatus")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Gestión de Estatus de Solicitudes", html)
        self.assertIn("tabla-estatus", html)

    def test_redireccion_seccion_placeholder_estatus(self):
        self.iniciar_sesion_admin()
        resp = self.client.get("/admin/seccion/estatus")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/estatus", resp.headers["Location"])


if __name__ == "__main__":
    unittest.main()
