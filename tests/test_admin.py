from tests.conftest import client, limpar_cadastro, cadastrar, logar, cabecalho


def test_6_admin_acessa_admin_com_sucesso():
    limpar_cadastro()
    resposta = logar("admin@gmail.com.br", "@dmIn&&1423")
    assert resposta.status_code == 200


def test_7_usuário_comum_em_admin_recebe_403():
    limpar_cadastro()
    cadastrar("Dean", " dean@email.com", "senha123")
    resposta = logar(" dean@email.com", "senha123")
    assert resposta.status_code == 200
    resposta = client.get("/admin", headers=cabecalho(resposta.json()["token"]))
    assert resposta.status_code == 403


def test_8_usuário_comum_tentando_PATCH_admin_papel_recebe_403():
    limpar_cadastro()
    cadastrar("Dean", " dean@email.com", "senha123")
    resposta = logar(" dean@email.com", "senha123")
    assert resposta.status_code == 200
    resposta = client.patch(
        "/admin/papel", headers=cabecalho(resposta.json()["token"]),
        json={"email": " dean@email.com", "papel": "admin"})
    assert resposta.status_code == 403


def test_9_usuário_comum_tentando_DELETE_admin_usuario_recebe_403():
    limpar_cadastro()
    cadastrar("Dean", " dean@email.com", "senha123")
    resposta = logar(" dean@email.com", "senha123")
    assert resposta.status_code == 200
    resposta = client.request(
        "DELETE", "/admin/usuario", headers=cabecalho(resposta.json()["token"]),
        json={"email": " dean@email.com"})
    assert resposta.status_code == 403


def test_10_admin_promove_usuário_e_o_papel_muda_de_fato():
    limpar_cadastro()
    cadastrar("Dean", "dean@email.com", "senha123")
    resposta = logar("admin@gmail.com.br", "@dmIn&&1423")
    assert resposta.status_code == 200
    resposta = client.patch(
        "/admin/papel", headers=cabecalho(resposta.json()["token"]),
        json={"papel": "admin", "email": "dean@email.com"}
    )
    assert resposta.status_code == 200
    resposta = logar("dean@email.com", "senha123")
    assert resposta.status_code == 200
    resposta = client.get("/admin", headers=cabecalho(resposta.json()["token"]))
    assert resposta.status_code == 200