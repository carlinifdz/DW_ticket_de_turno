from extensions import db

class Municipio(db.Model):
    __tablename__ = "municipios"
    id_municipio = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    ultimo_turno = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
