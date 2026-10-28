import re
from sqlalchemy import select
from extensions import db
from models import Municipio, NivelEducativo, Asunto, Solicitud, Turno

class SolicitudInvalida(ValueError):
    pass

class TurnoService:
    CAMPOS = ("responsable", "curp", "nombre", "paterno", "materno", "telefono", "celular", "correo")

    @staticmethod
    def registrar(datos):
        if not isinstance(datos, dict):
            raise SolicitudInvalida("Datos inválidos")
        valores = {campo: str(datos.get(campo) or "").strip() for campo in TurnoService.CAMPOS}
        valores["curp"] = valores["curp"].upper()
        for campo in ("responsable", "curp", "nombre", "paterno", "materno", "telefono", "celular", "correo"):
            if not valores[campo]:
                raise SolicitudInvalida(f"El campo {campo} es obligatorio")
        if not re.fullmatch(r"[A-Z0-9]{18}", valores["curp"]):
            raise SolicitudInvalida("La CURP debe contener 18 caracteres alfanuméricos")
        for campo in ("telefono", "celular"):
            if not re.fullmatch(r"[0-9]{10}", valores[campo]):
                raise SolicitudInvalida(f"El campo {campo} debe contener 10 dígitos")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", valores["correo"]):
            raise SolicitudInvalida("Correo electrónico inválido")
        nombres = {"municipio": Municipio, "nivel": NivelEducativo, "asunto": Asunto}
        try:
            # El bloqueo FOR UPDATE mantiene un consecutivo seguro por municipio.
            municipio = db.session.execute(select(Municipio).where(
                Municipio.nombre == str(datos.get("municipio", "")), Municipio.activo.is_(True)
            ).with_for_update()).scalar_one_or_none()
            if municipio is None:
                raise SolicitudInvalida("Municipio inválido o inactivo")
            nivel = db.session.execute(select(NivelEducativo).where(NivelEducativo.nombre == str(datos.get("nivel", "")), NivelEducativo.activo.is_(True))).scalar_one_or_none()
            asunto = db.session.execute(select(Asunto).where(Asunto.nombre == str(datos.get("asunto", "")), Asunto.activo.is_(True))).scalar_one_or_none()
            if nivel is None or asunto is None:
                raise SolicitudInvalida("Nivel educativo o asunto inválido")
            municipio.ultimo_turno += 1
            solicitud = Solicitud(**valores, id_nivel=nivel.id_nivel, id_asunto=asunto.id_asunto, id_municipio=municipio.id_municipio)
            db.session.add(solicitud)
            db.session.flush()
            # No se utiliza el campo 'codigo': municipio ID + consecutivo.
            folio = f"M{municipio.id_municipio}-{municipio.ultimo_turno:06d}"
            db.session.add(Turno(id_solicitud=solicitud.id_solicitud, id_municipio=municipio.id_municipio, numero_turno=municipio.ultimo_turno, folio=folio))
            db.session.commit()
            return {"mensaje": "Turno registrado correctamente", "folio": folio, "numero_turno": municipio.ultimo_turno, "municipio": municipio.nombre}
        except Exception:
            db.session.rollback()
            raise
