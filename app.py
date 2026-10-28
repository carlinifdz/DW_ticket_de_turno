
import click

from flask import Flask
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db, migrate
from controllers.publico_controller import publico_bp
from controllers.admin_controller import admin_bp
from models.usuario import Usuario

import models


@click.command("crear-admin")
@click.option(
    "--usuario",
    prompt="Nombre de usuario"
)
@click.option(
    "--nombre",
    prompt="Nombre completo"
)
@click.password_option(
    prompt="Contraseña",
    confirmation_prompt=True
)
@with_appcontext
def crear_admin(usuario, nombre, password):

    usuario = usuario.strip()
    nombre = nombre.strip()

    if not usuario or not nombre:
        raise click.ClickException(
            "El nombre y el usuario son obligatorios."
        )

    existente = Usuario.query.filter_by(
        usuario=usuario
    ).first()

    if existente:
        raise click.ClickException(
            "Ese usuario ya existe."
        )

    nuevo = Usuario(
        nombre=nombre,
        usuario=usuario,
        password_hash=generate_password_hash(password),
        activo=True
    )

    try:
        db.session.add(nuevo)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise click.ClickException(
            "No se pudo registrar el administrador."
        )

    click.echo("Administrador registrado correctamente.")


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError(
            "Configura DATABASE_URL en el archivo .env"
        )

    if (
        not app.config.get("SECRET_KEY")
        or app.config["SECRET_KEY"] == "dev-only-change-me"
    ):
        raise RuntimeError(
            "Configura una SECRET_KEY segura en .env"
        )

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax"
    )

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(publico_bp)
    app.register_blueprint(admin_bp)

    app.cli.add_command(crear_admin)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
