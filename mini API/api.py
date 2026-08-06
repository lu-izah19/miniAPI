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

# Classe que guarda os dados do usuário atual (nome, email, senha) em memória
# Substitui o antigo dicionário "usuario" usado na versão de terminal
class Usuario:
    # Construtor: todos os campos são opcionais para permitir criar o objeto
    # em etapas (primeiro só com nome, depois só com email/senha)
    def __init__(self, nome=None, email=None, senha=None):
        self.nome = nome
        self.email = email
        self.senha = senha

# Rota GET que dispara o fluxo principal do "menu" via terminal
# (nome na URL não é usado dentro da função, é só o path da rota)
@app.get("/usuario/{nome}")
# Função principal que controla o fluxo do programa via terminal
def inicio():
    # Pede o nome do usuário
    nome = input("Digite seu nome: ")
    # Cria uma instância da classe Usuario com o nome fornecido
    usuario = Usuario(nome=nome)
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


# Rota POST que recebe email e senha para cadastro
@app.post("/usuario/{email}/{senha}")
# Função responsável por cadastrar o email e a senha do usuário
def cadastro():
    # Pede o email do usuário
    email = input("Digite seu email: ")
    # Pede a senha do usuário
    senha = input("Digite sua senha: ")
    # Declara que "usuario" aqui se refere à variável global, não a uma nova local
    global usuario
    # Atenção: cria um Usuario NOVO (sem nome), sobrescrevendo o objeto criado em inicio()
    # e perdendo o nome salvo anteriormente
    usuario = Usuario(email=email, senha=senha)
    # Retorna uma confirmação de cadastro 
    return {"mensagem": "Cadastro realizado com sucesso!"}

# Rota GET para autenticação (reutiliza o mesmo path "/usuario/{email}/{senha}" do cadastro, mas em outro método HTTP)
@app.get("/usuario/{email}/{senha}")
# Função responsável por autenticar o usuário já cadastrado
def login():
    # Pede o email para login
    email_login = input("Digite seu email para login: ")
    # Pede a senha para login
    senha_login = input("Digite sua senha para login: ")
    # Declara que "usuario" aqui se refere à variável global, não a uma nova local
    global usuario
    # Compara os dados digitados com os dados salvos no objeto usuario
    if email_login == usuario.email and senha_login == usuario.senha:
        # Se os dados baterem, loga sucesso no login
        logging.info("Login realizado com sucesso!")
    else:
        logging.warning("Credenciais inválidas!")

# Rota GET para exibir o perfil do usuário
@app.get("/usuario/{nome}/{email}")
# Função que exibe os dados do perfil do usuário logado
def perfil():
    # Declara que "usuario" aqui se refere à variável global, não a uma nova local
    global usuario
    # Loga que está acessando o perfil
    logging.info("Acessando o perfil do usuário...")
    # Exibe o nome salvo do usuário
    logging.info("nome: %s", usuario.nome)
    # Exibe o email salvo do usuário
    logging.info("Email: %s", usuario.email)
    # Informa como sair da tela de perfil (mas nada aqui realmente sai, é só uma instrução)
    logging.info("Para sair do perfil, digite 4.")

# Chama a função inicio() para começar a execução do programa assim que o arquivo é executado
inicio()