
from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError

from models import Municipio, NivelEducativo, Asunto
from services.turno_service import TurnoService, SolicitudInvalida

publico_bp = Blueprint("publico", __name__)

# Página principal
@publico_bp.get("/")
def inicio():
    return render_template("inicio.html")

# Formulario para solicitar un turno
@publico_bp.get("/crear-turno")
def crear_turno():
    return render_template(
        "ticket.html",
        municipios=Municipio.query.filter_by(activo=True)
            .order_by(Municipio.nombre).all(),
        niveles=NivelEducativo.query.filter_by(activo=True)
            .order_by(NivelEducativo.id_nivel).all(),
        asuntos=Asunto.query.filter_by(activo=True)
            .order_by(Asunto.id_asunto).all()
    )

@publico_bp.get("/editar-turno")
def editar_turno():
    return render_template("editar_turno.html")

@publico_bp.post("/generar-turno")
def generar_turno():
    try:
        resultado = TurnoService.registrar(
            request.get_json(silent=True)
        )
        return jsonify(resultado), 201

    except SolicitudInvalida as error:
        return jsonify(error=str(error)), 400

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al guardar el turno"
        )
        return jsonify(
            error="No se pudo guardar la solicitud en MySQL"
        ), 500
