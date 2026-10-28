from extensions import db

class NivelEducativo(db.Model):
    __tablename__ = "niveles_educativos"
    id_nivel = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)

class Asunto(db.Model):
    __tablename__ = "asuntos"
    id_asunto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
