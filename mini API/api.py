from fastapi import FastAPI
# Importa o módulo logging para exibir mensagens de status/erro formatadas
import logging

from pydantic import BaseModel

# Configura o sistema de logging para exibir mensagens de nível INFO ou superior
logging.basicConfig(level=logging.INFO)

# Cria a instância da aplicação FastAPI
app = FastAPI()
@app.get("/")
def home():
    return {"message": "Bem-vindo à API!"}

# Texto de menu herdado da versão em terminal; nenhuma rota desta API o utiliza
menu = """
1. Cadastro
2. Login
3. Perfil
4.Sair
"""

# Classe que representa os dados de um usuário (nome, email, senha)
# As rotas abaixo leem e gravam esses dados diretamente nos atributos da classe
# (Usuario.nome, Usuario.email, Usuario.senha), não em uma instância — ou seja,
# os dados ficam compartilhados entre todas as requisições, e não por usuário
class Usuario:
    # Construtor: todos os campos são opcionais para permitir criar o objeto
    # em etapas (primeiro só com nome, depois só com email/senha)
    def __init__(self, nome=None, email=None, senha=None):
        self.nome = nome
        self.email = email
        self.senha = senha

class UsuarioCadastro(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioInicio(BaseModel):
    nome: str

class UsuarioLogin(BaseModel):
    email: str
    senha: str

# Rota GET que recebe o nome do usuário no corpo da requisição
# e registra uma mensagem de boas-vindas no log
@app.get("/usuario")
# Função executada ao acessar a rota GET /usuario
def inicio(dados: UsuarioInicio):
    # Cria uma instância local da classe Usuario apenas para montar a mensagem de boas-vindas
    usuario = Usuario(nome=dados.nome)
    # Loga uma mensagem de boas-vindas personalizada com o nome informado
    logging.info("Olá %s, seja bem vindo(a)!", usuario.nome)
    # Atenção: essa instância não é salva em lugar nenhum; os dados usados pelas
    # outras rotas (cadastro, login, perfil) ficam nos atributos da classe Usuario


# Rota POST que recebe email e senha para cadastro
@app.post("/usuario")
# Função responsável por cadastrar o email e a senha do usuário
def cadastro(dados: UsuarioCadastro):
    # Pede o email do usuário
    email = dados.email
    # Pede a senha do usuário
    senha = dados.senha
    # Declaração sem efeito prático aqui: a variável global "usuario" nunca chega a
    # ser atribuída nesta função — os dados são gravados na classe Usuario abaixo
    global usuario
    # Salva o email como atributo da classe Usuario (não de uma instância)
    Usuario.email = email
    # Salva a senha como atributo da classe Usuario (não de uma instância)
    Usuario.senha = senha
    # Como email e senha são gravados na classe (e não em uma instância), o nome
    # definido em inicio() não é sobrescrito, mas também não é usado por esta rota

    # Retorna uma confirmação de cadastro
    return {"mensagem": "Cadastro realizado com sucesso!"}

# Rota POST para autenticação, recebe email e senha no corpo da requisição
@app.post("/login")
# Função responsável por autenticar o usuário já cadastrado
def login(dados: UsuarioLogin):
    # Pede o email para login
    email_login = dados.email
    # Pede a senha para login
    senha_login = dados.senha
    # Declaração sem efeito prático aqui: a variável global "usuario" nunca é usada
    # nesta função — a comparação abaixo usa os atributos da classe Usuario
    global usuario
    # Compara os dados recebidos com os atributos salvos na classe Usuario
    if email_login == Usuario.email and senha_login == Usuario.senha:
        # Se os dados baterem, loga sucesso no login
        logging.info("Login realizado com sucesso!")
    else:
        logging.warning("Credenciais inválidas!")

# Rota GET para exibir o perfil do usuário
@app.get("/perfil")
# Função que exibe os dados atualmente salvos na classe Usuario
def perfil(dados: Usuario):
    # Declaração sem efeito prático aqui: a variável global "usuario" nunca é usada
    # nesta função — os dados exibidos abaixo vêm dos atributos da classe Usuario
    global usuario
    # Loga que está acessando o perfil
    logging.info("Acessando o perfil do usuário...")
    # Exibe o nome salvo do usuário
    logging.info("nome: %s", Usuario.nome)
    # Exibe o email salvo do usuário
    logging.info("Email: %s", Usuario.email)
    # Informa como sair da tela de perfil (mas nada aqui realmente sai, é só uma instrução)
    logging.info("Para sair do perfil, digite 4.")

# Fim do arquivo: não há bloco "__main__"; a aplicação deve ser iniciada
# externamente, por exemplo com "uvicorn api:app --reload"
