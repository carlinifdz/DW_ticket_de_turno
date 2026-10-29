import re

from extensions import db
from models import Municipio, Solicitud, Turno, NivelEducativo, Asunto


class SolicitudNoEncontrada(LookupError):
    pass


class EdicionInvalida(ValueError):
    pass


class SolicitudPublicaService:
    """Consulta y edicion publica de una solicitud por CURP + municipio + numero."""

    CAMPOS_EDITABLES = ("responsable", "nombre", "paterno", "materno",
                        "telefono", "celular", "correo")

    @staticmethod
    def _buscar_turno(municipio_nombre, numero_turno):
        municipio = Municipio.query.filter_by(
            nombre=str(municipio_nombre or "").strip()
        ).first()
        if municipio is None:
            return None
        try:
            numero = int(numero_turno)
        except (TypeError, ValueError):
            return None
        return Turno.query.filter_by(
            id_municipio=municipio.id_municipio, numero_turno=numero
        ).first()

    @staticmethod
    def consultar(curp, municipio_nombre, numero_turno):
        curp = str(curp or "").strip().upper()
        turno = SolicitudPublicaService._buscar_turno(municipio_nombre, numero_turno)
        if turno is None:
            raise SolicitudNoEncontrada("No existe un turno con esos datos")

        solicitud = db.session.get(Solicitud, turno.id_solicitud)
        # Si la CURP no coincide, respondemos igual que si no existiera.
        if solicitud is None or solicitud.curp != curp:
            raise SolicitudNoEncontrada("No existe un turno con esos datos")

        return SolicitudPublicaService._serializar(solicitud, turno)

    @staticmethod
    def actualizar(folio, curp, datos):
        curp = str(curp or "").strip().upper()
        turno = Turno.query.filter_by(
            folio=str(folio or "").strip().upper()
        ).first()
        if turno is None:
            raise SolicitudNoEncontrada("No existe un turno con esos datos")

        solicitud = db.session.get(Solicitud, turno.id_solicitud)
        if solicitud is None or solicitud.curp != curp:
            raise SolicitudNoEncontrada("No existe un turno con esos datos")

        valores = {
            campo: str((datos or {}).get(campo) or "").strip()
            for campo in SolicitudPublicaService.CAMPOS_EDITABLES
        }
        SolicitudPublicaService._validar(valores)

        try:
            for campo, valor in valores.items():
                setattr(solicitud, campo, valor)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return SolicitudPublicaService._serializar(solicitud, turno)

    @staticmethod
    def _validar(valores):
        for campo in SolicitudPublicaService.CAMPOS_EDITABLES:
            if not valores[campo]:
                raise EdicionInvalida(f"El campo {campo} es obligatorio")
        for campo in ("telefono", "celular"):
            if not re.fullmatch(r"[0-9]{10}", valores[campo]):
                raise EdicionInvalida(f"El campo {campo} debe contener 10 digitos")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", valores["correo"]):
            raise EdicionInvalida("Correo electronico invalido")

    @staticmethod
    def _serializar(solicitud, turno):
        municipio = db.session.get(Municipio, turno.id_municipio)
        nivel = db.session.get(NivelEducativo, solicitud.id_nivel)
        asunto = db.session.get(Asunto, solicitud.id_asunto)
        return {
            "folio": turno.folio,
            "numero_turno": turno.numero_turno,
            "municipio": municipio.nombre if municipio else "",
            "curp": solicitud.curp,
            "responsable": solicitud.responsable,
            "nombre": solicitud.nombre,
            "paterno": solicitud.paterno,
            "materno": solicitud.materno,
            "telefono": solicitud.telefono,
            "celular": solicitud.celular,
            "correo": solicitud.correo,
            "nivel": nivel.nombre if nivel else "",
            "asunto": asunto.nombre if asunto else "",
            "estatus": solicitud.estatus,
        }
