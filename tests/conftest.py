"""
Fixtures compartidos para tests de menu-processor
"""

import pytest

from app import create_app


@pytest.fixture
def app():
    """Crear app en modo testing"""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Cliente de test Flask"""
    return app.test_client()
