from extensions import db
from models import Municipio, Solicitud, Turno, NivelEducativo, Asunto


class SolicitudNoEncontrada(LookupError):
    pass


class SolicitudPublicaService:
    """Consulta publica de una solicitud por CURP + municipio + numero de turno."""

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
