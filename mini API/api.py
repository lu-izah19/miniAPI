import email

from fastapi import FastAPI
# Módulo padrão de logging, usado no lugar de print() para as mensagens de status/erro
import logging

import bcrypt

from pydantic import BaseModel

# Define o nível mínimo de log exibido como INFO (mostra INFO, WARNING, ERROR, etc.)
logging.basicConfig(level=logging.INFO)

# Instância principal da aplicação FastAPI
app = FastAPI()
@app.get("/")
def home():
    return {"message": "Bem-vindo à API!"}

# Texto de menu herdado da versão em terminal do projeto; nenhuma rota desta API o utiliza
menu = """
1. Cadastro
2. Login
3. Perfil
4.Sair
"""

# Classe genérica para guardar os dados de um usuário (nome, email, senha).
# É usada tanto para a instância local descartável de inicio() quanto para os
# objetos guardados no dicionário global usuario_cadastro, preenchidos em
# cadastro() e lidos em login() e perfil()
class Usuario:
    # Todos os campos são opcionais para permitir montar o objeto com dados parciais
    # (ex: inicio() usa só o nome; cadastro() usa só email e senha)
    def __init__(self, nome=None, email=None, senha=None):
        self.nome = nome
        self.email = email
        self.senha = senha

usuario_cadastro = {}
# Dicionário global que guarda os usuários cadastrados, indexados pelo email

# Modelo de validação do corpo da requisição de cadastro (POST /usuario)
class UsuarioCadastro(BaseModel):
    nome: str
    email: str
    senha: str

# Modelo de validação do corpo da requisição de boas-vindas (GET /usuario)
class UsuarioInicio(BaseModel):
    nome: str

# Modelo de validação do corpo da requisição de login (POST /login)
class UsuarioLogin(BaseModel):
    email: str
    senha: str

# Modelo não utilizado atualmente: a rota GET /perfil/{email} passou a receber
# o email como parâmetro de path (veja perfil()), em vez de um corpo de requisição
class UsuarioPerfil(BaseModel):
    nome: str
    email: str

# Rota GET que recebe o nome do usuário e registra uma mensagem de boas-vindas no log
@app.get("/usuario")
def inicio(dados: UsuarioInicio):
    # Instância local usada só para montar a mensagem de boas-vindas;
    # não é salva em nenhuma variável global, então não afeta as demais rotas
    usuario = Usuario(nome=dados.nome)
    # Loga a mensagem de boas-vindas personalizada com o nome informado
    logging.info("Olá %s, seja bem vindo(a)!", usuario.nome)


# Rota POST que recebe email e senha e efetua o cadastro do usuário
@app.post("/usuario")
def cadastro(dados: UsuarioCadastro):
    email = dados.email
    senha_hash = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
    # Grava o cadastro no dicionário global usuario_cadastro, usando o email como
    # chave e uma instância de Usuario como valor (nome não é informado aqui,
    # então permanece None); login() e perfil() leem os dados a partir desse
    # mesmo dicionário global, buscando pela chave email
    global usuario_cadastro
    novo_usuario = Usuario(nome=None, email=email, senha=senha_hash)
    usuario_cadastro[email] = novo_usuario
    # Confirma o cadastro para quem chamou a rota
    return {"mensagem": "Cadastro realizado com sucesso!"}

# Rota POST para autenticação, recebe email e senha no corpo da requisição
@app.post("/login")
def login(dados: UsuarioLogin):
    email_login = dados.email
    senha_login = dados.senha

    
    # Compara os dados recebidos com os dados salvos em usuario_cadastro (definidos
    # em cadastro()). Se o email não estiver cadastrado, usuario_cadastro[email_login]
    # levanta KeyError, pois usuario_cadastro é um dicionário vazio por padrão
    if email_login == usuario_cadastro[email_login].email and bcrypt.checkpw(senha_login.encode('utf-8'), usuario_cadastro[email_login].senha):
        # Credenciais conferem: loga sucesso no login
        logging.info("Login realizado com sucesso!")
    else:
        # Credenciais não conferem: loga aviso de credenciais inválidas
        logging.warning("Credenciais inválidas!")

# Rota GET para exibir o perfil do usuário
@app.get("/perfil/{email}")
def perfil(email: str):

    # email vem do path da URL (/perfil/{email}) e é usado para buscar o usuário
    # em usuario_cadastro (definidos em cadastro()). Se o email não estiver
    # cadastrado, a busca abaixo levanta KeyError. Como cadastro() nunca define
    # o nome, o campo "nome" logado abaixo sempre aparece como None

    logging.info("Acessando o perfil do usuário...")
    logging.info("nome: %s", usuario_cadastro[email].nome)
    logging.info("Email: %s", usuario_cadastro[email].email)
    # Apenas uma instrução textual no log; não interrompe nem finaliza a execução
    return {"mensagem": "Perfil finalizado com sucesso!"}

# Fim do arquivo: não há bloco "__main__"; a aplicação deve ser iniciada
# externamente, por exemplo com "uvicorn api:app --reload"
