"""
Tests básicos de la aplicación Flask
"""


def test_app_creates_successfully(app):
    """La app debe crearse correctamente"""
    assert app is not None
    assert app.config["TESTING"] is True


def test_health_endpoint_returns_ok(client):
    """GET /api/health debe retornar status healthy"""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "menu-processor"


def test_index_page_loads(client):
    """GET / debe cargar la página principal"""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Menu Processor" in response.data
