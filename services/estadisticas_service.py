
from sqlalchemy import func, case

from extensions import db
from models import Solicitud, Municipio


class EstadisticasService:

    @staticmethod
    def obtener(id_municipio=None):
        # Estadísticas generales o de un municipio.
        consulta = db.session.query(
            func.count(Solicitud.id_solicitud).label("total"),
            func.coalesce(
                func.sum(
                    case(
                        (Solicitud.estatus == "Pendiente", 1),
                        else_=0
                    )
                ), 0
            ).label("pendientes"),
            func.coalesce(
                func.sum(
                    case(
                        (Solicitud.estatus == "Resuelto", 1),
                        else_=0
                    )
                ), 0
            ).label("resueltas")
        )

        if id_municipio is not None:
            consulta = consulta.filter(
                Solicitud.id_municipio == id_municipio
            )

        resultado = consulta.one()

        # Conteo para la gráfica de municipios.
        por_municipio = (
            db.session.query(
                Municipio.nombre,
                func.count(Solicitud.id_solicitud)
            )
            .outerjoin(
                Solicitud,
                Solicitud.id_municipio == Municipio.id_municipio
            )
        )

        if id_municipio is not None:
            por_municipio = por_municipio.filter(
                Municipio.id_municipio == id_municipio
            )

        por_municipio = (
            por_municipio
            .group_by(Municipio.id_municipio, Municipio.nombre)
            .order_by(Municipio.nombre)
            .all()
        )

        return {
            "total": int(resultado.total),
            "pendientes": int(resultado.pendientes),
            "resueltas": int(resultado.resueltas),
            "por_municipio": [
                {
                    "municipio": nombre,
                    "total": int(total)
                }
                for nombre, total in por_municipio
            ]
        }
