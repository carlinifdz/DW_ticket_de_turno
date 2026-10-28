from flask import Blueprint, render_template

publico_bp = Blueprint("publico", __name__)


@publico_bp.get("/")
def inicio():
    return render_template("inicio.html")


@publico_bp.get("/crear-turno")
def crear_turno():
    return render_template("ticket.html")


@publico_bp.get("/editar-turno")
def editar_turno():
    return render_template("editar_turno.html")
