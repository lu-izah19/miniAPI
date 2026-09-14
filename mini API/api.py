# Importa a classe FastAPI e a dependência Depends para criar rotas e injetar autenticação.
from fastapi import Depends, FastAPI

# Importa Optional para permitir campos opcionais em modelos Pydantic.
from typing import Optional

# Importa HTTPBearer para autenticação via token no cabeçalho Authorization.
from fastapi.security import HTTPBearer

# Importa o módulo de logging para registrar eventos e erros da API.
import logging

# Importa o módulo os para acessar variáveis de ambiente.
import os

# Importa bcrypt para gerar hash e validar senhas de forma segura.
import bcrypt

# Importa PyJWT para gerar e validar tokens JWT.
import jwt

# Importa Fernet para criptografar e descriptografar dados sensíveis.
from cryptography.fernet import Fernet

# Importa load_dotenv para carregar variáveis do arquivo .env.
from dotenv import load_dotenv

# Importa HTTPException para retornar erros HTTP personalizados.
from fastapi import HTTPException

# Importa BaseModel para criar modelos de dados da API.
from pydantic import BaseModel

# Importa datetime para controlar tempo de expiração dos tokens.
import datetime

# Importa mysql.connector para conectar com o banco de dados MySQL.
import mysql.connector

# Cria a instância principal da aplicação FastAPI.
app = FastAPI()

# Carrega as variáveis do arquivo .env para o ambiente da aplicação.
load_dotenv()

# Lê o nome do usuário root configurado no ambiente.
USUARIO_ROOT = os.environ.get("USUARIO_ROOT")
# Lê a senha do usuário root configurada no ambiente.
SENHA_ROOT = os.environ.get("SENHA_ROOT")
# Lê o e-mail do usuário root configurado no ambiente.
EMAIL_ROOT = os.environ.get("EMAIL_ROOT")
# Lê a chave secreta usada para assinar tokens JWT.
SECRET_KEY = os.environ.get("SECRET_KEY")
# Lê a chave usada para criptografar e descriptografar e-mails.
FERNET_KEY = os.environ.get("FERNET_KEY")
# Cria o objeto Fernet responsável pela criptografia simétrica.
fernet = Fernet(FERNET_KEY)

# Configura o nível mínimo de logs para exibir mensagens informativas.
logging.basicConfig(level=logging.INFO)


# Define uma rota GET na raiz da aplicação.
@app.get("/")
# Função responsável por responder ao acesso na rota inicial da API.
def home():
    # Registra que a rota raiz foi acessada.
    logging.info("Acessando a rota raiz da API...")
    # Retorna uma mensagem de boas-vindas em formato JSON.
    return {"message": "Bem-vindo à API!"}


# Lê o usuário configurado para acesso ao banco de dados MariaDB.
MARIADB_USER = os.environ.get("MARIADB_USER")
# Lê a senha do banco de dados.
MARIADB_PASSWORD = os.environ.get("MARIADB_PASSWORD")
# Lê o nome do banco de dados a ser utilizado.
MARIADB_DATABASE = os.environ.get("MARIADB_DATABASE")


# Cria a conexão com o banco de dados usando as variáveis de ambiente.
conexao = mysql.connector.connect(
    # Endereço do host do banco de dados.
    host="137.131.133.237",
    # Usuário para autenticação no banco.
    user=MARIADB_USER,
    # Senha do usuário do banco.
    password=MARIADB_PASSWORD,
    # Nome do banco de dados usado pela API.
    database=MARIADB_DATABASE
)


# Classe interna para representar um usuário em memória.
class Usuario:
    # Inicializa os dados do usuário com valores opcionais.
    def __init__(self, nome=None, email=None, senha=None, papel="user"):
        # Armazena o nome do usuário.
        self.nome = nome
        # Armazena o e-mail do usuário.
        self.email = email
        # Armazena a senha do usuário.
        self.senha = senha
        # Armazena o papel do usuário dentro da aplicação.
        self.papel = papel


# Função para criptografar o e-mail antes de salvar no banco.
def criptografar_email(email):
    # Registra o início da criptografia do e-mail.
    logging.info(f"Criptografando email: {email}")
    # Criptografa o e-mail em bytes e converte para string.
    return fernet.encrypt(email.encode('utf-8')).decode('utf-8')


# Função para descriptografar o e-mail criptografado.
def descriptografar_email(email):
    # Registra o início da descriptografia do e-mail.
    logging.info(f"Descriptografando email: {email}")
    # Descriptografa a string e retorna o e-mail em texto puro.
    return fernet.decrypt(email.encode('utf-8')).decode('utf-8')


# Dicionário usado como estrutura de cadastro em memória.
usuario_cadastro = {}


# Modelo para receber dados do cadastro do usuário.
class UsuarioCadastro(BaseModel):
    # Nome do usuário.
    nome: str
    # E-mail informado pelo usuário.
    email: str
    # Senha informada pelo usuário.
    senha: str


# Modelo para receber os dados do login do usuário.
class UsuarioLogin(BaseModel):
    # E-mail usado para autenticação.
    email: str
    # Senha usada para autenticação.
    senha: str


# Modelo para representar as informações do perfil do usuário.
class UsuarioPerfil(BaseModel):
    # Nome do usuário.
    nome: str
    # E-mail do usuário.
    email: str


# Modelo para alterar o papel do usuário.
class AlterarPapel(BaseModel):
    # E-mail do usuário alvo.
    email: str
    # Novo papel que será aplicado.
    papel: str


# Modelo para receber o e-mail de um usuário que será removido.
class UsuarioDelete(BaseModel):
    # E-mail do usuário a ser deletado.
    email: str


# Modelo para receber a nova senha de um usuário.
class UsuarioSenha(BaseModel):
    # E-mail do usuário que terá a senha alterada.
    email: str
    # Nova senha em texto puro.
    senha: str


# Modelo para atualizar campos do perfil do usuário de forma opcional.
class UsuarioAlterarPerfil(BaseModel):
    # Novo nome, se houver.
    nome: Optional[str] = None
    # Novo e-mail, se houver.
    email: Optional[str] = None
    # Nova senha, se houver.
    senha: Optional[str] = None


# Define a rota para cadastro do usuário.
@app.post("/usuario")
# Função que cadastra um novo usuário no banco de dados.
def cadastro(dados: UsuarioCadastro):
    # Inicia um bloco de tratamento de exceções.
    try:
        # Cria um cursor para executar queries SQL.
        cursor = conexao.cursor(dictionary=True)
        # Criptografa o e-mail recebido.
        email = criptografar_email(dados.email)
        # Gera um hash seguro para a senha do usuário.
        senha_hash = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Insere os dados do usuário na tabela usuarios.
        cursor.execute("INSERT INTO usuarios (email, nome, senha, papel) VALUES(%s, %s, %s, 'user')", 
            (email, dados.nome, senha_hash))
        # Confirma a operação no banco de dados.
        conexao.commit()
        # Registra o sucesso do cadastro.
        logging.info(f"Usuário cadastrado com sucesso: {email}")
        # Retorna confirmação de cadastro para o cliente.
        return {"mensagem": "Cadastro realizado com sucesso!"}
    # Captura erro de e-mail duplicado.
    except mysql.connector.errors.IntegrityError:
        # Registra que o e-mail já está em uso.
        logging.info(f"Esse email ja está sendo utilizado por outro usuário!")
        # Retorna erro de conflito HTTP 409.
        raise HTTPException(status_code=409, detail="Email já está em uso!")


# Define a rota de login da API.
@app.post("/login")
# Função responsável por autenticar o usuário e emitir um token JWT.
def login(dados: UsuarioLogin):
    # Cria um cursor para consultar o banco.
    cursor = conexao.cursor(dictionary=True)
    # Busca todos os usuários cadastrados.
    cursor.execute("SELECT * FROM usuarios")
    # Armazena os registros retornados.
    todos_usuarios = cursor.fetchall()
    # Inicializa a variável do usuário autenticado.
    usuario = None
    # Percorre todos os usuários para encontrar o e-mail informado.
    for linha in todos_usuarios:
        # Compara o e-mail descriptografado com o e-mail digitado.
        if descriptografar_email(linha["email"]) == dados.email:
            # Salva o usuário encontrado.
            usuario = linha
            # Interrompe a busca ao encontrar o usuário.
            break
    # Verifica se o login é do usuário root.
    if EMAIL_ROOT == dados.email and SENHA_ROOT == dados.senha:
        # Gera um JWT para o usuário root com expiração de 30 minutos.
        jtoken = jwt.encode({"email": dados.email, "papel": "root",
                            "exp": datetime.datetime.now(datetime.timezone.utc)
                            + datetime.timedelta(minutes=30)},
                            SECRET_KEY, algorithm="HS256")
        # Registra o login do usuário root.
        logging.info("Usuário root autenticado com sucesso.")
        # Retorna o token JWT do root.
        return {"token": jtoken}
    # Caso não seja root, autentica o usuário comum.
    else:
        # Se o usuário existe, valida a senha.
        if usuario is not None:
            # Verifica se a senha informada corresponde ao hash salvo.
            if bcrypt.checkpw(dados.senha.encode('utf-8'), usuario['senha'].encode('utf-8')):
                # Gera um token para o usuário autenticado.
                jtoken = jwt.encode({"email": dados.email,
                                    "papel": usuario['papel'],
                                    "exp": datetime.datetime.now(datetime.timezone.utc)
                                    + datetime.timedelta(minutes=30)},
                                    SECRET_KEY, algorithm="HS256")
                # Registra o login com sucesso.
                logging.info(f"Login realizado com sucesso para o email {dados.email}.")
                # Retorna mensagem e token do usuário.
                return {"mensagem": "Login realizado com sucesso!", "token": jtoken}
            # Se a senha estiver incorreta, retorna erro 401.
            else:
                # Registra a falha de senha.
                logging.error(f"Senha incorreta para o email {dados.email}.")
                # Lança exceção de senha incorreta.
                raise HTTPException(status_code=401, detail="Senha incorreta!")
        # Se o e-mail não existir, retorna erro 404.
        else:
            # Registra o e-mail não encontrado.
            logging.error(f"Email {dados.email} não encontrado no cadastro.")
            # Lança exceção de e-mail inválido.
            raise HTTPException(status_code=404, detail="Email incorreto!")


# Define a rota de listagem de usuários administrativos.
@app.get("/admin")
# Função que valida o token e retorna a lista de usuários.
def admin(credenciais=Depends(HTTPBearer())):
    # Registra o acesso à rota de administração.
    logging.info("Acessando a rota de administração...")
    # Cria um cursor para consultar os usuários.
    cursor = conexao.cursor(dictionary=True)
    # Tenta decodificar o token JWT recebido.
    try:
        # Extrai o payload do token.
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    # Captura token expirado.
    except jwt.ExpiredSignatureError:
        # Registra erro de token expirado.
        logging.error("Token expirado!")
        # Lança erro HTTP 401.
        raise HTTPException(status_code=401, detail="Token expirado!")
    # Captura token inválido.
    except jwt.InvalidTokenError:
        # Registra token inválido.
        logging.error("Token inválido!")
        # Lança erro HTTP 401.
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário autenticado é o root.
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        # Registra login do usuário root.
        logging.info("Usuário root autenticado com sucesso.")
        # Busca todos os usuários no banco.
        cursor.execute("SELECT * FROM usuarios")
        # Pega a lista de usuários.
        todos_usuarios = cursor.fetchall()
        # Cria lista para exportar os dados.
        lista_usuarios = []
        # Percorre os usuários e adiciona nome e e-mail descriptografado.
        for linha in todos_usuarios:
            lista_usuarios.append({
                "nome": linha["nome"],
                "email": descriptografar_email(linha["email"])
            })
            # Registra o acesso à listagem por parte do root.
            logging.info(f"Usuário {payload['email']} acessou a lista de usuários cadastrados.")
            # Retorna a lista de usuários.
            return{"usuarios": lista_usuarios} 
    # Se não for root, continua para validação de admin.
    else:   
        # Busca todos os usuários do banco.
        cursor.execute("SELECT * FROM usuarios")
        # Armazena os registros.
        todos_usuarios = cursor.fetchall()
        # Inicializa usuário atual como None.
        usuario = None
        # Busca o usuário autenticado na tabela.
        for linha in todos_usuarios:
            if descriptografar_email(linha["email"]) == payload["email"]:
                usuario = linha
                break
        # Se o usuário não for encontrado, retorna erro 404.
        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
        # Verifica se o usuário possui papel de administrador.
        if usuario["papel"]== "admin":
            # Busca todos os usuários novamente.
            cursor.execute("SELECT * FROM usuarios")
            # Salva os registros.
            todos_usuarios = cursor.fetchall()
            # Cria a lista de retorno.
            lista_usuarios = []
            # Percorre os usuários e adiciona os dados de cada um.
            for linha in todos_usuarios:
                lista_usuarios.append({
                    "nome": linha["nome"],
                    "email": descriptografar_email(linha["email"])
                })
                # Registra acesso da lista por admin.
                logging.info(f"Usuário {payload['email']} acessou a lista de usuários cadastrados.")
                # Retorna a lista para o admin.
                return{"usuarios": lista_usuarios}
        # Se não for admin, bloqueia o acesso.
        else:
            # Registra tentativa de acesso negada.
            logging.error(f"Usuário {payload['email']} não é administrador")
            # Lança erro 403 de acesso proibido.
            raise HTTPException(status_code=403,
                                detail="Acesso negado! Usuário não é administrador.")


# Define a rota para alterar o papel de um usuário.
@app.patch("/admin/papel")
# Função que valida o token e altera o papel do usuário informado.
def alterar_papel(dados: AlterarPapel, credenciais=Depends(HTTPBearer())):
    # Cria o cursor para executar consultas SQL.
    cursor = conexao.cursor(dictionary=True)
    # Tenta decodificar o token de autenticação.
    try:
        # Extrai o payload do token.
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    # Trata token expirado.
    except jwt.ExpiredSignatureError:
        # Registra o erro de token expirado.
        logging.error("Token expirado!")
        # Lança erro 401.
        raise HTTPException(status_code=401, detail="Token expirado!")
    # Trata token inválido.
    except jwt.InvalidTokenError:
        # Registra token inválido.
        logging.error("Token inválido!")
        # Lança erro 401.
        raise HTTPException(status_code=401, detail="Token inválido!")
    # Verifica se o usuário autenticado é o usuário root.
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        # Registra o login do root.
        logging.info("Usuário root autenticado com sucesso.")
        # Busca todos os usuários.
        cursor.execute("SELECT * FROM usuarios")
        # Salva os resultados em uma variável.
        todos_usuarios = cursor.fetchall()
        # Inicializa usuário alvo.
        usuario = None
        # Busca o usuário cujo e-mail coincida com o e-mail informado.
        for linha in todos_usuarios:
            if descriptografar_email(linha["email"]) == dados.email:
                usuario = linha
                break
        # Se o usuário existe, altera o papel.
        if usuario is not None:
            # Atualiza o papel do usuário alvo.
            cursor.execute("UPDATE usuarios SET papel = %s WHERE email = %s", (dados.papel, usuario["email"]))
            # Confirma a alteração no banco.
            conexao.commit()
            # Registra a mudança de papel.
            logging.info(
                f"Papel do usuário {dados.email} alterado por "
                f"{payload['email']} para {dados.papel}."
            )
            # Retorna mensagem de sucesso.
            return {"mensagem": "Papel de usuário alterado!", "papel": dados.papel}
        # Se o usuário não existir, retorna erro 404.
        else:
            # Registra usuário não encontrado.
            logging.error(f"Usuário {dados.email} não encontrado para alteração de papel.")
            # Lança erro HTTP 404.
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    # Se não for root, valida permissões de admin.
    else:
        # Busca todos os usuários.
        cursor.execute("SELECT * FROM usuarios")
        # Armazena os registros.
        todos_usuarios = cursor.fetchall()
        # Inicializa variável do usuário alvo.
        usuario = None
        # Procura o usuário alvo no banco.
        for linha in todos_usuarios:
            if descriptografar_email(linha["email"]) == dados.email:
                usuario = linha
                break
        # Verifica se o usuário autenticado é administrador.
        if payload["papel"] == "admin":
            # Se o usuário alvo existir, atualiza o papel.
            if usuario is not None:
                # Atualiza o papel do usuário.
                cursor.execute("UPDATE usuarios SET papel = %s WHERE email = %s", (dados.papel, usuario["email"]))
                # Confirma a alteração.
                conexao.commit()
                # Registra a modificação de papel.
                logging.info(
                    f"Papel do usuário {dados.email} alterado por "
                    f"{payload['email']} para {dados.papel}."
                )
                # Retorna confirmação da alteração.
                return {"mensagem": "Papel de usuário alterado!", "papel": dados.papel}
            # Se o usuário não existir, retorna erro 404.
            else:
                # Registra usuário não encontrado.
                logging.error(f"Usuário {dados.email} não encontrado para alteração de papel.")
                # Lança erro 404.
                raise HTTPException(status_code=404, detail="Usuário não encontrado!")
        # Se o usuário não for admin, bloqueia a ação.
        else:
            # Registra acesso negado.
            logging.error(f"Usuário {payload['email']} não é administrador")
            # Lança erro 403.
            raise HTTPException(
                status_code=403, detail="Acesso negado! Usuário não é administrador."
            )


@app.delete("/admin/usuario")
def deletar_perfil_usuario(dados: UsuarioDelete, credenciais=Depends(HTTPBearer())):
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (dados.email,))
    usuario = cursor.fetchone()
    conexao.commit()
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logging.error("Token expirado!")
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        logging.error("Token inválido!")
        raise HTTPException(status_code=401, detail="Token inválido!")
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        logging.info("Usuário root autenticado com sucesso.")
        if usuario is not None:
            del usuario[dados.email]
            logging.info(f"Usuário {dados.email} deletado com sucesso por {payload['email']}.")
            return {"mensagem": "Usuário deletado com sucesso!"}
        else:
            logging.error(f"Usuário {dados.email} não encontrado.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        if usuario[payload["email"]].papel == "admin":
            if dados.email in usuario:
                del usuario[dados.email]
                logging.info(f"Usuário {dados.email} deletado com sucesso por {payload['email']}.")
                return {"mensagem": "Usuário deletado com sucesso!"}
            else:
                logging.error(f"Usuário {dados.email} não encontrado.")
                raise HTTPException(status_code=404, detail="Usuário não encontrado!")
        else:
            logging.error(f"Usuário {payload['email']} não é administrador")
            raise HTTPException(
                status_code=403, detail="Acesso negado! Usuário não é administrador."
            )


@app.patch("/perfil/usuario")
def alterar_perfil(dados: UsuarioAlterarPerfil, credenciais=Depends(HTTPBearer())):
    cursor = conexao.cursor(dictionary=True)
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logging.error("Token expirado!")
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        logging.error("Token inválido!")
        raise HTTPException(status_code=401, detail="Token inválido!")
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (payload["email"],))
    email = descriptografar_email(payload["email"])
    usuario = cursor.fetchone()
    if (payload["email"] is not None):
        if usuario is not None:
            cursor.execute("UPDATE usuarios SET nome = %s WHERE email = %s", (dados.nome, payload["email"]))
        if dados.senha is not None:
            nova_senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (nova_senha, payload["email"]))
            if dados.email is not None and dados.email != payload["email"]:
                novo_email = criptografar_email(dados.email)
                cursor.execute("UPDATE usuarios SET email = %s WHERE email = %s", (novo_email, payload["email"]))
                conexao.commit()
            logging.info(f"Dados do usuário {payload['email']} alterados com sucesso.")
            return {"mensagem": "Perfil alterado com sucesso!"}
        else:
            logging.info(f"Credenciais do usuario inválidas ou vazias,")
            raise HTTPException(status_code=409, detail="Credenciais inválidas ou vazias!")
    else:
        logging.info(f"Email {dados.email} já está em uso por outro usuário.")
        raise HTTPException(status_code=409, detail="Email já está em uso!")


@app.patch("/admin/usuario")
def alterar_senha(dados: UsuarioSenha, credenciais=Depends(HTTPBearer())):
    cursor = conexao.cursor(dictionary=True)
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logging.error("Token expirado!")
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        logging.error("Token inválido!")
        raise HTTPException(status_code=401, detail="Token inválido!")
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (dados.email,))
    usuario = cursor.fetchone()
    conexao.commit()
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        logging.info("Usuário root autenticado com sucesso.")
        if usuario is not None:
            if bcrypt.checkpw(dados.senha.encode('utf-8'), usuario["senha"].encode('utf-8')):
                logging.error(f"A nova senha do usuário {dados.email} é igual à anterior.")
                raise HTTPException(status_code=409, detail="Essa senha é igual a anterior!")
            else:
                nova_senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
                cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (nova_senha, dados.email))
                conexao.commit()
                logging.info(
                    f"Senha do usuário {dados.email} alterada com sucesso "
                    f"por {payload['email']}."
                )
                return {"mensagem": "Senha de usuário alterada!"}
        else:
            logging.error(f"Usuário {dados.email} não encontrado para alteração de senha.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        if payload["papel"] == "admin":
            if usuario is not None:
                if bcrypt.checkpw(dados.senha.encode('utf-8'), usuario["senha"].encode('utf-8')):
                    logging.error(f"A nova senha do usuário {dados.email} é igual à anterior.")
                    raise HTTPException(status_code=409, detail="Essa senha é igual a anterior!")
                else:
                    nova_senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt())
                    cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (nova_senha, dados.email))
                    conexao.commit()
                    logging.info(
                        f"Senha do usuário {dados.email} alterada com sucesso "
                        f"por {payload['email']}."
                    )
                    return {"mensagem": "Senha de usuário alterada!"}
            else:
                logging.error(f"Usuário {dados.email} não encontrado para alteração de senha.")
                raise HTTPException(status_code=404, detail="Usuário não encontrado!")
        else:
            logging.error(f"Usuário {payload['email']} não é administrador")
            raise HTTPException(
                status_code=403, detail="Acesso negado! Usuário não é administrador."
            )


@app.patch("/perfil/desativar")
def desativar_perfil_proprio(credenciais=Depends(HTTPBearer())):
    cursor = conexao.cursor(dictionary=True)
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logging.error("Token expirado!")
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        logging.error("Token inválido!")
        raise HTTPException(status_code=401, detail="Token inválido!")
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (payload["email"],))
    usuario = cursor.fetchone()
    if usuario is not None:
        cursor.execute("UPDATE usuarios SET ativo = %s WHERE email = %s",(False, payload["email"],))
        conexao.commit()
        logging.info(f"Usuário {payload['email']} desativado com sucesso.")
        return {"mensagem": "Usuário desativado com sucesso!"}
    else:
        logging.error(f"Usuário {payload['email']} não encontrado para desativação.")
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")


@app.get("/perfil")
def perfil(credenciais=Depends(HTTPBearer())):
    logging.info("Acessando o perfil do usuário...")
    cursor = conexao.cursor(dictionary=True)
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (payload["email"],))
        usuario = cursor.fetchone()
        conexao.commit()
        logging.info(f"Perfil do usuário {payload['email']} acessado com sucesso!")
        return {"nome": usuario["nome"], "email": payload["email"]}
    except jwt.ExpiredSignatureError:
        logging.error("Token expirado!")
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        logging.error("Token inválido!")
        raise HTTPException(status_code=401, detail="Token inválido!")
    
