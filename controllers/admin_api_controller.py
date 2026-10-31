
import secrets
from functools import wraps

from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    current_app
)

from sqlalchemy.exc import SQLAlchemyError

from models.usuario import Usuario

from services.admin_solicitud_service import (
    AdminSolicitudService,
    SolicitudNoExiste,
    DatosInvalidos,
)

from services.turno_service import SolicitudInvalida

from services.municipio_service import (
    MunicipioService,
    MunicipioInvalido,
    MunicipioNoEncontrado,
    MunicipioDuplicado,
)
from services.catalogos_service import (
    NivelEducativoService,
    AsuntoService,
    CatalogoInvalido,
    CatalogoNoEncontrado,
    CatalogoDuplicado,
)


# ==========================================
# BLUEPRINT ADMINISTRATIVO
# ==========================================

admin_api_bp = Blueprint(
    "admin_api",
    __name__,
    url_prefix="/api/admin"
)


# ==========================================
# AUTENTICACIÓN Y PROTECCIÓN CSRF
# ==========================================

def admin_api_requerido(func):
    """
    Protege los endpoints administrativos.

    - Comprueba que exista una sesión.
    - Verifica que el administrador esté activo.
    - Valida el token CSRF para POST, PUT,
      PATCH y DELETE.
    """

    @wraps(func)
    def decorador(*args, **kwargs):

        id_usuario = session.get("admin_id")

        if not id_usuario:
            return jsonify({
                "error": (
                    "Acceso no autorizado. "
                    "Inicie sesión como administrador."
                )
            }), 401

        admin = Usuario.query.filter_by(
            id_usuario=id_usuario,
            activo=True
        ).first()

        if not admin:
            session.clear()

            return jsonify({
                "error": "Sesión inválida o expirada."
            }), 401

        # Validación CSRF para operaciones
        # que modifican información
        if request.method in (
            "POST",
            "PUT",
            "PATCH",
            "DELETE"
        ):

            token_cliente = request.headers.get(
                "X-CSRF-Token", ""
            )

            token_servidor = session.get(
                "logout_csrf", ""
            )

            if (
                not token_cliente
                or not token_servidor
                or not secrets.compare_digest(
                    token_cliente,
                    token_servidor
                )
            ):
                return jsonify({
                    "error": (
                        "Token de seguridad CSRF "
                        "inválido o ausente."
                    )
                }), 403

        return func(*args, **kwargs)

    return decorador


# ==========================================
# CRUD ADMINISTRATIVO DE SOLICITUDES
# ==========================================

# GET /api/admin/solicitudes
@admin_api_bp.get("/solicitudes")
@admin_api_requerido
def listar_solicitudes():

    filtros = {
        "curp": request.args.get("curp"),
        "nombre": request.args.get("nombre"),
        "municipio": request.args.get("municipio"),
        "folio": request.args.get("folio"),
        "numero_turno": request.args.get("numero_turno"),
        "estatus": request.args.get("estatus"),
    }

    pagina = request.args.get("pagina", 1)

    return jsonify(
        AdminSolicitudService.listar(
            filtros,
            pagina
        )
    ), 200


# GET /api/admin/solicitudes/<id>
@admin_api_bp.get("/solicitudes/<int:id_solicitud>")
@admin_api_requerido
def detalle_solicitud(id_solicitud):

    try:
        resultado = AdminSolicitudService.obtener(
            id_solicitud
        )

        return jsonify(resultado), 200

    except SolicitudNoExiste as error:
        return jsonify({
            "error": str(error)
        }), 404


# POST /api/admin/solicitudes
@admin_api_bp.post("/solicitudes")
@admin_api_requerido
def crear_solicitud():

    if not request.is_json:
        return jsonify({
            "error": "Se requiere enviar datos JSON"
        }), 415

    try:
        datos = request.get_json(silent=True)

        resultado = AdminSolicitudService.crear(
            datos
        )

        return jsonify(resultado), 201

    except SolicitudInvalida as error:
        return jsonify({
            "error": str(error)
        }), 400

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al crear la solicitud (admin)"
        )

        return jsonify({
            "error": "No se pudo crear la solicitud"
        }), 500


# PUT /api/admin/solicitudes/<id>
@admin_api_bp.put("/solicitudes/<int:id_solicitud>")
@admin_api_requerido
def actualizar_solicitud(id_solicitud):

    if not request.is_json:
        return jsonify({
            "error": "Se requiere enviar datos JSON"
        }), 415

    try:
        datos = request.get_json(silent=True)

        resultado = AdminSolicitudService.actualizar(
            id_solicitud,
            datos
        )

        return jsonify({
            "mensaje": "Solicitud actualizada correctamente",
            **resultado
        }), 200

    except SolicitudNoExiste as error:
        return jsonify({
            "error": str(error)
        }), 404

    except DatosInvalidos as error:
        return jsonify({
            "error": str(error)
        }), 400

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al actualizar la solicitud (admin)"
        )

        return jsonify({
            "error": "No se pudo actualizar la solicitud"
        }), 500


# DELETE /api/admin/solicitudes/<id>
@admin_api_bp.delete("/solicitudes/<int:id_solicitud>")
@admin_api_requerido
def eliminar_solicitud(id_solicitud):

    try:
        resultado = AdminSolicitudService.eliminar(
            id_solicitud
        )

        return jsonify(resultado), 200

    except SolicitudNoExiste as error:
        return jsonify({
            "error": str(error)
        }), 404

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al eliminar la solicitud (admin)"
        )

        return jsonify({
            "error": "No se pudo eliminar la solicitud"
        }), 500



# PATCH /api/admin/solicitudes/<id>/estatus
@admin_api_bp.patch("/solicitudes/<int:id_solicitud>/estatus")
@admin_api_requerido
def cambiar_estatus_solicitud(id_solicitud):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nuevo_estatus = datos.get("estatus")

    if not nuevo_estatus:
        return jsonify({"error": "El campo 'estatus' es obligatorio."}), 400

    try:
        resultado = AdminSolicitudService.cambiar_estatus(id_solicitud, nuevo_estatus)
        return jsonify({
            "mensaje": f"Estatus actualizado a '{resultado['estatus']}' correctamente.",
            "solicitud": resultado
        }), 200

    except SolicitudNoExiste as error:
        return jsonify({"error": str(error)}), 404

    except DatosInvalidos as error:
        return jsonify({"error": str(error)}), 400

    except SQLAlchemyError:
        current_app.logger.exception("Error al actualizar el estatus de la solicitud (admin)")
        return jsonify({"error": "No se pudo actualizar el estatus de la solicitud."}), 500


# ==========================================
# CRUD ADMINISTRATIVO DE MUNICIPIOS
# ==========================================

# GET /api/admin/municipios
@admin_api_bp.get("/municipios")
@admin_api_requerido
def listar_municipios():

    try:
        municipios = MunicipioService.listar(
            solo_activos=False
        )

        return jsonify(municipios), 200

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al consultar municipios"
        )

        return jsonify({
            "error": (
                "Error interno al consultar municipios."
            )
        }), 500


# POST /api/admin/municipios
@admin_api_bp.post("/municipios")
@admin_api_requerido
def crear_municipio():

    if not request.is_json:
        return jsonify({
            "error": (
                "Se requiere enviar datos en formato JSON."
            )
        }), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        nuevo = MunicipioService.crear(nombre)

        return jsonify({
            "mensaje": (
                f"Municipio '{nuevo['nombre']}' "
                "registrado correctamente."
            ),
            "municipio": nuevo
        }), 201

    except MunicipioInvalido as error:
        return jsonify({
            "error": str(error)
        }), 400

    except MunicipioDuplicado as error:
        return jsonify({
            "error": str(error)
        }), 409

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al crear municipio"
        )

        return jsonify({
            "error": (
                "Error interno al registrar "
                "el municipio."
            )
        }), 500


# PUT /api/admin/municipios/<id>
@admin_api_bp.put("/municipios/<int:id_municipio>")
@admin_api_requerido
def actualizar_municipio(id_municipio):

    if not request.is_json:
        return jsonify({
            "error": (
                "Se requiere enviar datos en formato JSON."
            )
        }), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        actualizado = MunicipioService.actualizar(
            id_municipio,
            nombre
        )

        return jsonify({
            "mensaje": (
                f"Municipio actualizado a "
                f"'{actualizado['nombre']}'."
            ),
            "municipio": actualizado
        }), 200

    except MunicipioNoEncontrado as error:
        return jsonify({
            "error": str(error)
        }), 404

    except MunicipioInvalido as error:
        return jsonify({
            "error": str(error)
        }), 400

    except MunicipioDuplicado as error:
        return jsonify({
            "error": str(error)
        }), 409

    except SQLAlchemyError:
        current_app.logger.exception(
            "Error al actualizar municipio"
        )

        return jsonify({
            "error": (
                "Error interno al actualizar "
                "el municipio."
            )
        }), 500


# PATCH /api/admin/municipios/<id>/estado
@admin_api_bp.patch(
    "/municipios/<int:id_municipio>/estado"
)
@admin_api_requerido
def cambiar_estado_municipio(id_municipio):

    if not request.is_json:
        return jsonify({
            "error": (
                "Se requiere enviar datos en formato JSON."
            )
        }), 415

    datos = request.get_json(silent=True) or {}

    if "activo" not in datos:
        return jsonify({
            "error": (
                "El campo 'activo' es obligatorio."
            )
        }), 400

    activo = datos.get("activo")

    try:
        actualizado = MunicipioService.cambiar_estado(
            id_municipio,
            activo
        )

        estado_texto = (
            "activado"
            if actualizado["activo"]
            else "desactivado"
        )

        return jsonify({
            "mensaje": (
                f"Municipio '{actualizado['nombre']}' "
                f"{estado_texto} correctamente."
            ),
            "municipio": actualizado
        }), 200

    except MunicipioNoEncontrado as error:
        return jsonify({
            "error": str(error)
        }), 404

    except MunicipioInvalido as error:
        return jsonify({
            "error": str(error)
        }), 400

    except SQLAlchemyError:
        current_app.logger.exception("Error al cambiar estado del municipio")
        return jsonify({"error": "Error interno al cambiar el estado del municipio."}), 500


# ==========================================================
# ENDPOINTS: NIVELES EDUCATIVOS
# ==========================================================

@admin_api_bp.get("/niveles")
@admin_api_requerido
def listar_niveles():
    try:
        niveles = NivelEducativoService.listar(solo_activos=False)
        return jsonify(niveles), 200
    except SQLAlchemyError:
        current_app.logger.exception("Error al consultar niveles educativos")
        return jsonify({"error": "Error interno al consultar niveles educativos."}), 500


@admin_api_bp.post("/niveles")
@admin_api_requerido
def crear_nivel():
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        nuevo = NivelEducativoService.crear(nombre)
        return jsonify({
            "mensaje": f"Nivel educativo '{nuevo['nombre']}' registrado correctamente.",
            "registro": nuevo
        }), 201
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al crear nivel educativo")
        return jsonify({"error": "Error interno al registrar el nivel educativo."}), 500


@admin_api_bp.put("/niveles/<int:id_nivel>")
@admin_api_requerido
def actualizar_nivel(id_nivel):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        actualizado = NivelEducativoService.actualizar(id_nivel, nombre)
        return jsonify({
            "mensaje": f"Nivel educativo actualizado a '{actualizado['nombre']}'.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al actualizar nivel educativo")
        return jsonify({"error": "Error interno al actualizar el nivel educativo."}), 500


@admin_api_bp.patch("/niveles/<int:id_nivel>/estado")
@admin_api_requerido
def cambiar_estado_nivel(id_nivel):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    if "activo" not in datos:
        return jsonify({"error": "El campo 'activo' es obligatorio."}), 400

    activo = datos.get("activo")

    try:
        actualizado = NivelEducativoService.cambiar_estado(id_nivel, activo)
        estado_texto = "activado" if actualizado["activo"] else "desactivado"
        return jsonify({
            "mensaje": f"Nivel educativo '{actualizado['nombre']}' {estado_texto} correctamente.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("Error al cambiar estado del nivel educativo")
        return jsonify({"error": "Error interno al cambiar el estado del nivel educativo."}), 500


# ==========================================================
# ENDPOINTS: ASUNTOS
# ==========================================================

@admin_api_bp.get("/asuntos")
@admin_api_requerido
def listar_asuntos():
    try:
        asuntos = AsuntoService.listar(solo_activos=False)
        return jsonify(asuntos), 200
    except SQLAlchemyError:
        current_app.logger.exception("Error al consultar asuntos")
        return jsonify({"error": "Error interno al consultar asuntos."}), 500


@admin_api_bp.post("/asuntos")
@admin_api_requerido
def crear_asunto():
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        nuevo = AsuntoService.crear(nombre)
        return jsonify({
            "mensaje": f"Asunto '{nuevo['nombre']}' registrado correctamente.",
            "registro": nuevo
        }), 201
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al crear asunto")
        return jsonify({"error": "Error interno al registrar el asunto."}), 500


@admin_api_bp.put("/asuntos/<int:id_asunto>")
@admin_api_requerido
def actualizar_asunto(id_asunto):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")

    try:
        actualizado = AsuntoService.actualizar(id_asunto, nombre)
        return jsonify({
            "mensaje": f"Asunto actualizado a '{actualizado['nombre']}'.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except CatalogoDuplicado as error:
        return jsonify({"error": str(error)}), 409
    except SQLAlchemyError:
        current_app.logger.exception("Error al actualizar asunto")
        return jsonify({"error": "Error interno al actualizar el asunto."}), 500


@admin_api_bp.patch("/asuntos/<int:id_asunto>/estado")
@admin_api_requerido
def cambiar_estado_asunto(id_asunto):
    if not request.is_json:
        return jsonify({"error": "Se requiere enviar datos en formato JSON."}), 415

    datos = request.get_json(silent=True) or {}
    if "activo" not in datos:
        return jsonify({"error": "El campo 'activo' es obligatorio."}), 400

    activo = datos.get("activo")

    try:
        actualizado = AsuntoService.cambiar_estado(id_asunto, activo)
        estado_texto = "activado" if actualizado["activo"] else "desactivado"
        return jsonify({
            "mensaje": f"Asunto '{actualizado['nombre']}' {estado_texto} correctamente.",
            "registro": actualizado
        }), 200
    except CatalogoNoEncontrado as error:
        return jsonify({"error": str(error)}), 404
    except CatalogoInvalido as error:
        return jsonify({"error": str(error)}), 400
    except SQLAlchemyError:
        current_app.logger.exception("Error al cambiar estado del asunto")
        return jsonify({"error": "Error interno al cambiar el estado del asunto."}), 500
