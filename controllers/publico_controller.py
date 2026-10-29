from flask import Blueprint, render_template, Response, abort

from services.comprobante_service import ComprobanteService, ComprobanteNoEncontrado
from services.comprobante_pdf import ComprobantePDF
from services.qr_service import QrService

publico_bp = Blueprint("publico", __name__)


@publico_bp.get("/")
def inicio():
    return render_template("inicio.html")


@publico_bp.get("/crear-turno")
def crear_turno():
    return render_template("ticket.html")


@publico_bp.get("/editar-turno")
def editar_turno():
    return render_template("editar_turno.html")


@publico_bp.get("/comprobante/<folio>")
def comprobante(folio):
    try:
        datos = ComprobanteService.obtener_por_folio(folio)
    except ComprobanteNoEncontrado:
        abort(404)

    qr = QrService.data_uri(datos["curp"])
    return render_template("comprobante.html", datos=datos, qr=qr)


@publico_bp.get("/comprobante/<folio>/pdf")
def comprobante_pdf(folio):
    try:
        datos = ComprobanteService.obtener_por_folio(folio)
    except ComprobanteNoEncontrado:
        abort(404)

    pdf = ComprobantePDF.generar(datos)
    archivo = f"comprobante_{datos['folio']}.pdf"
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={archivo}"},
    )
