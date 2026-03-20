"""
Menu Processor - Servicio para procesar menús y generar listas de compra en Mealie
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask


def create_app():
    """Factory function para crear la aplicación Flask"""

    # Cargar variables de entorno
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

    app = Flask(__name__, static_folder="../static", template_folder="../templates")

    # Configuración
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["MEALIE_BASE_URL"] = os.environ.get("MEALIE_BASE_URL", "")
    app.config["MEALIE_API_KEY"] = os.environ.get("MEALIE_API_KEY", "")
    # URL pública de Mealie para enlaces en el navegador (no Docker interno)
    app.config["MEALIE_URL_PUBLIC"] = os.environ.get(
        "MEALIE_URL_PUBLIC", os.environ.get("MEALIE_BASE_URL", "")
    )
    app.config["DATA_DIR"] = Path(__file__).resolve().parent.parent / "data"

    # Asegurar que existe el directorio de datos
    app.config["DATA_DIR"].mkdir(exist_ok=True)

    # Registrar blueprints
    from app.controllers.api import api_bp
    from app.controllers.views import views_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(views_bp)

    return app
