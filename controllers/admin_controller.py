import os
import secrets
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort
)

from models.usuario import Usuario
from services.auth_service import AuthService


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# Protección de rutas administrativas
def login_requerido(func):
    @wraps(func)
    def decorador(*args, **kwargs):
        id_usuario = session.get("admin_id")

        if not id_usuario:
            return redirect(url_for("admin.login"))

        admin = Usuario.query.filter_by(
            id_usuario=id_usuario,
            activo=True
        ).first()

        if not admin:
            session.clear()
            return redirect(url_for("admin.login"))

        return func(*args, **kwargs)

    return decorador


# Inicio de sesión
@admin_bp.route("/login", methods=["GET", "POST"])
def login():

    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    error = None

    if request.method == "POST":

        token = request.form.get("csrf_token", "")
        token_valido = secrets.compare_digest(
            token,
            session.get("login_csrf", "")
        ) if token and session.get("login_csrf") else False

        captcha_valido = AuthService.validar_captcha(
            request.form.get("g-recaptcha-response", "")
        )

        if not token_valido:
            abort(400)

        usuario = request.form.get(
            "usuario", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        if not captcha_valido:
            error = "CAPTCHA incorrecto."
        else:
            administrador = AuthService.autenticar(
                usuario,
                password
            )

            if administrador:
                session.clear()
                session["admin_id"] = administrador.id_usuario
                session["admin_nombre"] = administrador.nombre
                session["logout_csrf"] = secrets.token_urlsafe(32)

                return redirect(
                    url_for("admin.dashboard")
                )

            error = "Usuario o contraseña incorrectos."

    session["login_csrf"] = secrets.token_urlsafe(32)

    return render_template(
        "admin/login.html",
        recaptcha_site_key=os.getenv("RECAPTCHA_SITE_KEY"),
        csrf_token=session["login_csrf"],
        error=error
    )


# Panel principal
@admin_bp.get("/dashboard")
@login_requerido
def dashboard():
    return render_template(
        "admin/dashboard.html",
        nombre=session.get("admin_nombre"),
        csrf_token=session.get("logout_csrf")
    )


# Opciones provisionales del administrador
SECCIONES = {
    "solicitudes": "Consulta de solicitudes",
    "registrar": "Registrar solicitud",
    "estatus": "Gestión de estatus",
    "municipios": "Catálogo de municipios",
    "niveles": "Catálogo de niveles educativos",
    "asuntos": "Catálogo de asuntos",
    "estadisticas": "Dashboard de estadísticas",
    "api": "API REST"
}


@admin_bp.get("/seccion/<nombre>")
@login_requerido
def seccion(nombre):

    if nombre not in SECCIONES:
        abort(404)

    return render_template(
        "admin/placeholder.html",
        titulo=SECCIONES[nombre],
        csrf_token=session.get("logout_csrf")
    )


# Cerrar sesión
@admin_bp.post("/logout")
@login_requerido
def logout():

    token = request.form.get("csrf_token", "")
    esperado = session.get("logout_csrf", "")

    if not token or not esperado or not secrets.compare_digest(
        token, esperado
    ):
        abort(400)

    session.clear()

    return redirect(url_for("publico.inicio"))
