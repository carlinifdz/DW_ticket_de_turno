
import os
import requests

from werkzeug.security import check_password_hash
from models.usuario import Usuario


class AuthService:

    @staticmethod
    def autenticar(usuario, password):
        administrador = Usuario.query.filter_by(
            usuario=usuario,
            activo=True
        ).first()

        if administrador and check_password_hash(
            administrador.password_hash,
            password
        ):
            return administrador

        return None

    @staticmethod
    def validar_captcha(token):
        secret_key = os.getenv("RECAPTCHA_SECRET_KEY")

        if not secret_key or not token:
            return False

        try:
            respuesta = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": secret_key,
                    "response": token
                },
                timeout=5
            )

            respuesta.raise_for_status()
            resultado = respuesta.json()

            return resultado.get("success") is True

        except (requests.RequestException, ValueError):
            return False
