from datetime import datetime, timedelta
import jwt

from main import SECRET_KEY
from tests.conftest import client, limpar_cadastro, cadastrar, logar, cabecalho


def test_1_login_com_senha_certa_devolve_token():
    limpar_cadastro("email")
    cadastrar("Ana", "ana@email.com", "senha123")
    resposta = logar("ana@email.com", "senha123")
    assert resposta.status_code == 200
    assert "token" in resposta.json()


def test_2_login_com_senha_errada_devolve_401():
    limpar_cadastro("email")
    cadastrar("Ana", "ana@email.com", "senha123")
    resposta = logar("ana@email.com", "senha_errada")
    assert resposta.status_code == 401


def test_3_login_com_senha_inexistente_devolve_404():
    limpar_cadastro("email")
    cadastrar("Max", "max@email.com", "senha123")
    resposta = logar("caroline@email.com", "senha123")
    assert resposta.status_code == 404


def test_4_rota_protegida_sem_token_devolve_401_ou_403():
    limpar_cadastro("email")
    cadastrar("Max", "max@email.com", "senha123")
    resposta = client.get("/perfil")
    assert resposta.status_code == 401 or resposta.status_code == 403


def test_5_rota_protegida_com_token_inválido_devolve_401():
    limpar_cadastro("email")
    cadastrar("Max", "max@email.com", "senha123")
    resposta = client.get("/perfil", headers=cabecalho("token_invalido"))
    assert resposta.status_code == 401


def test_12_token_ja_nasce_vencido():
    limpar_cadastro("email")
    cadastrar("Rosa Linn", "rosaLinn@email.com", "senha123")
    payload = {
        "sub": "rosaLinn@email.com",
        "exp": datetime.now() - timedelta(hours=1)
    }
    token_vencido = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    resposta = client.get("/perfil", headers=cabecalho(token_vencido))
    assert resposta.status_code == 401
