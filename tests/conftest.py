from fastapi.testclient import TestClient
from main import app, usuario_cadastro

client = TestClient(app)


def limpar_cadastro():
    usuario_cadastro.clear()


def cadastrar(nome, email, senha):
    return client.post("/usuario", json={"nome": nome, "email": email, "senha": senha})


def logar(email, senha):
    return client.post("/login", json={"email": email, "senha": senha})


def cabecalho(token):
    return {"Authorization": f"Bearer {token}"}