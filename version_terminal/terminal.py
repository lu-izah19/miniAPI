from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Bem-vindo à API!"}

menu = """
1. Cadastro
2. Login
3. Perfil
4.Sair
"""

usuario = {}

def inicio():
    nome = input("Digite seu nome: ")
    usuario["nome"] = nome
    logging.info("Olá %s, seja bem vindo(a)!", nome)
    while True:
        print(menu)
        opcao = input("Escolha uma opção: ")
        if opcao == "1":
            cadastro()
        elif opcao == "2":
            login()
        elif opcao == "3":
            perfil()
        elif opcao == "4":
            logging.info("Saindo da API...")
            break
        else:
            logging.warning("Opção inválida!")


def cadastro():
    email = input("Digite seu email: ")
    senha = input("Digite sua senha: ")
    usuario["email"] = email
    usuario["senha"] = senha
    return {"mensagem": "Cadastro realizado com sucesso!"}

def login():
    email_login = input("Digite seu email para login: ")
    senha_login = input("Digite sua senha para login: ")
    if email_login == usuario.get("email") and senha_login == usuario.get("senha"):
        logging.info("Login realizado com sucesso!")
    else:
        logging.warning("Credenciais inválidas!")

def perfil():
    logging.info("Acessando o perfil do usuário...")
    logging.info("nome: %s", usuario.get("nome"))
    logging.info("Email: %s", usuario.get("email"))
    logging.info("Para sair do perfil, digite 4.")

inicio()