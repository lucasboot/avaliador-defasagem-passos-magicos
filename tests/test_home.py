"""
Testes para o endpoint GET / (home).
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_retorna_200():
    """GET / retorna status 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_home_retorna_html():
    """GET / retorna HTML."""
    response = client.get("/")
    assert "text/html" in response.headers.get("content-type", "")


def test_home_contem_titulo():
    """Página contém o título do projeto."""
    response = client.get("/")
    assert "Classificador de Risco de Defasagem" in response.text


def test_home_contem_textarea():
    """Página contém textarea para input."""
    response = client.get("/")
    assert 'id="student-text"' in response.text or "student-text" in response.text


def test_home_contem_botao_classificar():
    """Página contém botão Classificar."""
    response = client.get("/")
    assert "Classificar" in response.text
