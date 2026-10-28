from extensions import db

class Turno(db.Model):
    __tablename__ = "turnos"
    id_turno = db.Column(db.Integer, primary_key=True)
    id_solicitud = db.Column(db.Integer, nullable=False, unique=True)
    id_municipio = db.Column(db.Integer, db.ForeignKey("municipios.id_municipio"), nullable=False)
    numero_turno = db.Column(db.Integer, nullable=False)
    folio = db.Column(db.String(30), nullable=False, unique=True)
    fecha_asignacion = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    __table_args__ = (
        db.ForeignKeyConstraint(["id_solicitud", "id_municipio"], ["solicitudes.id_solicitud", "solicitudes.id_municipio"], name="fk_turno_solicitud_municipio"),
        db.UniqueConstraint("id_municipio", "numero_turno", name="uq_turno_municipio"),
        db.CheckConstraint("numero_turno >= 1", name="chk_numero_turno"),
    )
