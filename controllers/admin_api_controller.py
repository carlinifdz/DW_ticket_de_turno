from functools import wraps

from flask import Blueprint, jsonify, request, session, current_app
from sqlalchemy.exc import SQLAlchemyError

from models.usuario import Usuario
from services.admin_solicitud_service import (
    AdminSolicitudService,
    SolicitudNoExiste,
    DatosInvalidos,
)
from services.turno_service import SolicitudInvalida


admin_api_bp = Blueprint(
    "admin_api",
    __name__,
    url_prefix="/admin/api"
)


# Igual que login_requerido pero responde JSON 401 en vez de redirigir.
def login_requerido_api(func):
    @wraps(func)
    def decorador(*args, **kwargs):
        id_usuario = session.get("admin_id")

        if not id_usuario:
            return jsonify({"error": "No autorizado"}), 401

        admin = Usuario.query.filter_by(
            id_usuario=id_usuario,
            activo=True
        ).first()

        if not admin:
            session.clear()
            return jsonify({"error": "No autorizado"}), 401

        return func(*args, **kwargs)

    return decorador


@admin_api_bp.get("/solicitudes")
@login_requerido_api
def listar():
    filtros = {
        "curp": request.args.get("curp"),
        "nombre": request.args.get("nombre"),
        "municipio": request.args.get("municipio"),
        "folio": request.args.get("folio"),
        "numero_turno": request.args.get("numero_turno"),
        "estatus": request.args.get("estatus"),
    }
    pagina = request.args.get("pagina", 1)

    return jsonify(AdminSolicitudService.listar(filtros, pagina)), 200


@admin_api_bp.get("/solicitudes/<int:id_solicitud>")
@login_requerido_api
def detalle(id_solicitud):
    try:
        return jsonify(AdminSolicitudService.obtener(id_solicitud)), 200
    except SolicitudNoExiste as error:
        return jsonify({"error": str(error)}), 404


@admin_api_bp.post("/solicitudes")
@login_requerido_api
def crear():
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos JSON"}), 415

    try:
        resultado = AdminSolicitudService.crear(request.get_json(silent=True))
        return jsonify(resultado), 201
    except SolicitudInvalida as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("Error al crear la solicitud (admin)")
        return jsonify({"error": "No se pudo crear la solicitud"}), 500


@admin_api_bp.put("/solicitudes/<int:id_solicitud>")
@login_requerido_api
def actualizar(id_solicitud):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos JSON"}), 415

    try:
        resultado = AdminSolicitudService.actualizar(
            id_solicitud, request.get_json(silent=True)
        )
        return jsonify({
            "mensaje": "Solicitud actualizada correctamente",
            **resultado
        }), 200
    except SolicitudNoExiste as error:
        return jsonify({"error": str(error)}), 404
    except DatosInvalidos as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("Error al actualizar la solicitud (admin)")
        return jsonify({"error": "No se pudo actualizar la solicitud"}), 500


@admin_api_bp.delete("/solicitudes/<int:id_solicitud>")
@login_requerido_api
def eliminar(id_solicitud):
    try:
        return jsonify(AdminSolicitudService.eliminar(id_solicitud)), 200
    except SolicitudNoExiste as error:
        return jsonify({"error": str(error)}), 404
    except SQLAlchemyError:
        current_app.logger.exception("Error al eliminar la solicitud (admin)")
        return jsonify({"error": "No se pudo eliminar la solicitud"}), 500
