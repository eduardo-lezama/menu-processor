"""
Punto de entrada para ejecutar el servicio en desarrollo
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
