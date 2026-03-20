"""
Vistas HTML para la UI del procesador de menús
"""

from flask import Blueprint, render_template

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Página principal - UI para gestionar menús"""
    return render_template("index.html")
