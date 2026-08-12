# Importa a classe FastAPI, usada para criar a aplicação/API
from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer
app = FastAPI()
# Importa o módulo de logging, usado para registrar mensagens (info, erro, etc.)
import logging
# Importa HTTPException, usado para lançar exceções HTTP com códigos de status e mensagens
from fastapi import HTTPException
# Importa o módulo jwt (PyJWT), usado para gerar e validar tokens de autenticação
import jwt
# Importa o bcrypt, usado para gerar hash e verificar senhas de forma segura
import bcrypt
# Importa a função que carrega variáveis de ambiente de um arquivo .env
from dotenv import load_dotenv
# Importa o módulo os, usado para acessar variáveis de ambiente do sistema
import os
# Importa BaseModel do pydantic, usado para criar os modelos de dados (schemas) da API
from pydantic import BaseModel

# Carrega as variáveis definidas no arquivo .env para o ambiente do processo
load_dotenv()
# Lê a variável de ambiente SECRET_KEY, usada para assinar os tokens JWT
SECRET_KEY =os.environ.get("SECRET_KEY")

# Configura o logging para exibir mensagens a partir do nível INFO
logging.basicConfig(level=logging.INFO)

# Rota GET na raiz ("/") da API
@app.get("/")
def home():
    # Retorna uma mensagem simples de boas-vindas em formato JSON
    return {"message": "Bem-vindo à API!"}

# Classe que representa um usuário internamente (não é um modelo do pydantic)
class Usuario:
    # Construtor: define nome, email e senha, todos opcionais por padrão
    def __init__(self, nome=None, email=None, senha=None, papel="user"):
        self.nome = nome # Adiciona o atributo nome ao usuário
        self.email = email # Adiciona o atributo email ao usuário
        self.senha = senha # Adiciona o atributo senha ao usuário
        self.papel = papel # Adiciona o atributo papel ao usuário

# Dicionário usado como "banco de dados" em memória, indexado pelo email do usuário
usuario_cadastro = {}

# Modelo de dados esperado no corpo da requisição de cadastro
class UsuarioCadastro(BaseModel):
    nome: str
    email: str
    senha: str

# Modelo de dados esperado para a rota de início (apenas o nome)
class UsuarioInicio(BaseModel):
    nome: str

# Modelo de dados esperado no corpo da requisição de login
class UsuarioLogin(BaseModel):
    email: str
    senha: str
    papel: str = "user"  # Define o papel do usuário como "user" por padrão

# Modelo de dados usado para representar o perfil do usuário (nome e email)
class UsuarioPerfil(BaseModel):
    nome: str
    email: str

# Rota GET "/usuario", recebe dados de UsuarioInicio (apenas nome)
@app.get("/usuario")
def inicio(dados: UsuarioInicio):
    # Cria um objeto Usuario apenas com o nome recebido
    usuario = Usuario(nome=dados.nome)
    # Registra no log uma mensagem de boas-vindas com o nome do usuário
    logging.info("Olá %s, seja bem vindo(a)!", usuario.nome)

# Rota POST "/usuario", usada para cadastrar um novo usuário
@app.post("/usuario")
def cadastro(dados: UsuarioCadastro):
    # Extrai o email enviado no corpo da requisição
    email = dados.email
    # Gera o hash da senha (com salt) usando bcrypt, para não guardar a senha em texto puro
    senha_hash = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
    # Declara que a variável usuario_cadastro usada aqui é a global definida acima
    global usuario_cadastro
    # Cria um novo objeto Usuario com email e senha (hash); nome fica None
    novo_usuario = Usuario(nome=None, email=email, senha=senha_hash, papel="user")
    # Salva o novo usuário no dicionário, usando o email como chave
    usuario_cadastro[email] = novo_usuario
    # Retorna uma mensagem confirmando o cadastro
    return {"mensagem": "Cadastro realizado com sucesso!"}

# Rota POST "/login", usada para autenticar um usuário já cadastrado
@app.post("/login")
def login(dados: UsuarioLogin):
    # Extrai o email enviado no corpo da requisição
    email_login = dados.email
    # Extrai a senha enviada no corpo da requisição
    senha_login = dados.senha
    # Extrai o papel enviado no corpo da requisição
    papel_login = dados.papel

    
    # Verifica se o email existe e bate com o cadastrado, e se a senha confere com o hash salvo
    if email_login in usuario_cadastro:
        # Verifica se o email e a senha conferem com os dados cadastrados
        if bcrypt.checkpw(senha_login.encode('utf-8'), usuario_cadastro[email_login].senha):
            # Verifica se o papel do usuário é válido (existe no cadastro)
            if papel_login == usuario_cadastro[email_login].papel:
                # Gera um token JWT contendo o email, assinado com a SECRET_KEY usando o algoritmo HS256
                jtoken = jwt.encode({"email": email_login}, SECRET_KEY, algorithm="HS256")
                # Retorna mensagem de sucesso junto com o token gerado
                return {"mensagem": "Login realizado com sucesso!", "token": jtoken}
            else:
                    # Caso o papel do usuário não seja válido, retorna mensagem de erro
                    raise HTTPException(status_code=403, detail="Papel de usuário inválido!")
        else:
            # Caso a senha não confira, retorna mensagem de senha incorreta
            raise HTTPException(status_code=401, detail="Senha incorreta!")
    else:
        # Caso email/senha não confiram, retorna mensagem de erro de login
        raise HTTPException(status_code=404, detail="Email incorreto!")

@app.get("/admin")
def admin(credenciais = Depends(HTTPBearer())):
    logging.info("Acessando a rota de administração...")
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"]) 
        # Verifica se o usuário é administrador com base no papel armazenado no cadastro
        if usuario_cadastro[payload["email"]].papel == "admin":
            # Retorna o nome e email do usuário, obtidos a partir do payload do token
            return {"nome" : usuario_cadastro[payload["email"]].nome, "email": payload["email"]}
        else: 
            # Caso o usuário não seja administrador, retorna erro de acesso negado
            raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")
        
    except:
        # Caso o token seja inválido ou tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido ou expirado!")
    

# Rota GET "/perfil", protegida por autenticação via token JWT
@app.get("/perfil")
def perfil(credenciais = Depends(HTTPBearer())):
    # Registra no log que o perfil está sendo acessado
    logging.info("Acessando o perfil do usuário...")
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"]) 
        # Retorna o nome e email do usuário, obtidos a partir do payload do token
        return {"nome" : usuario_cadastro[payload["email"]].nome, "email": payload["email"]}
    except:
        # Caso o token seja inválido ou tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido ou expirado!")
   

