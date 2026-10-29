import io

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from services.qr_service import QrService


class ComprobantePDF:
    """Construye el comprobante de turno en PDF (reportlab) con el QR de la CURP."""

    @staticmethod
    def generar(datos):
        buffer = io.BytesIO()
        lienzo = canvas.Canvas(buffer, pagesize=A4)
        ancho, alto = A4

        # Encabezado
        lienzo.setFont("Helvetica-Bold", 20)
        lienzo.drawCentredString(ancho / 2, alto - 30 * mm, "Comprobante de Turno")
        lienzo.setFont("Helvetica", 11)
        lienzo.drawCentredString(ancho / 2, alto - 38 * mm, "Sistema de Atencion Escolar")

        # Turno y folio destacados
        lienzo.setFont("Helvetica-Bold", 14)
        lienzo.drawCentredString(
            ancho / 2, alto - 50 * mm,
            f"Turno: {datos['numero_turno']}    Folio: {datos['folio']}",
        )

        # Datos del solicitante
        filas = [
            ("Nombre", datos["nombre"]),
            ("CURP", datos["curp"]),
            ("Responsable", datos["responsable"]),
            ("Telefono", datos["telefono"]),
            ("Celular", datos["celular"]),
            ("Correo", datos["correo"]),
            ("Municipio", datos["municipio"]),
            ("Asunto", datos["asunto"]),
            ("Nivel", datos["nivel"]),
            ("Numero de turno", str(datos["numero_turno"])),
        ]
        y = alto - 65 * mm
        for etiqueta, valor in filas:
            lienzo.setFont("Helvetica-Bold", 12)
            lienzo.drawString(30 * mm, y, f"{etiqueta}:")
            lienzo.setFont("Helvetica", 12)
            lienzo.drawString(70 * mm, y, str(valor))
            y -= 9 * mm

        # Codigo QR vectorial con la CURP
        ComprobantePDF._dibujar_qr(lienzo, datos["curp"], ancho, y - 8 * mm)

        lienzo.showPage()
        lienzo.save()
        return buffer.getvalue()

    @staticmethod
    def _dibujar_qr(lienzo, curp, ancho_pagina, borde_superior):
        matriz = QrService.matriz(curp)
        modulos = len(matriz)
        lado = 1.6 * mm
        tamano = modulos * lado
        x0 = (ancho_pagina - tamano) / 2

        lienzo.setFillColorRGB(0, 0, 0)
        for i, fila in enumerate(matriz):
            for j, valor in enumerate(fila):
                if valor:
                    lienzo.rect(x0 + j * lado, borde_superior - (i + 1) * lado,
                                lado, lado, stroke=0, fill=1)

        lienzo.setFont("Helvetica-Oblique", 9)
        lienzo.drawCentredString(ancho_pagina / 2, borde_superior - tamano - 6 * mm,
                                 "Codigo QR con la CURP del solicitante")
