from flask import Flask
from config import Config
from extensions import db, migrate
from controllers.publico_controller import publico_bp
import models  # Registra los modelos para SQLAlchemy y Flask-Migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("Configura DATABASE_URL en el archivo .env")
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(publico_bp)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
