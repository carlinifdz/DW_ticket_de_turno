from sqlalchemy import func
from extensions import db
from models.catalogos import NivelEducativo, Asunto


class CatalogoInvalido(ValueError):
    pass


class CatalogoNoEncontrado(LookupError):
    pass


class CatalogoDuplicado(ValueError):
    pass


class CatalogoBaseService:
    """Clase base genérica para la gestión de catálogos simples (id, nombre, activo)."""

    modelo = None
    campo_id = ""
    max_longitud = 100
    entidad_nombre = "elemento"

    @classmethod
    def _validar_nombre(cls, nombre: str) -> str:
        nombre_limpio = (nombre or "").strip()
        if not nombre_limpio:
            raise CatalogoInvalido(f"El nombre de {cls.entidad_nombre} es obligatorio.")

        if len(nombre_limpio) > cls.max_longitud:
            raise CatalogoInvalido(
                f"El nombre no puede exceder {cls.max_longitud} caracteres."
            )

        return nombre_limpio

    @classmethod
    def serializar(cls, registro) -> dict:
        return {
            "id": getattr(registro, cls.campo_id),
            "nombre": registro.nombre,
            "activo": bool(registro.activo),
        }

    @classmethod
    def listar(cls, solo_activos: bool = False) -> list[dict]:
        query = cls.modelo.query
        if solo_activos:
            query = query.filter_by(activo=True)

        registros = query.order_by(cls.modelo.nombre.asc()).all()
        return [cls.serializar(r) for r in registros]

    @classmethod
    def obtener_por_id(cls, id_registro: int):
        registro = db.session.get(cls.modelo, id_registro)
        if not registro:
            raise CatalogoNoEncontrado(f"{cls.entidad_nombre.capitalize()} no encontrado.")
        return registro

    @classmethod
    def crear(cls, nombre: str) -> dict:
        nombre_limpio = cls._validar_nombre(nombre)

        existente = cls.modelo.query.filter(
            func.lower(cls.modelo.nombre) == func.lower(nombre_limpio)
        ).first()

        if existente:
            raise CatalogoDuplicado(
                f"Ya existe un registro con el nombre '{nombre_limpio}'."
            )

        nuevo = cls.modelo(
            nombre=nombre_limpio,
            activo=True
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            return cls.serializar(nuevo)
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def actualizar(cls, id_registro: int, nuevo_nombre: str) -> dict:
        nombre_limpio = cls._validar_nombre(nuevo_nombre)
        registro = cls.obtener_por_id(id_registro)

        columna_id = getattr(cls.modelo, cls.campo_id)
        existente = cls.modelo.query.filter(
            func.lower(cls.modelo.nombre) == func.lower(nombre_limpio),
            columna_id != id_registro
        ).first()

        if existente:
            raise CatalogoDuplicado(
                f"Ya existe otro registro con el nombre '{nombre_limpio}'."
            )

        registro.nombre = nombre_limpio

        try:
            db.session.commit()
            return cls.serializar(registro)
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def cambiar_estado(cls, id_registro: int, activo: bool) -> dict:
        if not isinstance(activo, bool):
            raise CatalogoInvalido("El valor del estado activo debe ser booleano.")

        registro = cls.obtener_por_id(id_registro)
        registro.activo = activo

        try:
            db.session.commit()
            return cls.serializar(registro)
        except Exception:
            db.session.rollback()
            raise


class NivelEducativoService(CatalogoBaseService):
    modelo = NivelEducativo
    campo_id = "id_nivel"
    max_longitud = 80
    entidad_nombre = "nivel educativo"


class AsuntoService(CatalogoBaseService):
    modelo = Asunto
    campo_id = "id_asunto"
    max_longitud = 100
    entidad_nombre = "asunto"
