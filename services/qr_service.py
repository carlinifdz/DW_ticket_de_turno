import io
import base64

import segno


class QrService:
    """Genera el codigo QR que identifica la CURP del solicitante."""

    @staticmethod
    def png_bytes(texto, scale=5, border=2):
        codigo = segno.make(str(texto), error="m")
        buffer = io.BytesIO()
        codigo.save(buffer, kind="png", scale=scale, border=border)
        return buffer.getvalue()

    @staticmethod
    def data_uri(texto, scale=5, border=2):
        png = QrService.png_bytes(texto, scale=scale, border=border)
        codificado = base64.b64encode(png).decode("ascii")
        return "data:image/png;base64," + codificado
