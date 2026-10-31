import unittest
from flask import session
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models.usuario import Usuario
from models.municipio import Municipio
from services.municipio_service import (
    MunicipioService,
    MunicipioInvalido,
    MunicipioDuplicado,
    MunicipioNoEncontrado,
)


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret-key-super-segura"
    WTF_CSRF_ENABLED = False


class TestMunicipios(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Crear tablas en SQLite en memoria
        db.create_all()

        # Crear usuario administrador para pruebas
        self.admin = Usuario(
            nombre="Admin Tester",
            usuario="admintester",
            password_hash=generate_password_hash("password123"),
            activo=True
        )
        db.session.add(self.admin)
        db.session.commit()

        # Token CSRF de prueba para peticiones autenticadas
        self.csrf_token = "token-csrf-de-prueba-12345"

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
    # Pruebas Unitarias de MunicipioService
    # ----------------------------------------------------

    def test_crear_municipio_exitoso(self):
        res = MunicipioService.crear("Saltillo")
        self.assertEqual(res["nombre"], "Saltillo")
        self.assertEqual(res["ultimo_turno"], 0)
        self.assertTrue(res["activo"])

    def test_crear_municipio_nombre_vacio_falla(self):
        with self.assertRaises(MunicipioInvalido):
            MunicipioService.crear("   ")

    def test_crear_municipio_duplicado_falla(self):
        MunicipioService.crear("Torreón")
        with self.assertRaises(MunicipioDuplicado):
            MunicipioService.crear("torreón")

    def test_actualizar_municipio_exitoso(self):
        creado = MunicipioService.crear("Ramos")
        actualizado = MunicipioService.actualizar(creado["id_municipio"], "Ramos Arizpe")
        self.assertEqual(actualizado["nombre"], "Ramos Arizpe")
        # Asegurar que ultimo_turno no cambia
        self.assertEqual(actualizado["ultimo_turno"], 0)

    def test_actualizar_municipio_duplicado_falla(self):
        m1 = MunicipioService.crear("Monclova")
        m2 = MunicipioService.crear("Parras")
        with self.assertRaises(MunicipioDuplicado):
            MunicipioService.actualizar(m2["id_municipio"], "monclova")

    def test_cambiar_estado_municipio(self):
        creado = MunicipioService.crear("Arteaga")
        desactivado = MunicipioService.cambiar_estado(creado["id_municipio"], False)
        self.assertFalse(desactivado["activo"])

        # Verificar que solo_activos=True lo excluye
        activos = MunicipioService.listar(solo_activos=True)
        self.assertEqual(len(activos), 0)

        # Pero listar todos sí lo incluye
        todos = MunicipioService.listar(solo_activos=False)
        self.assertEqual(len(todos), 1)

    # ----------------------------------------------------
    # Pruebas de Endpoints REST (/api/admin/municipios)
    # ----------------------------------------------------

    def test_api_sin_autenticacion_retorna_401(self):
        # GET sin login
        resp = self.client.get("/api/admin/municipios")
        self.assertEqual(resp.status_code, 401)
        self.assertIn("error", resp.get_json())

        # POST sin login
        resp = self.client.post("/api/admin/municipios", json={"nombre": "Acuña"})
        self.assertEqual(resp.status_code, 401)

    def test_api_mutacion_sin_csrf_retorna_403(self):
        self.iniciar_sesion_admin()
        # POST con sesión pero sin header CSRF
        resp = self.client.post("/api/admin/municipios", json={"nombre": "Acuña"})
        self.assertEqual(resp.status_code, 403)
        self.assertIn("CSRF", resp.get_json()["error"])

    def test_api_crear_municipio_autenticado(self):
        self.iniciar_sesion_admin()
        resp = self.client.post(
            "/api/admin/municipios",
            json={"nombre": "Sabinas"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["municipio"]["nombre"], "Sabinas")

    def test_api_actualizar_municipio_autenticado(self):
        self.iniciar_sesion_admin()
        creado = MunicipioService.crear("Múzquiz")

        resp = self.client.put(
            f"/api/admin/municipios/{creado['id_municipio']}",
            json={"nombre": "Melchor Múzquiz"},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["municipio"]["nombre"], "Melchor Múzquiz")

    def test_api_cambiar_estado_municipio_autenticado(self):
        self.iniciar_sesion_admin()
        creado = MunicipioService.crear("Allende")

        resp = self.client.patch(
            f"/api/admin/municipios/{creado['id_municipio']}/estado",
            json={"activo": False},
            headers={"X-CSRF-Token": self.csrf_token}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.get_json()["municipio"]["activo"])

    # ----------------------------------------------------
    # Pruebas de Vistas HTML (/admin/municipios)
    # ----------------------------------------------------

    def test_vista_municipios_requiere_login(self):
        resp = self.client.get("/admin/municipios")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp.headers["Location"])

    def test_vista_municipios_con_login(self):
        self.iniciar_sesion_admin()
        resp = self.client.get("/admin/municipios")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Administración de Municipios", resp.get_data(as_text=True))

    def test_redireccion_seccion_placeholder(self):
        self.iniciar_sesion_admin()
        resp = self.client.get("/admin/seccion/municipios")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/municipios", resp.headers["Location"])


    def test_municipio_desactivado_se_excluye_de_api_publica(self):
        # Crear activo
        MunicipioService.crear("Saltillo")
        # Crear e inactivar
        m_inactivo = MunicipioService.crear("Ramos")
        MunicipioService.cambiar_estado(m_inactivo["id_municipio"], False)

        resp = self.client.get("/api/municipios")
        self.assertEqual(resp.status_code, 200)
        nombres = [item["nombre"] for item in resp.get_json()]
        self.assertIn("Saltillo", nombres)
        self.assertNotIn("Ramos", nombres)


if __name__ == "__main__":
    unittest.main()
