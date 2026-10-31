import re

from sqlalchemy import or_

from extensions import db
from models import Solicitud, Turno, Municipio, NivelEducativo, Asunto
from services.turno_service import TurnoService


class SolicitudNoExiste(LookupError):
    pass


class DatosInvalidos(ValueError):
    pass


class AdminSolicitudService:
    """CRUD administrativo de solicitudes con filtros y paginacion."""

    POR_PAGINA = 10
    EDITABLES = ("responsable", "curp", "nombre", "paterno", "materno",
                 "telefono", "celular", "correo")

    @staticmethod
    def listar(filtros=None, pagina=1):
        filtros = filtros or {}
        consulta = (
            db.session.query(Solicitud, Turno, Municipio, Asunto)
            .join(Turno, Turno.id_solicitud == Solicitud.id_solicitud)
            .join(Municipio, Municipio.id_municipio == Solicitud.id_municipio)
            .join(Asunto, Asunto.id_asunto == Solicitud.id_asunto)
        )

        curp = str(filtros.get("curp") or "").strip().upper()
        if curp:
            consulta = consulta.filter(Solicitud.curp.like(f"%{curp}%"))

        nombre = str(filtros.get("nombre") or "").strip()
        if nombre:
            patron = f"%{nombre}%"
            consulta = consulta.filter(or_(
                Solicitud.nombre.like(patron),
                Solicitud.paterno.like(patron),
                Solicitud.materno.like(patron),
            ))

        municipio = str(filtros.get("municipio") or "").strip()
        if municipio:
            consulta = consulta.filter(Municipio.nombre == municipio)

        folio = str(filtros.get("folio") or "").strip().upper()
        if folio:
            consulta = consulta.filter(Turno.folio.like(f"%{folio}%"))

        numero = str(filtros.get("numero_turno") or "").strip()
        if numero.isdigit():
            consulta = consulta.filter(Turno.numero_turno == int(numero))

        estatus = str(filtros.get("estatus") or "").strip()
        if estatus in ("Pendiente", "Resuelto"):
            consulta = consulta.filter(Solicitud.estatus == estatus)

        total = consulta.count()

        try:
            pagina = max(1, int(pagina))
        except (TypeError, ValueError):
            pagina = 1

        por_pagina = AdminSolicitudService.POR_PAGINA
        paginas = max(1, (total + por_pagina - 1) // por_pagina)
        pagina = min(pagina, paginas)

        filas = (
            consulta.order_by(Turno.id_turno.desc())
            .limit(por_pagina)
            .offset((pagina - 1) * por_pagina)
            .all()
        )

        return {
            "total": total,
            "pagina": pagina,
            "paginas": paginas,
            "solicitudes": [
                AdminSolicitudService._resumen(s, t, m, a)
                for s, t, m, a in filas
            ],
        }

    @staticmethod
    def _resumen(solicitud, turno, municipio, asunto):
        nombre = " ".join(
            p for p in (solicitud.nombre, solicitud.paterno, solicitud.materno) if p
        )
        return {
            "id": solicitud.id_solicitud,
            "folio": turno.folio,
            "numero_turno": turno.numero_turno,
            "nombre": nombre,
            "curp": solicitud.curp,
            "municipio": municipio.nombre,
            "asunto": asunto.nombre,
            "estatus": solicitud.estatus,
            "fecha": (
                solicitud.fecha_solicitud.strftime("%Y-%m-%d %H:%M")
                if solicitud.fecha_solicitud else ""
            ),
        }

    @staticmethod
    def obtener(id_solicitud):
        solicitud = db.session.get(Solicitud, id_solicitud)
        if solicitud is None:
            raise SolicitudNoExiste("La solicitud no existe")

        turno = Turno.query.filter_by(id_solicitud=id_solicitud).first()
        municipio = db.session.get(Municipio, solicitud.id_municipio)
        nivel = db.session.get(NivelEducativo, solicitud.id_nivel)
        asunto = db.session.get(Asunto, solicitud.id_asunto)

        return {
            "id": solicitud.id_solicitud,
            "folio": turno.folio if turno else "",
            "numero_turno": turno.numero_turno if turno else None,
            "responsable": solicitud.responsable,
            "curp": solicitud.curp,
            "nombre": solicitud.nombre,
            "paterno": solicitud.paterno,
            "materno": solicitud.materno,
            "telefono": solicitud.telefono,
            "celular": solicitud.celular,
            "correo": solicitud.correo,
            "municipio": municipio.nombre if municipio else "",
            "nivel": nivel.nombre if nivel else "",
            "asunto": asunto.nombre if asunto else "",
            "estatus": solicitud.estatus,
        }

    @staticmethod
    def crear(datos):
        # Reutiliza el registro publico: asigna el consecutivo por municipio.
        return TurnoService.registrar(datos)

    @staticmethod
    def actualizar(id_solicitud, datos):
        solicitud = db.session.get(Solicitud, id_solicitud)
        if solicitud is None:
            raise SolicitudNoExiste("La solicitud no existe")

        datos = datos or {}
        valores = {
            campo: str(datos.get(campo) or "").strip()
            for campo in AdminSolicitudService.EDITABLES
        }
        valores["curp"] = valores["curp"].upper()

        for campo in AdminSolicitudService.EDITABLES:
            if not valores[campo]:
                raise DatosInvalidos(f"El campo {campo} es obligatorio")
        if not re.fullmatch(r"[A-Z0-9]{18}", valores["curp"]):
            raise DatosInvalidos("La CURP debe tener 18 caracteres alfanumericos")
        for campo in ("telefono", "celular"):
            if not re.fullmatch(r"[0-9]{10}", valores[campo]):
                raise DatosInvalidos(f"El campo {campo} debe tener 10 digitos")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", valores["correo"]):
            raise DatosInvalidos("Correo electronico invalido")

        nivel = NivelEducativo.query.filter_by(
            nombre=str(datos.get("nivel") or "")
        ).first()
        asunto = Asunto.query.filter_by(
            nombre=str(datos.get("asunto") or "")
        ).first()
        if nivel is None or asunto is None:
            raise DatosInvalidos("Nivel educativo o asunto invalido")

        estatus = str(datos.get("estatus") or solicitud.estatus).strip()
        if estatus not in ("Pendiente", "Resuelto"):
            raise DatosInvalidos("Estatus invalido")

        try:
            for campo, valor in valores.items():
                setattr(solicitud, campo, valor)
            solicitud.id_nivel = nivel.id_nivel
            solicitud.id_asunto = asunto.id_asunto
            solicitud.estatus = estatus
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return AdminSolicitudService.obtener(id_solicitud)

    @staticmethod
    def eliminar(id_solicitud):
        solicitud = db.session.get(Solicitud, id_solicitud)
        if solicitud is None:
            raise SolicitudNoExiste("La solicitud no existe")

        try:
            Turno.query.filter_by(id_solicitud=id_solicitud).delete()
            db.session.delete(solicitud)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {"mensaje": "Solicitud eliminada correctamente"}
