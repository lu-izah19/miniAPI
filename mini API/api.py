# Importa a classe FastAPI (cria a aplicação) e Depends (injeta
# dependências, ex: autenticação, nas rotas)
from fastapi import Depends, FastAPI  # noqa: I001

# Importa HTTPBearer, esquema de segurança que extrai o token do cabeçalho
# "Authorization: Bearer <token>"
from fastapi.security import HTTPBearer

# Importa o módulo de logging, usado para registrar mensagens (info, erro, etc.)
import logging

# Importa o módulo os, usado para acessar variáveis de ambiente do sistema
import os

# Importa o bcrypt, usado para gerar hash e verificar senhas de forma segura
import bcrypt

# Importa o módulo jwt (PyJWT), usado para gerar e validar tokens de autenticação
import jwt

# Importa o fernet do cryptography, usado para criptografar dados de forma simétrica
from cryptography.fernet import Fernet

# Importa a função que carrega variáveis de ambiente de um arquivo .env
from dotenv import load_dotenv

# Importa HTTPException, usado para lançar exceções HTTP com códigos de status e mensagens
from fastapi import HTTPException

# Importa BaseModel do pydantic, usado para criar os modelos de dados (schemas) da API
from pydantic import BaseModel

# Cria a instância principal da aplicação FastAPI
app = FastAPI()

# Carrega as variáveis definidas no arquivo .env para o ambiente do processo
load_dotenv()
# Lê a variável de ambiente SECRET_KEY, usada para assinar os tokens JWT
SECRET_KEY = os.environ.get("SECRET_KEY")
# Lê a variável de ambiente FERNET_KEY, usada para criptografar dados
FERNET_KEY = os.environ.get("FERNET_KEY")
# Cria o objeto Fernet responsável por criptografar/descriptografar os
# e-mails, usando a chave lida acima
fernet = Fernet(FERNET_KEY)

# Configura o logging para exibir mensagens a partir do nível INFO
logging.basicConfig(level=logging.INFO)


# Rota GET na raiz ("/") da API
@app.get("/")
def home():
    # Registra no log que a rota raiz da API foi acessada
    logging.info("Acessando a rota raiz da API...")
    # Retorna uma mensagem simples de boas-vindas em formato JSON
    return {"message": "Bem-vindo à API!"}


# Classe que representa um usuário internamente (não é um modelo do pydantic)
class Usuario:
    # Construtor: define nome, email e senha, todos opcionais por padrão
    def __init__(self, nome=None, email=None, senha=None, papel="user"):
        self.nome = nome  # Adiciona o atributo nome ao usuário
        self.email = email  # Adiciona o atributo email ao usuário
        self.senha = senha  # Adiciona o atributo senha ao usuário
        self.papel = papel  # Adiciona o atributo papel ao usuário


# Recebe o email em texto puro, codifica em bytes e criptografa com Fernet, devolvendo uma string
def criptografar_email(email):
    logging.info(f"Criptografando email: {email}")
    return fernet.encrypt(email.encode('utf-8')).decode('utf-8')


# Recebe o email criptografado (string), decodifica em bytes e
# descriptografa, devolvendo o texto original
def descriptografar_email(email):
    logging.info(f"Descriptografando email: {email}")
    return fernet.decrypt(email.encode('utf-8')).decode('utf-8')


# Dicionário usado como "banco de dados" em memória, indexado pelo email do usuário
usuario_cadastro = {}


# Modelo de dados esperado no corpo da requisição de cadastro
class UsuarioCadastro(BaseModel):
    nome: str   # Nome informado no cadastro
    email: str   # Email informado no cadastro (texto puro, será criptografado ao salvar)
    senha: str   # Senha em texto puro, será transformada em hash ao salvar


# Modelo de dados esperado no corpo da requisição de login
class UsuarioLogin(BaseModel):
    email: str   # Email usado para localizar o usuário cadastrado
    senha: str   # Senha em texto puro, comparada com o hash salvo


# Modelo de dados usado para representar o perfil do usuário (nome e email)
class UsuarioPerfil(BaseModel):
    nome: str   # Nome do usuário
    email: str   # Email do usuário


# Modelo de dados usado para alterar o papel do usuário (email e novo papel)
class AlterarPapel(BaseModel):
    email: str   # Email do usuário que terá o papel alterado
    papel: str   # Novo papel a ser atribuído (ex: "user" ou "admin")


# Modelo de dados esperado no corpo da requisição de deleção de usuário
class UsuarioDelete(BaseModel):
    email: str   # Email do usuário a ser deletado


# Modelo de dados esperado no corpo da requisição de alteração de senha
class UsuarioSenha(BaseModel):
    email: str   # Email do usuário que terá a senha alterada
    senha: str   # Nova senha em texto puro (será transformada em hash)


# Rota POST "/usuario", usada para cadastrar um novo usuário
@app.post("/usuario")
# Função que cadastra um novo usuário, recebendo nome, email e senha em texto puro
def cadastro(dados: UsuarioCadastro):
    # Extrai o email enviado no corpo da requisição
    email = dados.email
    # Gera o hash da senha (com salt) usando bcrypt, para não guardar a senha em texto puro
    senha_hash = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
    # Cria um novo objeto Usuario com o nome, email, senha hash e papel "user"
    novo_usuario = Usuario(
        nome=dados.nome,
        email=criptografar_email(email),
        senha=senha_hash,
        papel="user")
    # Salva o novo usuário no dicionário, usando o email como chave
    usuario_cadastro[email] = novo_usuario
    # Registra no log que o usuário foi cadastrado com sucesso
    logging.info(f"Usuário cadastrado com sucesso: {email}")
    # Retorna uma mensagem confirmando o cadastro
    return {"mensagem": "Cadastro realizado com sucesso!"}


# Rota POST "/login", usada para autenticar um usuário já cadastrado
@app.post("/login")
# Função que autentica um usuário e retorna um token JWT se a autenticação for bem-sucedida
def login(dados: UsuarioLogin):
    # Extrai o email enviado no corpo da requisição
    email_login = dados.email
    # Extrai a senha enviada no corpo da requisição
    senha_login = dados.senha
    # Verifica se o email existe e bate com o cadastrado, e se a senha confere com o hash salvo
    if email_login in usuario_cadastro:
        # Verifica se o email e a senha conferem com os dados cadastrados
        if bcrypt.checkpw(senha_login.encode('utf-8'), usuario_cadastro[email_login].senha):
            # Gera um token JWT contendo o email e o papel, assinado com a SECRET_KEY
            # usando o algoritmo HS256
            jtoken = jwt.encode({"email": email_login,
                                "papel": usuario_cadastro[email_login].papel},
                                SECRET_KEY, algorithm="HS256")
            # Registra no log que o login foi realizado com sucesso
            logging.info(f"Login realizado com sucesso para o email {email_login}.")
            # Retorna mensagem de sucesso junto com o token gerado
            return {"mensagem": "Login realizado com sucesso!", "token": jtoken}
        else:
            # Caso a senha não confira, registra o erro no log
            logging.error(f"Senha incorreta para o email {email_login}.")
            # Caso a senha não confira, retorna mensagem de senha incorreta
            raise HTTPException(status_code=401, detail="Senha incorreta!")
    else:
        # Caso o email não exista no cadastro, registra o erro no log
        logging.error(f"Email {email_login} não encontrado no cadastro.")
        # Caso email/senha não confiram, retorna mensagem de erro de login
        raise HTTPException(status_code=404, detail="Email incorreto!")


# Rota GET "/admin", protegida por autenticação via token JWT
@app.get("/admin")
# Função que retorna a lista de usuários cadastrados, exigindo autenticação de administrador
# credenciais: token Bearer extraído automaticamente do cabeçalho pela dependência HTTPBearer
def admin(credenciais=Depends(HTTPBearer())):
    logging.info("Acessando a rota de administração...")
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, registra o erro no log
        logging.error("Token expirado!")
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, registra o erro no log
        logging.error("Token inválido!")
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        lista_usuarios = []
        # Se o usuário for administrador, retorna o nome e email do usuário
        for chave_secreta in usuario_cadastro:  # noqa: PLC0206
            lista_usuarios.append({
                "nome": usuario_cadastro[chave_secreta].nome,
                "email": descriptografar_email(usuario_cadastro[chave_secreta].email)})
        # Registra no log que o usuário administrador acessou a lista de usuários cadastrados
        logging.info(f"Usuário {payload['email']} acessou a lista de usuários cadastrados.")
        # Retorna a lista de usuários cadastrados (nome e email) em formato JSON
        return {"usuarios": lista_usuarios}
    else:
        # Caso o usuário não seja administrador, registra o erro no log
        logging.error(f"Usuário {payload['email']} não é administrador")
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")


# Rota PATCH "/admin/papel", usada para alterar o papel de um usuário específico
@app.patch("/admin/papel")
# Função que altera o papel de um usuário específico, exigindo autenticação de administrador
# credenciais: token Bearer extraído do cabeçalho, exigido por essa rota protegida
def alterar_papel(dados: AlterarPapel, credenciais=Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, registra o erro no log
        logging.error("Token expirado!")
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, registra o erro no log
        logging.error("Token inválido!")
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        if dados.email in usuario_cadastro:
            # Altera o papel do usuário especificado no corpo da requisição
            usuario = usuario_cadastro[dados.email]
            usuario.papel = dados.papel
            # Registra no log que o papel do usuário foi alterado com sucesso
            logging.info(f"Papel do usuário {dados.email} alterado por {payload['email']} para {dados.papel}.")
            # Registra que o papel do usuário foi alterado
            return {"mensagem": "Papel de usuário alterado!", "papel": usuario.papel}
        else:
            # Caso o email não exista no cadastro, registra o erro no log
            logging.error(f"Usuário {dados.email} não encontrado para alteração de papel.")
            # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        # Caso o usuário não seja administrador, registra o erro no log
        logging.error(f"Usuário {payload['email']} não é administrador")
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")


# Rota DELETE "/admin/usuario", usada para deletar um usuário específico
@app.delete("/admin/usuario")
# Função que deleta um usuário específico, exigindo autenticação de administrador
# credenciais: token Bearer extraído do cabeçalho, exigido por essa rota protegida
def deletar_perfil_usuario(dados: UsuarioDelete, credenciais=Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, registra o erro no log
        logging.error("Token expirado!")    
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, registra o erro no log
        logging.error("Token inválido!")
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        if dados.email in usuario_cadastro:
            # Deleta o usuário especificado no corpo da requisição
            del usuario_cadastro[dados.email]
            # Registra no log que o usuário foi deletado com sucesso
            logging.info(f"Usuário {dados.email} deletado com sucesso por {payload['email']}.")
            # Registra que o usuário foi deletado
            return {"mensagem": "Usuário deletado com sucesso!"}
        else:
            # Caso o email não exista no cadastro, registra o erro no log
            logging.error(f"Usuário {dados.email} não encontrado.")
            # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        # Caso o usuário não seja administrador, registra o erro no log
        logging.error(f"Usuário {payload['email']} não é administrador")
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")


# Rota PATCH "/perfil/usuario", usada para alterar o perfil do usuário autenticado
@app.patch("/perfil/usuario")
# Função que altera o perfil do usuário autenticado, usando o token JWT para identificar o usuário
# credenciais: token Bearer extraído do cabeçalho, identifica quem está editando o próprio perfil
def alterar_perfil(dados: UsuarioCadastro, credenciais=Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, registra o erro no log
        logging.error("Token expirado!")
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, registra o erro no log
        logging.error("Token inválido!")
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o email enviado no corpo da requisição já está em uso por outro usuário
    if dados.email in usuario_cadastro and dados.email != payload["email"]:
        # Caso o email já esteja em uso, registra a informação no log
        logging.info(f"Email {dados.email} já está em uso por outro usuário.")
        # Caso o email já esteja em uso, retorna erro de conflito
        raise HTTPException(status_code=409, detail="Email já está em uso!")
    # Atualiza os dados do usuário no dicionário de cadastro
    usuario = usuario_cadastro[payload["email"]]
    usuario.nome = dados.nome
    usuario.senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
    # Se o email foi alterado, atualiza a chave no dicionário de cadastro
    if dados.email != payload["email"]:
        usuario.email = criptografar_email(dados.email)
        usuario_cadastro[dados.email] = usuario
        del usuario_cadastro[payload["email"]]
    # Registra no log que os dados do usuário foram alterados com sucesso
    logging.info(f"Dados do usuário {payload['email']} alterados com sucesso.")
    # Retorna mensagem de sucesso após a alteração do perfil
    return {"mensagem": "Perfil alterado com sucesso!"}


# Rota PATCH "/admin/usuario", usada para alterar a senha de um usuário específico
@app.patch("/admin/usuario")
# Função que altera a senha de um usuário específico, exigindo autenticação de administrador
# credenciais: token Bearer extraído do cabeçalho, exigido por essa rota protegida
def alterar_senha(dados: UsuarioSenha, credenciais=Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, registra o erro no log
        logging.error("Token expirado!")
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, registra o erro no log
        logging.error("Token inválido!")
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário é administrador com base no papel armazenado no cadastro
    if usuario_cadastro[payload["email"]].papel == "admin":
        if dados.email in usuario_cadastro:
            # Altera a senha do usuário especificado no corpo da requisição
            usuario = usuario_cadastro[dados.email]
            usuario.senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
            # Registra no log que a senha do usuário foi alterada com sucesso
            logging.info(f"Senha do usuário {dados.email} alterada com sucesso por {payload['email']}.")
            # Registra que a senha do usuário foi alterada
            return {"mensagem": "Senha de usuário alterada!"}
        else:
            # Caso o email não exista no cadastro, registra o erro no log
            logging.error(f"Usuário {dados.email} não encontrado para alteração de senha.")
            # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        # Caso o usuário não seja administrador, registra o erro no log
        logging.error(f"Usuário {payload['email']} não é administrador")
        # Caso o usuário não seja administrador, retorna erro de acesso negado
        raise HTTPException(status_code=403, detail="Acesso negado! Usuário não é administrador.")


# Rota DELETE "/perfil/usuario", usada para deletar o perfil do usuário autenticado
@app.delete("/perfil/usuario")
# Função que deleta o perfil do usuário autenticado, usando o token JWT para identificar o usuário
# credenciais: token Bearer extraído do cabeçalho, identifica quem está deletando a própria conta
def deletar_perfil_proprio(credenciais=Depends(HTTPBearer())):
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, registra o erro no log
        logging.error("Token expirado!")
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, registra o erro no log
        logging.error("Token inválido!")
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
    if payload["email"] in usuario_cadastro:
        # Deleta o usuário especificado no corpo da requisição
        del usuario_cadastro[payload["email"]]
        # Registra no log que o usuário foi deletado com sucesso
        logging.info(f"Usuário {payload['email']} deletado com sucesso.")
        # Registra que o usuário foi deletado
        return {"mensagem": "Usuário deletado com sucesso!"}
    else:
        # Caso o email não exista no cadastro, registra o erro no log
        logging.error(f"Usuário {payload['email']} não encontrado para deleção.")
        # Caso o email não exista no cadastro, retorna erro de usuário não encontrado
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")


# Rota GET "/perfil", protegida por autenticação via token JWT
@app.get("/perfil")
# Função que retorna o perfil do usuário autenticado, usando o token JWT para identificar o usuário
# credenciais: token Bearer extraído do cabeçalho, identifica quem está consultando o perfil
def perfil(credenciais=Depends(HTTPBearer())):
    # Registra no log que o perfil está sendo acessado
    logging.info("Acessando o perfil do usuário...")
    try:
        # Extrai o token JWT do cabeçalho Authorization (Bearer)
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
        # Registra no log que o perfil do usuário foi acessado com sucesso
        logging.info(f"Perfil do usuário {payload['email']} acessado com sucesso!")
        # Retorna o nome e email do usuário, obtidos a partir do payload do token
        return {"nome": usuario_cadastro[payload["email"]].nome, "email": payload["email"]}
    except jwt.ExpiredSignatureError:
        # Caso o token tenha expirado, registra o erro no log
        logging.error("Token expirado!")
        # Caso o token tenha expirado, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        # Caso o token seja inválido, registra o erro no log
        logging.error("Token inválido!")
        # Caso o token seja inválido, retorna erro de autenticação
        raise HTTPException(status_code=401, detail="Token inválido!")
