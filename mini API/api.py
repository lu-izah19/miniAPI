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

# Modelo de dados usado para representar o perfil do usuário (nome e email)
class UsuarioPerfil(BaseModel):
    nome: str
    email: str

# Modelo de dados usado para alterar o papel do usuário (email e novo papel)
class AlterarPapel(BaseModel):
    email: str
    papel: str

# Modelo de dados esperado no corpo da requisição de deleção de usuário
class UsuarioDelete(BaseModel):
    email: str

# Modelo de dados esperado no corpo da requisição de alteração de senha
class UsuarioSenha(BaseModel):
    email: str
    senha: str

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
    # Cria um novo objeto Usuario com o nome, email, senha hash e papel "user"
    novo_usuario = Usuario(nome=dados.nome, email=email, senha=senha_hash, papel="user")
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
    # Verifica se o email existe e bate com o cadastrado, e se a senha confere com o hash salvo
    if email_login in usuario_cadastro:
        # Verifica se o email e a senha conferem com os dados cadastrados
        if bcrypt.checkpw(senha_login.encode('utf-8'), usuario_cadastro[email_login].senha):
            # Gera um token JWT contendo o email e o papel, assinado com a SECRET_KEY usando o algoritmo HS256
            jtoken = jwt.encode({"email": email_login, "papel": usuario_cadastro[email_login].papel}, SECRET_KEY, algorithm="HS256")
            # Retorna mensagem de sucesso junto com o token gerado
            return {"mensagem": "Login realizado com sucesso!", "token": jtoken}
        else:
            # Caso a senha não confira, retorna mensagem de senha incorreta
            raise HTTPException(status_code=401, detail="Senha incorreta!")
    else:
        # Caso email/senha não confiram, retorna mensagem de erro de login
        raise HTTPException(status_code=404, detail="Email incorreto!")

# Rota GET "/admin", protegida por autenticação via token JWT
@app.get("/admin")
def admin(credenciais = Depends(HTTPBearer())):
    logging.info("Acessando a rota de administração...")
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"]) 
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        lista_usuarios = []
        # Se o usuário for administrador, retorna o nome e email do usuário
        for chave_secreta in usuario_cadastro:
            lista_usuarios.append({"nome": usuario_cadastro[chave_secreta].nome, "email": usuario_cadastro[chave_secreta].email})
            return {"usuarios": lista_usuarios}
    else: 
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")

# Rota PATCH "/admin/papel", usada para alterar o papel de um usuário específico
@app.patch("/admin/papel")
def alterar_papel(dados: AlterarPapel, credenciais = Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"]) 
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        if dados.email in usuario_cadastro:
            # Altera o papel do usuário especificado no corpo da requisição
            usuario = usuario_cadastro[dados.email]
            usuario.papel = dados.papel
            # Registra que o papel do usuário foi alterado 
            return {"mensagem": "Papel de usuário alterado!", "papel": usuario.papel}
        else: 
            # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")

# Rota DELETE "/admin/usuario", usada para deletar um usuário específico
@app.delete("/admin/usuario")
def deletar_usuario(dados: UsuarioDelete, credenciais = Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"]) 
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
     # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        if dados.email in usuario_cadastro:
            # Deleta o usuário especificado no corpo da requisição
            del usuario_cadastro[dados.email]
            # Registra que o usuário foi deletado
            return {"mensagem": "Usuário deletado com sucesso!"}
        else: 
            # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")

# Rota PATCH "/perfil/usuario", usada para alterar o perfil do usuário autenticado
@app.patch("/perfil/usuario")
def alterar_perfil(dados: UsuarioCadastro, credenciais = Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o email enviado no corpo da requisição já está em uso por outro usuário
    if dados.email in usuario_cadastro and dados.email != payload["email"]:
        # Caso o email já esteja em uso, retorna erro de conflito
        raise HTTPException(status_code=409, detail="Email já está em uso!")
    # Atualiza os dados do usuário no dicionário de cadastro
    usuario = usuario_cadastro[payload["email"]]
    usuario.nome = dados.nome
    usuario.senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
    # Se o email foi alterado, atualiza a chave no dicionário de cadastro
    if dados.email != payload["email"]:
        usuario.email = dados.email
        usuario_cadastro[dados.email] = usuario
        del usuario_cadastro[payload["email"]]
    # Retorna mensagem de sucesso após a alteração do perfil   
    return {"mensagem": "Perfil alterado com sucesso!"}

# Rota PATCH "/admin/usuario", usada para alterar a senha de um usuário específico
@app.patch("/admin/usuario")
def alterar_senha(dados: UsuarioSenha, credenciais = Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"]) 
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        if dados.email in usuario_cadastro:
            # Altera a senha do usuário especificado no corpo da requisição
            usuario = usuario_cadastro[dados.email]
            usuario.senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
            # Registra que a senha do usuário foi alterada
            return {"mensagem": "Senha de usuário alterada!"}
        else: 
            # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")

# Rota DELETE "/perfil/usuario", usada para deletar o perfil do usuário autenticado
@app.delete("/perfil/usuario")
def deletar_usuario(credenciais = Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"]) 
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    if payload["email"] in usuario_cadastro:
        # Deleta o usuário especificado no corpo da requisição
        del usuario_cadastro[payload["email"]]
        # Registra que o usuário foi deletado
        return {"mensagem": "Usuário deletado com sucesso!"}
    else: 
        # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")

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
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
