# Importa a classe FastAPI para criar a aplicação web (embora não esteja sendo usada nas rotas ainda)
from fastapi import FastAPI
# Importa o módulo logging para exibir mensagens de status/erro formatadas
import logging

# Configura o sistema de logging para exibir mensagens de nível INFO ou superior
logging.basicConfig(level=logging.INFO)

# Cria a instância da aplicação FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Bem-vindo à API!"}

# Texto do menu que será exibido para o usuário no terminal
menu = """
1. Cadastro
2. Login
3. Perfil
4.Sair
"""

# Dicionário em memória que guarda os dados do usuário atual (nome, email, senha)
usuario = {}

# Função principal que controla o fluxo do programa via terminal
def inicio():
    # Pede o nome do usuário
    nome = input("Digite seu nome: ")
    # Salva o nome no dicionário do usuário
    usuario["nome"] = nome
    # Loga uma mensagem de boas-vindas personalizada
    logging.info("Olá %s, seja bem vindo(a)!", nome)
    # Loop infinito que mantém o menu ativo até o usuário escolher sair
    while True:
        # Exibe o menu de opções
        print(menu)
        # Lê a opção escolhida pelo usuário
        opcao = input("Escolha uma opção: ")
        # Se a opção for "1", chama a função de cadastro
        if opcao == "1":
            cadastro()
        # Se a opção for "2", chama a função de login
        elif opcao == "2":
            login()
        # Se a opção for "3", chama a função de perfil
        elif opcao == "3":
            perfil()
        # Se a opção for "4", loga a saída e interrompe o loop (encerra o programa)
        elif opcao == "4":
            logging.info("Saindo da API...")
            break
        # Para qualquer outra entrada, avisa que a opção é inválida e repete o menu
        else:
            logging.warning("Opção inválida!")


# Função responsável por cadastrar o email e a senha do usuário
def cadastro():
    # Pede o email do usuário
    email = input("Digite seu email: ")
    # Pede a senha do usuário
    senha = input("Digite sua senha: ")
    # Salva o email no dicionário do usuário
    usuario["email"] = email
    # Salva a senha no dicionário do usuário
    usuario["senha"] = senha
    # Retorna uma confirmação de cadastro 
    return {"mensagem": "Cadastro realizado com sucesso!"}

# Função responsável por autenticar o usuário já cadastrado
def login():
    # Pede o email para login
    email_login = input("Digite seu email para login: ")
    # Pede a senha para login
    senha_login = input("Digite sua senha para login: ")
    # Compara os dados digitados com os dados salvos no dicionário usuario
    if email_login == usuario.get("email") and senha_login == usuario.get("senha"):
        # Se os dados baterem, loga sucesso no login
        logging.info("Login realizado com sucesso!")
    else:
        # Se os dados não baterem, loga um aviso de credenciais inválidas
        logging.warning("Credenciais inválidas!")

# Função que exibe os dados do perfil do usuário logado
def perfil():
    # Loga que está acessando o perfil
    logging.info("Acessando o perfil do usuário...")
    # Exibe o nome salvo do usuário
    logging.info("nome: %s", usuario.get("nome"))
    # Exibe o email salvo do usuário
    logging.info("Email: %s", usuario.get("email"))
    # Informa como sair da tela de perfil (mas nada aqui realmente sai, é só uma instrução)
    logging.info("Para sair do perfil, digite 4.")

# Chama a função inicio() para começar a execução do programa assim que o arquivo é executado
inicio()