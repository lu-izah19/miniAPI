from fastapi.testclient import TestClient
from main.main import app
from database.database import conexao
from auth.auth import descriptografar_email

client = TestClient(app)


def limpar_cadastro(email):
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    todos_usuarios = cursor.fetchall()
    usuario = None
    for linha in todos_usuarios:
        if descriptografar_email(linha["email"]) == email:
            usuario = linha
            break
    if usuario is not None:
        cursor.execute("DELETE FROM usuarios WHERE email = %s", (usuario["email"],))
        conexao.commit()
        cursor.close()


def cadastrar(nome, email, senha):
    return client.post("/usuario", json={"nome": nome, "email": email, "senha": senha})


def logar(email, senha):
    return client.post("/login", json={"email": email, "senha": senha})


def cabecalho(token):
    return {"Authorization": f"Bearer {token}"}
