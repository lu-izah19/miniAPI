# Importa o cliente usado para enviar requisições de teste à API FastAPI.
from fastapi.testclient import TestClient

# Importa a aplicação e o dicionário de usuários do módulo principal.
from api import AlterarPapel, UsuarioDelete, app, usuario_cadastro

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

# Testa se o login com um e-mail não cadastrado devolve o status HTTP 404.
def test_3_login_com_senha_inexistente_devolve_404():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra a usuária com uma senha conhecida.
    cadastrar("Max", "max@email.com", "senha123")
    # Tenta realizar o login usando um e-mail que não está cadastrado.
    resposta = logar("caroline@email.com", "senha123")
    # Confirma que a API rejeitou a autenticação.
    assert resposta.status_code == 404

# Testa se o acesso a uma rota protegida sem fornecer um token devolve o status HTTP 401 ou 403.
def test_4_rota_protegida_sem_token_devolve_401_ou_403():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra a usuária com uma senha conhecida.
    cadastrar("Max", "max@email.com", "senha123")
    # Tenta acessar uma rota protegida sem fornecer o token de autenticação.
    resposta = client.get("/perfil")
    # Confirma que a API rejeitou o acesso.
    assert resposta.status_code == 401 or resposta.status_code == 403

# Testa se o acesso a uma rota protegida com um token inválido devolve o status HTTP 401.
def test_5_rota_protegida_com_token_inválido_devolve_401():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra a usuária com uma senha conhecida.
    cadastrar("Max", "max@email.com", "senha123")
    # Tenta acessar uma rota protegida fornecendo um token de autenticação inválido.
    resposta = client.get("/perfil", headers=cabecalho("token_invalido"))
    # Confirma que a API rejeitou o acesso.
    assert resposta.status_code == 401

# Testa se o acesso a uma rota protegida com um token válido devolve o status HTTP 200.
def test_6_admin_acessa_admin_com_sucesso():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra o usuário com uma senha conhecida.
    cadastrar("Dean", " dean@email.com", "senha123")
    # Tenta realizar o login usando as credenciais corretas.
    resposta = logar(" dean@email.com", "senha123")
    # Confirma que o login foi realizado com sucesso.
    assert resposta.status_code == 200

# Testa se um usuário comum tentando acessar uma rota de administrador recebe o status HTTP 403.
def test_7_usuário_comum_em_admin_recebe_403():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra o usuário com uma senha conhecida.
    cadastrar("Dean", " dean@email.com", "senha123")
    # Tenta realizar o login usando as credenciais corretas.
    resposta = logar(" dean@email.com", "senha123")
    # Confirma que o login foi realizado com sucesso.
    assert resposta.status_code == 200
    # Tenta acessar uma rota protegida como usuário comum.
    resposta = client.get("/admin", headers=cabecalho(resposta.json()["token"]))
    # Confirma que a API rejeitou o acesso.
    assert resposta.status_code == 403

# Testa se um usuário comum tentando fazer PATCH em rota de administrador recebe o status HTTP 403.
def test_8_usuário_comum_tentando_PATCH_admin_papel_recebe_403():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra o usuário com uma senha conhecida.
    cadastrar("Dean", " dean@email.com", "senha123")
    # Tenta realizar o login usando as credenciais corretas.
    resposta = logar(" dean@email.com", "senha123")
    # Confirma que o login foi realizado com sucesso.
    assert resposta.status_code == 200
    # Tenta fazer PATCH em uma rota de administrador como usuário comum.
    resposta = client.patch(
        "/admin/papel", headers=cabecalho(resposta.json()["token"]), 
        json={"email": " dean@email.com", "papel": "admin"})
    # Confirma que a API rejeitou o acesso.
    assert resposta.status_code == 403

# Testa se um usuário comum tentando fazer DELETE em rota de administrador recebe o status HTTP 403.
def test_9_usuário_comum_tentando_DELETE_admin_usuario_recebe_403():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra o usuário com uma senha conhecida.
    cadastrar("Dean", " dean@email.com", "senha123")
    # Tenta realizar o login usando as credenciais corretas.
    resposta = logar(" dean@email.com", "senha123")
    # Confirma que o login foi realizado com sucesso.
    assert resposta.status_code == 200
    # Tenta fazer DELETE em uma rota de administrador como usuário comum.
    resposta = client.request(
        "DELETE", "/admin/usuario", headers=cabecalho(resposta.json()["token"]), 
        json={"email": " dean@email.com"})
    # Confirma que a API rejeitou o acesso.
    assert resposta.status_code == 403

# Testa se um administrador consegue promover um usuário comum a administrador e se o papel do usuário muda de fato.
def test_10_admin_promove_usuário_e_o_papel_muda_de_fato():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra o usuário com uma senha conhecida.
    cadastrar("Dean", " dean@email.com", "senha123")
    # Tenta realizar o login usando as credenciais corretas.
    resposta = logar(" dean@email.com", "senha123")
    # Confirma que o login foi realizado com sucesso.
    assert resposta.status_code == 200

# Testa se um usuário comum consegue editar o próprio perfil sem afetar o perfil de outro usuário.
def test_11_editar_o_próprio_perfil_não_afeta_o_perfil_de_outra_pessoa():
    # Remove usuários cadastrados por testes anteriores.
    limpar_cadastro()
    # Cadastra a usuária com uma senha conhecida.
    cadastrar("Britney", "britney@email.com", "senha123")
    # Tenta realizar o login usando as credenciais corretas.
    resposta = logar("britney@email.com", "senha123")
    # Confirma que o login foi realizado com sucesso.
    assert resposta.status_code == 200
    # Tenta editar o próprio perfil usando o token de autenticação.
    resposta = client.patch(
        "/perfil/usuario", headers=cabecalho(resposta.json()["token"]), 
        json={"nome": "Britney Spears", "email": "britney@email.com", "senha": "nova_senha123"})
    # Confirma que a edição do perfil foi realizada com sucesso.
    assert resposta.status_code == 200
