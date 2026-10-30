import secrets
from functools import wraps
from flask import Blueprint, jsonify, request, session, current_app
from sqlalchemy.exc import SQLAlchemyError

from models.usuario import Usuario
from services.municipio_service import (
    MunicipioService,
    MunicipioInvalido,
    MunicipioNoEncontrado,
    MunicipioDuplicado,
)
from services.catalogos_service import (
    NivelEducativoService,
    AsuntoService,
    CatalogoInvalido,
    CatalogoNoEncontrado,
    CatalogoDuplicado,
)

admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")


def admin_api_requerido(func):
    """Protege endpoints REST administrativos respondiendo con 401/403 en formato JSON."""
    @wraps(func)
    def decorador(*args, **kwargs):
        id_usuario = session.get("admin_id")
        if not id_usuario:
            return jsonify({"error": "Acceso no autorizado. Inicie sesión como administrador."}), 401

        admin = Usuario.query.filter_by(id_usuario=id_usuario, activo=True).first()
        if not admin:
            session.clear()
            return jsonify({"error": "Sesión inválida o expirada."}), 401

        # Validación CSRF para métodos que modifican estado
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token_cliente = request.headers.get("X-CSRF-Token", "")
            token_servidor = session.get("logout_csrf", "")
            if not token_servidor or not token_cliente or not secrets.compare_digest(token_cliente, token_servidor):
                return jsonify({"error": "Token de seguridad CSRF inválido o ausente."}), 403

        return func(*args, **kwargs)

    return decorador


@admin_api_bp.get("/municipios")
@admin_api_requerido
def listar_municipios():
    try:
        municipios = MunicipioService.listar(solo_activos=False)
        return jsonify(municipios), 200
    except SQLAlchemyError:
        current_app.logger.exception("Error al consultar municipios")
        return jsonify({"error": "Error interno al consultar municipios."}), 500


@admin_api_bp.post("/municipios")
@admin_api_requerido
def crear_municipio():
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        nuevo = MunicipioService.crear(nombre)
        return jsonify({
            "mensaje": f"Municipio '{nuevo['nombre']}' registrado correctamente.",
            "municipio": nuevo
        }), 201
    except MunicipioInvalido as error:
        return jsonify({"error": str(error)}), 400
    except MunicipioDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al crear municipio")
        return jsonify({"error": "Error interno al registrar el municipio."}), 500


@admin_api_bp.put("/municipios/<int:id_municipio>")
@admin_api_requerido
def actualizar_municipio(id_municipio):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        actualizado = MunicipioService.actualizar(id_municipio, nombre)
        return jsonify({
            "mensaje": f"Municipio actualizado a '{actualizado['nombre']}'.",
            "municipio": actualizado
        }), 200
    except MunicipioNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except MunicipioInvalido as error:
        return jsonify({"error": str(error)}), 400
    except MunicipioDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al actualizar municipio")
        return jsonify({"error": "Error interno al actualizar el municipio."}), 500


@admin_api_bp.patch("/municipios/<int:id_municipio>/estado")
@admin_api_requerido
def cambiar_estado_municipio(id_municipio):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    if "activo" not in datos:
        return jsonify({"error": "El campo 'activo' es obligatorio."}), 400

    activo = datos.get("activo")

    try:
        actualizado = MunicipioService.cambiar_estado(id_municipio, activo)
        estado_texto = "activado" if actualizado["activo"] else "desactivado"
        return jsonify({
            "mensaje": f"Municipio '{actualizado['nombre']}' {estado_texto} correctamente.",
            "municipio": actualizado
        }), 200
    except MunicipioNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except MunicipioInvalido as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("Error al cambiar estado del municipio")
        return jsonify({"error": "Error interno al cambiar el estado del municipio."}), 500


# ==========================================================
# ENDPOINTS: NIVELES EDUCATIVOS
# ==========================================================

@admin_api_bp.get("/niveles")
@admin_api_requerido
def listar_niveles():
    try:
        niveles = NivelEducativoService.listar(solo_activos=False)
        return jsonify(niveles), 200
    except SQLAlchemyError:
        current_app.logger.exception("Error al consultar niveles educativos")
        return jsonify({"error": "Error interno al consultar niveles educativos."}), 500


@admin_api_bp.post("/niveles")
@admin_api_requerido
def crear_nivel():
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        nuevo = NivelEducativoService.crear(nombre)
        return jsonify({
            "mensaje": f"Nivel educativo '{nuevo['nombre']}' registrado correctamente.",
            "registro": nuevo
        }), 201
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al crear nivel educativo")
        return jsonify({"error": "Error interno al registrar el nivel educativo."}), 500


@admin_api_bp.put("/niveles/<int:id_nivel>")
@admin_api_requerido
def actualizar_nivel(id_nivel):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        actualizado = NivelEducativoService.actualizar(id_nivel, nombre)
        return jsonify({
            "mensaje": f"Nivel educativo actualizado a '{actualizado['nombre']}'.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al actualizar nivel educativo")
        return jsonify({"error": "Error interno al actualizar el nivel educativo."}), 500


@admin_api_bp.patch("/niveles/<int:id_nivel>/estado")
@admin_api_requerido
def cambiar_estado_nivel(id_nivel):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    if "activo" not in datos:
        return jsonify({"error": "El campo 'activo' es obligatorio."}), 400

    activo = datos.get("activo")

    try:
        actualizado = NivelEducativoService.cambiar_estado(id_nivel, activo)
        estado_texto = "activado" if actualizado["activo"] else "desactivado"
        return jsonify({
            "mensaje": f"Nivel educativo '{actualizado['nombre']}' {estado_texto} correctamente.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("Error al cambiar estado del nivel educativo")
        return jsonify({"error": "Error interno al cambiar el estado del nivel educativo."}), 500


# ==========================================================
# ENDPOINTS: ASUNTOS
# ==========================================================

@admin_api_bp.get("/asuntos")
@admin_api_requerido
def listar_asuntos():
    try:
        asuntos = AsuntoService.listar(solo_activos=False)
        return jsonify(asuntos), 200
    except SQLAlchemyError:
        current_app.logger.exception("Error al consultar asuntos")
        return jsonify({"error": "Error interno al consultar asuntos."}), 500


@admin_api_bp.post("/asuntos")
@admin_api_requerido
def crear_asunto():
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        nuevo = AsuntoService.crear(nombre)
        return jsonify({
            "mensaje": f"Asunto '{nuevo['nombre']}' registrado correctamente.",
            "registro": nuevo
        }), 201
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al crear asunto")
        return jsonify({"error": "Error interno al registrar el asunto."}), 500


@admin_api_bp.put("/asuntos/<int:id_asunto>")
@admin_api_requerido
def actualizar_asunto(id_asunto):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        actualizado = AsuntoService.actualizar(id_asunto, nombre)
        return jsonify({
            "mensaje": f"Asunto actualizado a '{actualizado['nombre']}'.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al actualizar asunto")
        return jsonify({"error": "Error interno al actualizar el asunto."}), 500


@admin_api_bp.patch("/asuntos/<int:id_asunto>/estado")
@admin_api_requerido
def cambiar_estado_asunto(id_asunto):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    if "activo" not in datos:
        return jsonify({"error": "El campo 'activo' es obligatorio."}), 400

    activo = datos.get("activo")

    try:
        actualizado = AsuntoService.cambiar_estado(id_asunto, activo)
        estado_texto = "activado" if actualizado["activo"] else "desactivado"
        return jsonify({
            "mensaje": f"Asunto '{actualizado['nombre']}' {estado_texto} correctamente.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("Error al cambiar estado del asunto")
        return jsonify({"error": "Error interno al cambiar el estado del asunto."}), 500
