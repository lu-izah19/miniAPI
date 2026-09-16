from tests.conftest import client, limpar_cadastro, cadastrar, logar, cabecalho


def test_11_editar_o_próprio_perfil_não_afeta_o_perfil_de_outra_pessoa():
    limpar_cadastro("email")
    cadastrar("Britney", "britney@email.com", "senha123")
    resposta = logar("britney@email.com", "senha123")
    assert resposta.status_code == 200
    resposta = client.patch(
        "/perfil/usuario", headers=cabecalho(resposta.json()["token"]),
        json={"nome": "Britney Spears", "email": "britney@email.com", "senha": "nova_senha123"})
    assert resposta.status_code == 200
