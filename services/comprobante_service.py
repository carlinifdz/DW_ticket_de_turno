from extensions import db
from models import Turno, Solicitud, Municipio, Asunto, NivelEducativo


class ComprobanteNoEncontrado(LookupError):
    pass


class ComprobanteService:
    """Reune los datos del comprobante a partir del folio del turno."""

    @staticmethod
    def obtener_por_folio(folio):
        folio = str(folio or "").strip().upper()
        if not folio:
            raise ComprobanteNoEncontrado("Folio no proporcionado")

        turno = Turno.query.filter_by(folio=folio).first()
        if turno is None:
            raise ComprobanteNoEncontrado("No existe un turno con ese folio")

        solicitud = db.session.get(Solicitud, turno.id_solicitud)
        municipio = db.session.get(Municipio, turno.id_municipio)
        asunto = db.session.get(Asunto, solicitud.id_asunto)
        nivel = db.session.get(NivelEducativo, solicitud.id_nivel)

        partes = (solicitud.nombre, solicitud.paterno, solicitud.materno)
        nombre_completo = " ".join(p for p in partes if p)

        return {
            "folio": turno.folio,
            "numero_turno": turno.numero_turno,
            "curp": solicitud.curp,
            "nombre": nombre_completo,
            "responsable": solicitud.responsable,
            "municipio": municipio.nombre if municipio else "",
            "asunto": asunto.nombre if asunto else "",
            "nivel": nivel.nombre if nivel else "",
            "estatus": solicitud.estatus,
            "fecha": turno.fecha_asignacion,
        }
