import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models.usuario import Usuario
from models.catalogos import NivelEducativo, Asunto
from services.catalogos_service import (
    NivelEducativoService,
    AsuntoService,
    CatalogoInvalido,
    CatalogoDuplicado,
    CatalogoNoEncontrado,
)


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret-key-catalogos"
    WTF_CSRF_ENABLED = False


class TestCatalogos(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Usuario administrador para pruebas
        self.admin = Usuario(
            nombre="Admin Catálogo",
            usuario="admincatalogo",
            password_hash=generate_password_hash("password123"),
            activo=True
        )
        db.session.add(self.admin)
        db.session.commit()

        self.csrf_token = "token-csrf-catalogos-12345"

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
    # Pruebas Unitarias de NivelEducativoService
    # ----------------------------------------------------

    def test_crear_nivel_exitoso(self):
        res = NivelEducativoService.crear("Licenciatura")
        self.assertEqual(res["nombre"], "Licenciatura")
        self.assertTrue(res["activo"])

    def test_crear_nivel_vacio_falla(self):
        with self.assertRaises(CatalogoInvalido):
            NivelEducativoService.crear("   ")

    def test_crear_nivel_duplicado_falla(self):
        NivelEducativoService.crear("Primaria")
        with self.assertRaises(CatalogoDuplicado):
            NivelEducativoService.crear("primaria")

    def test_actualizar_nivel_exitoso(self):
        creado = NivelEducativoService.crear("Secu")
        actualizado = NivelEducativoService.actualizar(creado["id"], "Secundaria")
        self.assertEqual(actualizado["nombre"], "Secundaria")

    def test_cambiar_estado_nivel(self):
        creado = NivelEducativoService.crear("Preescolar")
        desactivado = NivelEducativoService.cambiar_estado(creado["id"], False)
        self.assertFalse(desactivado["activo"])

        # Verificar que solo_activos=True lo excluye
        activos = NivelEducativoService.listar(solo_activos=True)
        self.assertEqual(len(activos), 0)

        # Pero listar todos sí lo incluye
        todos = NivelEducativoService.listar(solo_activos=False)
        self.assertEqual(len(todos), 1)

    # ----------------------------------------------------
    # Pruebas Unitarias de AsuntoService
    # ----------------------------------------------------

    def test_crear_asunto_exitoso(self):
        res = AsuntoService.crear("Inscripción")
        self.assertEqual(res["nombre"], "Inscripción")
        self.assertTrue(res["activo"])

    def test_crear_asunto_vacio_falla(self):
        with self.assertRaises(CatalogoInvalido):
            AsuntoService.crear("   ")

    def test_crear_asunto_duplicado_falla(self):
        AsuntoService.crear("Cambio de Escuela")
        with self.assertRaises(CatalogoDuplicado):
            AsuntoService.crear("cambio de escuela")

    def test_actualizar_asunto_exitoso(self):
        creado = AsuntoService.crear("Doc")
        actualizado = AsuntoService.actualizar(creado["id"], "Documentación")
        self.assertEqual(actualizado["nombre"], "Documentación")

    def test_cambiar_estado_asunto(self):
        creado = AsuntoService.crear("Información")
        desactivado = AsuntoService.cambiar_estado(creado["id"], False)
        self.assertFalse(desactivado["activo"])

        activos = AsuntoService.listar(solo_activos=True)
        self.assertEqual(len(activos), 0)

        todos = AsuntoService.listar(solo_activos=False)
        self.assertEqual(len(todos), 1)

    # ----------------------------------------------------
    # Pruebas de Endpoints REST Protegidos (/api/admin)
    # ----------------------------------------------------

    def test_api_niveles_sin_login_retorna_401(self):
        resp = self.client.get("/api/admin/niveles")
        self.assertEqual(resp.status_code, 401)

        resp = self.client.post("/api/admin/niveles", json={"nombre": "Posgrado"})
        self.assertEqual(resp.status_code, 401)

    def test_api_asuntos_sin_login_retorna_401(self):
        resp = self.client.get("/api/admin/asuntos")
        self.assertEqual(resp.status_code, 401)

        resp = self.client.post("/api/admin/asuntos", json={"nombre": "Beca"})
        self.assertEqual(resp.status_code, 401)

    def test_api_mutacion_sin_csrf_retorna_403(self):
        self.iniciar_sesion_admin()
        resp = self.client.post("/api/admin/niveles", json={"nombre": "Técnico"})
        self.assertEqual(resp.status_code, 403)

    def test_api_crear_y_listar_niveles_autenticado(self):
        self.iniciar_sesion_admin()
        resp = self.client.post(
            "/api/admin/niveles",
            json={"nombre": "Bachillerato"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["registro"]["nombre"], "Bachillerato")

        # Listar
        resp_list = self.client.get("/api/admin/niveles")
        self.assertEqual(resp_list.status_code, 200)
        self.assertEqual(len(resp_list.get_json()), 1)

    def test_api_crear_y_listar_asuntos_autenticado(self):
        self.iniciar_sesion_admin()
        resp = self.client.post(
            "/api/admin/asuntos",
            json={"nombre": "Constancia de Estudios"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["registro"]["nombre"], "Constancia de Estudios")

        resp_list = self.client.get("/api/admin/asuntos")
        self.assertEqual(resp_list.status_code, 200)
        self.assertEqual(len(resp_list.get_json()), 1)

    def test_api_actualizar_y_cambiar_estado(self):
        self.iniciar_sesion_admin()
        nivel = NivelEducativoService.crear("Inicial")

        # Actualizar
        resp_put = self.client.put(
            f"/api/admin/niveles/{nivel['id']}",
            json={"nombre": "Educación Inicial"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp_put.status_code, 200)
        self.assertEqual(resp_put.get_json()["registro"]["nombre"], "Educación Inicial")

        # Cambiar estado
        resp_patch = self.client.patch(
            f"/api/admin/niveles/{nivel['id']}/estado",
            json={"activo": False},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp_patch.status_code, 200)
        self.assertFalse(resp_patch.get_json()["registro"]["activo"])

    # ----------------------------------------------------
    # Exclusión en APIs Públicas de Formulario
    # ----------------------------------------------------

    def test_excluir_inactivos_en_api_publica(self):
        # Nivel activo e inactivo
        NivelEducativoService.crear("Primaria")
        n_inactivo = NivelEducativoService.crear("Secundaria")
        NivelEducativoService.cambiar_estado(n_inactivo["id"], False)

        resp_niveles = self.client.get("/api/niveles-educativos")
        self.assertEqual(resp_niveles.status_code, 200)
        nombres_niveles = [item["nombre"] for item in resp_niveles.get_json()]
        self.assertIn("Primaria", nombres_niveles)
        self.assertNotIn("Secundaria", nombres_niveles)

        # Asunto activo e inactivo
        AsuntoService.crear("Inscripción")
        a_inactivo = AsuntoService.crear("Baja")
        AsuntoService.cambiar_estado(a_inactivo["id"], False)

        resp_asuntos = self.client.get("/api/asuntos")
        self.assertEqual(resp_asuntos.status_code, 200)
        nombres_asuntos = [item["nombre"] for item in resp_asuntos.get_json()]
        self.assertIn("Inscripción", nombres_asuntos)
        self.assertNotIn("Baja", nombres_asuntos)

    # ----------------------------------------------------
    # Pruebas de Vistas HTML
    # ----------------------------------------------------

    def test_vista_catalogos_requiere_login(self):
        resp = self.client.get("/admin/catalogos")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp.headers["Location"])

    def test_vista_catalogos_con_login(self):
        self.iniciar_sesion_admin()
        resp = self.client.get("/admin/catalogos")
        self.assertEqual(resp.status_code, 200)
        contenido = resp.get_data(as_text=True)
        self.assertIn("Administración de Catálogos", contenido)
        self.assertIn("Niveles Educativos", contenido)
        self.assertIn("Trámites y Asuntos", contenido)


if __name__ == "__main__":
    unittest.main()
