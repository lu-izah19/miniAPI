# Importa o cliente usado para enviar requisições de teste à API FastAPI.
from fastapi.testclient import TestClient

# Importa a aplicação e o dicionário de usuários do módulo principal.
from api import app, usuario_cadastro

# Cria um cliente de teste conectado à aplicação.
client = TestClient(app)


# Define uma função auxiliar para limpar os usuários antes de cada teste.
def limpar_cadastro():
    # Zera o dicionário para que um teste não interfira nos outros.
    usuario_cadastro.clear()


# Define uma função auxiliar para enviar uma requisição de cadastro.
def cadastrar(nome, email, senha):
    # Envia nome, e-mail e senha no corpo da requisição POST.
    return client.post("/usuario", json={"nome": nome, "email": email, "senha": senha})


# Define uma função auxiliar para enviar uma requisição de login.
def logar(email, senha):
    # Envia e-mail e senha no corpo da requisição POST.
    return client.post("/login", json={"email": email, "senha": senha})


# Define uma função auxiliar para montar o cabeçalho de autenticação.
def cabecalho(token):
    # Cria o formato exigido pela autenticação Bearer.
    return {"Authorization": f"Bearer {token}"}


# Testa se o login com a senha correta devolve um token.
def test_1_login_com_senha_certa_devolve_token():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra a usuária usada neste teste.
    cadastrar("Ana", "ana@email.com", "senha123")

    # Realiza o login com as credenciais corretas.
    resposta = logar("ana@email.com", "senha123")

    # Confirma que o login foi realizado com sucesso.
    assert resposta.status_code == 200
    # Confirma que a resposta contém um token de autenticação.
    assert "token" in resposta.json()


# Testa se o login com a senha errada devolve o status HTTP 401.
def test_2_login_com_senha_errada_devolve_401():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra a usuária com uma senha conhecida.
    cadastrar("Ana", "ana@email.com", "senha123")

    # Tenta realizar o login usando uma senha incorreta.
    resposta = logar("ana@email.com", "senha_errada")

    # Confirma que a API rejeitou a autenticação.
    assert resposta.status_code == 401


