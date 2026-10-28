from extensions import db

class Solicitud(db.Model):
    __tablename__ = "solicitudes"
    id_solicitud = db.Column(db.Integer, primary_key=True)
    responsable = db.Column(db.String(150), nullable=False)
    curp = db.Column(db.CHAR(18), nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    paterno = db.Column(db.String(100), nullable=False)
    materno = db.Column(db.String(100))
    telefono = db.Column(db.String(10))
    celular = db.Column(db.String(10))
    correo = db.Column(db.String(150))
    id_nivel = db.Column(db.Integer, db.ForeignKey("niveles_educativos.id_nivel"), nullable=False)
    id_asunto = db.Column(db.Integer, db.ForeignKey("asuntos.id_asunto"), nullable=False)
    id_municipio = db.Column(db.Integer, db.ForeignKey("municipios.id_municipio"), nullable=False)
    estatus = db.Column(db.Enum("Pendiente", "Resuelto"), nullable=False, default="Pendiente")
    fecha_solicitud = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    __table_args__ = (db.UniqueConstraint("id_solicitud", "id_municipio", name="uq_solicitud_municipio"),)
