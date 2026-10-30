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
