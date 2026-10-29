
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError

from models import Municipio, NivelEducativo, Asunto
from services.turno_service import (
    TurnoService,
    SolicitudInvalida
)
from services.solicitud_publica_service import (
    SolicitudPublicaService,
    SolicitudNoEncontrada
)

api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)


class CatalogoAPI:

    @staticmethod
    def serializar(registros, campo_id):
        return [
            {
                "id": getattr(registro, campo_id),
                "nombre": registro.nombre
            }
            for registro in registros
        ]


@api_bp.get("/municipios")
def obtener_municipios():
    municipios = (
        Municipio.query
        .filter_by(activo=True)
        .order_by(Municipio.nombre)
        .all()
    )

    return jsonify(
        CatalogoAPI.serializar(
            municipios,
            "id_municipio"
        )
    )


@api_bp.get("/niveles-educativos")
def obtener_niveles():
    niveles = (
        NivelEducativo.query
        .filter_by(activo=True)
        .order_by(NivelEducativo.id_nivel)
        .all()
    )

    return jsonify(
        CatalogoAPI.serializar(
            niveles,
            "id_nivel"
        )
    )


@api_bp.get("/asuntos")
def obtener_asuntos():
    asuntos = (
        Asunto.query
        .filter_by(activo=True)
        .order_by(Asunto.id_asunto)
        .all()
    )

    return jsonify(
        CatalogoAPI.serializar(
            asuntos,
            "id_asunto"
        )
    )


@api_bp.post("/solicitudes")
def crear_solicitud():
    if not request.is_json:
        return jsonify({
            "error": "Se requiere enviar datos JSON"
        }), 415

    try:
        resultado = TurnoService.registrar(
            request.get_json(silent=True)
        )

        return jsonify(resultado), 201

    except SolicitudInvalida as error:
        return jsonify({
            "error": str(error)
        }), 400

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al registrar la solicitud"
        )

        return jsonify({
            "error": "No se pudo guardar la solicitud"
        }), 500


@api_bp.post("/solicitudes/consulta")
def consultar_solicitud():
    if not request.is_json:
        return jsonify({
            "error": "Se requiere enviar datos JSON"
        }), 415

    datos = request.get_json(silent=True) or {}

    try:
        resultado = SolicitudPublicaService.consultar(
            datos.get("curp"),
            datos.get("municipio"),
            datos.get("numero_turno")
        )

        return jsonify(resultado), 200

    except SolicitudNoEncontrada as error:
        return jsonify({
            "error": str(error)
        }), 404
