import io
import base64

import segno


class QrService:
    """Genera el codigo QR que identifica la CURP del solicitante."""

    @staticmethod
    def _codigo(texto):
        # micro=False fuerza un QR estandar, legible por cualquier lector.
        return segno.make(str(texto), error="m", micro=False)

    @staticmethod
    def png_bytes(texto, scale=5, border=2):
        buffer = io.BytesIO()
        QrService._codigo(texto).save(buffer, kind="png", scale=scale, border=border)
        return buffer.getvalue()

    @staticmethod
    def data_uri(texto, scale=5, border=2):
        png = QrService.png_bytes(texto, scale=scale, border=border)
        codificado = base64.b64encode(png).decode("ascii")
        return "data:image/png;base64," + codificado

    @staticmethod
    def matriz(texto):
        # Matriz de 0/1 para dibujar el QR como vectores dentro del PDF.
        return [list(fila) for fila in QrService._codigo(texto).matrix]
