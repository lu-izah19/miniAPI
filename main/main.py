import logging
import datetime
import bcrypt
import jwt
import mysql.connector
from fastapi import Depends, FastAPI, HTTPException
from auth import criptografar_email, descriptografar_email
from auth import validar_usuario, buscar_usuario_por_email

from config import SECRET_KEY, EMAIL_ROOT, SENHA_ROOT
from database import conexao
from models import (
    UsuarioCadastro,
    UsuarioLogin,
    AlterarPapel,
    UsuarioDelete,
    UsuarioSenha,
    UsuarioAlterarPerfil,
)

app = FastAPI()

logging.basicConfig(level=logging.INFO)


@app.get("/")
def home():
    logging.info("Acessando a rota raiz da API...")
    return {"message": "Bem-vindo à API!"}


@app.post("/usuario")
def cadastro(dados: UsuarioCadastro):
    try:
        cursor = conexao.cursor(dictionary=True)
        email = criptografar_email(dados.email)
        senha_hash = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO usuarios (email, nome, senha, papel) VALUES(%s, %s, %s, 'user')",
            (email, dados.nome, senha_hash))
        conexao.commit()
        logging.info(f"Usuário cadastrado com sucesso: {email}")
        return {"mensagem": "Cadastro realizado com sucesso!"}
    except mysql.connector.errors.IntegrityError:
        logging.info(f"Esse email ja está sendo utilizado por outro usuário!")
        raise HTTPException(status_code=409, detail="Email já está em uso!")


@app.post("/login")
def login(dados: UsuarioLogin):
    usuario = buscar_usuario_por_email(dados.email)
    if EMAIL_ROOT == dados.email and SENHA_ROOT == dados.senha:
        jtoken = jwt.encode({"email": dados.email, "papel": "root",
                            "exp": datetime.datetime.now(datetime.timezone.utc)
                            + datetime.timedelta(minutes=30)},
                            SECRET_KEY, algorithm="HS256")
        logging.info("Usuário root autenticado com sucesso.")
        return {"token": jtoken}
    else:
        if usuario is not None:
            if bcrypt.checkpw(dados.senha.encode('utf-8'), usuario['senha'].encode('utf-8')):
                jtoken = jwt.encode({"email": dados.email,
                                    "papel": usuario['papel'],
                                    "exp": datetime.datetime.now(datetime.timezone.utc)
                                    + datetime.timedelta(minutes=30)},
                                    SECRET_KEY, algorithm="HS256")
                logging.info(f"Login realizado com sucesso para o email {dados.email}.")
                return {"mensagem": "Login realizado com sucesso!", "token": jtoken}
            else:
                logging.error(f"Senha incorreta para o email {dados.email}.")
                raise HTTPException(status_code=401, detail="Senha incorreta!")
        else:
            logging.error(f"Email {dados.email} não encontrado no cadastro.")
            raise HTTPException(status_code=404, detail="Email incorreto!")


@app.get("/admin")
def admin(payload=Depends(validar_usuario)):
    logging.info("Acessando a rota de administração...")
    cursor = conexao.cursor(dictionary=True)
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        logging.info("Usuário root autenticado com sucesso.")
        cursor.execute("SELECT * FROM usuarios")
        todos_usuarios = cursor.fetchall()
        lista_usuarios = []
        for linha in todos_usuarios:
            lista_usuarios.append({
                "nome": linha["nome"],
                "email": descriptografar_email(linha["email"])
            })
        logging.info(f"Usuário {payload['email']} acessou a lista de usuários cadastrados.")
        return{"usuarios": lista_usuarios}
    else:
        usuario = buscar_usuario_por_email(payload["email"])
        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
        if usuario["papel"]== "admin":
            cursor.execute("SELECT * FROM usuarios")
            todos_usuarios = cursor.fetchall()
            lista_usuarios = []
            for linha in todos_usuarios:
                lista_usuarios.append({
                    "nome": linha["nome"],
                    "email": descriptografar_email(linha["email"])
                })
            logging.info(f"Usuário {payload['email']} acessou a lista de usuários cadastrados.")
            return{"usuarios": lista_usuarios}
        else:
            logging.error(f"Usuário {payload['email']} não é administrador")
            raise HTTPException(status_code=403,
                                detail="Acesso negado! Usuário não é administrador.")


@app.patch("/admin/papel")
def alterar_papel(dados: AlterarPapel, payload=Depends(validar_usuario)):
    cursor = conexao.cursor(dictionary=True)
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        logging.info("Usuário root autenticado com sucesso.")
        usuario = buscar_usuario_por_email(dados.email)
        if usuario is not None:
            cursor.execute("UPDATE usuarios SET papel = %s WHERE email = %s", (dados.papel, usuario["email"]))
            conexao.commit()
            logging.info(
                f"Papel do usuário {dados.email} alterado por "
                f"{payload['email']} para {dados.papel}."
            )
            return {"mensagem": "Papel de usuário alterado!", "papel": dados.papel}
        else:
            logging.error(f"Usuário {dados.email} não encontrado para alteração de papel.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        usuario = buscar_usuario_por_email(dados.email)
        if payload["papel"] == "admin":
            if usuario is not None:
                cursor.execute("UPDATE usuarios SET papel = %s WHERE email = %s", (dados.papel, usuario["email"]))
                conexao.commit()
                logging.info(
                    f"Papel do usuário {dados.email} alterado por "
                    f"{payload['email']} para {dados.papel}."
                )
                return {"mensagem": "Papel de usuário alterado!", "papel": dados.papel}
            else:
                logging.error(f"Usuário {dados.email} não encontrado para alteração de papel.")
                raise HTTPException(status_code=404, detail="Usuário não encontrado!")
        else:
            logging.error(f"Usuário {payload['email']} não é administrador")
            raise HTTPException(
                status_code=403, detail="Acesso negado! Usuário não é administrador."
            )


@app.delete("/admin/usuario")
def deletar_perfil_usuario(dados: UsuarioDelete, payload=Depends(validar_usuario)):
    cursor = conexao.cursor(dictionary=True)
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        logging.info("Usuário root autenticado com sucesso.")
        usuario = buscar_usuario_por_email(dados.email)
        if usuario is not None:
            cursor.execute("DELETE FROM usuarios WHERE email = %s", (usuario["email"],))
            conexao.commit()
            logging.info(f"Usuário {dados.email} deletado com sucesso por {payload['email']}.")
            return {"mensagem": "Usuário deletado com sucesso!"}
        else:
            logging.error(f"Usuário {dados.email} não encontrado.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado!")
    else:
        if payload["papel"] == "admin":
            usuario = buscar_usuario_por_email(dados.email)
            if usuario is not None:
                cursor.execute("DELETE FROM usuarios WHERE email = %s", (usuario["email"],))
                conexao.commit()
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
def alterar_perfil(dados: UsuarioAlterarPerfil, payload=Depends(validar_usuario)):
    cursor = conexao.cursor(dictionary=True)
    if (payload["email"] is not None):
        usuario = buscar_usuario_por_email(payload["email"])
        if usuario is not None:
            if dados.nome is not None:
                cursor.execute("UPDATE usuarios SET nome = %s WHERE email = %s", (dados.nome, usuario["email"]))
                conexao.commit()
                logging.info(f"Nome do usuário {payload['email']} alterado com sucesso.")
                return {"mensagem": "Perfil alterado com sucesso!"}
            if dados.senha is not None:
                nova_senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt().decode('utf-8'))
                cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (nova_senha, usuario["email"]))
                conexao.commit()
                logging.info(f"Senha do usuário {payload['email']} alterada com sucesso.")
                return {"mensagem": "Perfil alterado com sucesso!"}
            if dados.email is not None:
                usuario_novo = buscar_usuario_por_email(dados.email)
                if usuario_novo is not None:
                    if dados.email != usuario_novo["email"] and dados.email != payload["email"]:
                        logging.info(f"Email {dados.email} já está em uso por outro usuário.")
                        raise HTTPException(status_code=409, detail="Email já está em uso!")
                    else:
                        return {"mensagem": "Perfil alterado com sucesso!"}
                else:
                    novo_email = criptografar_email(dados.email)
                    cursor.execute("UPDATE usuarios SET email = %s WHERE email = %s", (novo_email, usuario["email"]))
                    conexao.commit()
                    logging.info(f"Email do usuário {payload['email']} alterado com sucesso.")
                    return {"mensagem": "Perfil alterado com sucesso!"}
    else:
        logging.info(f"Credenciais do usuario inválidas ou vazias,")
        raise HTTPException(status_code=409, detail="Credenciais inválidas ou vazias!")


@app.patch("/admin/usuario")
def alterar_senha(dados: UsuarioSenha, payload=Depends(validar_usuario)):
    cursor = conexao.cursor(dictionary=True)
    if EMAIL_ROOT == payload["email"] and payload["papel"] == "root":
        logging.info("Usuário root autenticado com sucesso.")
        usuario = buscar_usuario_por_email(dados.email)
        if usuario is not None:
            if bcrypt.checkpw(dados.senha.encode('utf-8'), usuario["senha"].encode('utf-8')):
                logging.error(f"A nova senha do usuário {dados.email} é igual à anterior.")
                raise HTTPException(status_code=409, detail="Essa senha é igual a anterior!")
            else:
                nova_senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt().decode('utf-8'))
                cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (nova_senha, usuario["email"]))
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
        usuario = buscar_usuario_por_email(dados.email)
        if payload["papel"] == "admin":
            if usuario is not None:
                if bcrypt.checkpw(dados.senha.encode('utf-8'), usuario["senha"].encode('utf-8')):
                    logging.error(f"A nova senha do usuário {dados.email} é igual à anterior.")
                    raise HTTPException(status_code=409, detail="Essa senha é igual a anterior!")
                else:
                    nova_senha = bcrypt.hashpw(dados.senha.encode('utf-8'), bcrypt.gensalt().decode('utf-8'))
                    cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (nova_senha, usuario["email"]))
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
def desativar_perfil_proprio(payload=Depends(validar_usuario)):
    cursor = conexao.cursor(dictionary=True)
    usuario = buscar_usuario_por_email(payload["email"])
    if usuario is not None:
        cursor.execute("UPDATE usuarios SET ativo = %s WHERE email = %s",(False, usuario["email"],))
        conexao.commit()
        logging.info(f"Usuário {payload['email']} desativado com sucesso.")
        return {"mensagem": "Usuário desativado com sucesso!"}
    else:
        logging.error(f"Usuário {payload['email']} não encontrado para desativação.")
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")


@app.get("/perfil")
def perfil(payload=Depends(validar_usuario)):
    logging.info("Acessando o perfil do usuário...")
    usuario = buscar_usuario_por_email(payload["email"])
    if usuario is not None:
        logging.info(f"Perfil do usuário {payload['email']} acessado com sucesso!")
        return {"nome": usuario["nome"], "email": payload["email"]}
    else:
        logging.error("Usuário não encontrado!")
        raise HTTPException(status_code=404, detail="Usuário não encontrado!")
