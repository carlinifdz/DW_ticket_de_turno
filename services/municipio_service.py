from sqlalchemy import func
from extensions import db
from models.municipio import Municipio


class MunicipioInvalido(ValueError):
    pass


class MunicipioNoEncontrado(LookupError):
    pass


class MunicipioDuplicado(ValueError):
    pass


class MunicipioService:
    """Reglas de negocio y operaciones de base de datos para el catálogo de municipios."""

    MAX_LONGITUD_NOMBRE = 100

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        nombre_limpio = (nombre or "").strip()
        if not nombre_limpio:
            raise MunicipioInvalido("El nombre del municipio es obligatorio.")

        if len(nombre_limpio) > MunicipioService.MAX_LONGITUD_NOMBRE:
            raise MunicipioInvalido(
                f"El nombre no puede exceder {MunicipioService.MAX_LONGITUD_NOMBRE} caracteres."
            )

        return nombre_limpio

    @staticmethod
    def serializar(municipio: Municipio) -> dict:
        return {
            "id_municipio": municipio.id_municipio,
            "nombre": municipio.nombre,
            "ultimo_turno": municipio.ultimo_turno,
            "activo": bool(municipio.activo),
        }

    @staticmethod
    def listar(solo_activos: bool = False) -> list[dict]:
        query = Municipio.query
        if solo_activos:
            query = query.filter_by(activo=True)

        municipios = query.order_by(Municipio.nombre.asc()).all()
        return [MunicipioService.serializar(m) for m in municipios]

    @staticmethod
    def obtener_por_id(id_municipio: int) -> Municipio:
        municipio = db.session.get(Municipio, id_municipio)
        if not municipio:
            raise MunicipioNoEncontrado("Municipio no encontrado.")
        return municipio

    @staticmethod
    def crear(nombre: str) -> dict:
        nombre_limpio = MunicipioService._validar_nombre(nombre)

        # Validar duplicados sin distinguir mayúsculas/minúsculas
        existente = Municipio.query.filter(
            func.lower(Municipio.nombre) == func.lower(nombre_limpio)
        ).first()

        if existente:
            raise MunicipioDuplicado(
                f"Ya existe un municipio registrado con el nombre '{nombre_limpio}'."
            )

        nuevo = Municipio(
            nombre=nombre_limpio,
            ultimo_turno=0,
            activo=True
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            return MunicipioService.serializar(nuevo)
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def actualizar(id_municipio: int, nuevo_nombre: str) -> dict:
        nombre_limpio = MunicipioService._validar_nombre(nuevo_nombre)
        municipio = MunicipioService.obtener_por_id(id_municipio)

        # Validar si otro municipio ya tiene ese nombre
        existente = Municipio.query.filter(
            func.lower(Municipio.nombre) == func.lower(nombre_limpio),
            Municipio.id_municipio != id_municipio
        ).first()

        if existente:
            raise MunicipioDuplicado(
                f"Ya existe otro municipio con el nombre '{nombre_limpio}'."
            )

        # No se modifica ultimo_turno para proteger el consecutivo
        municipio.nombre = nombre_limpio

        try:
            db.session.commit()
            return MunicipioService.serializar(municipio)
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def cambiar_estado(id_municipio: int, activo: bool) -> dict:
        if not isinstance(activo, bool):
            raise MunicipioInvalido("El valor del estado activo debe ser booleano.")

        municipio = MunicipioService.obtener_por_id(id_municipio)
        municipio.activo = activo

        try:
            db.session.commit()
            return MunicipioService.serializar(municipio)
        except Exception:
            db.session.rollback()
            raise
