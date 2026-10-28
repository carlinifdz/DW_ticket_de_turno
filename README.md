## Preparación
1. Crea entorno virtual: `python -m venv .venv` y actívalo.
2. Activa el venv con `.\.venv\Scripts\Activate.ps1` en la terminal, estando en la raiz del proyecto   
3. Instala dependencias: `pip install -r requirements.txt`.
4. Copia `.env.example` como `.env` y ajusta usuario, contraseña, servidor y nombre de la base, no modifiques las claves de RECAPTCHA_SITE_KEY ni RECAPTCHA_SECRET_KEY.
5. Genera una key con `python -c "import secrets; print(secrets.token_hex(32))"` y copiala en SECTET_KEY
6. Arranca con `flask --app app run --debug` o `python app.py`.
7. Visita `http://127.0.0.1:5000/`.

Ejecutar flask `--app app crear-admin` para crear un perfil de administrador 

## Estructura
- `models/`: clases ORM que representan las 6 tablas.
- `controllers/`: rutas HTTP y vistas.
- `services/`: reglas de registro y consecutivos.
- `templates/`: vistas HTML originales; selects alimentados desde MySQL.
- `static/`: CSS y JavaScript originales.

## Migraciones
Flask-Migrate queda configurado. **Si ya creaste las tablas manualmente**, no ejecutes `flask db upgrade` sobre migraciones iniciales que pretendan recrearlas. Cuando se adopten migraciones como fuente de verdad, primero se debe establecer una línea base coherente con el esquema existente.

