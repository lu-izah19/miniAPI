import logging
from cryptography.fernet import Fernet
from config import FERNET_KEY, SECRET_KEY
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

fernet = Fernet(FERNET_KEY)


def criptografar_email(email):
    logging.info(f"Criptografando email: {email}")
    return fernet.encrypt(email.encode('utf-8')).decode('utf-8')


def descriptografar_email(email):
    logging.info(f"Descriptografando email: {email}")
    return fernet.decrypt(email.encode('utf-8')).decode('utf-8')


def validar_usuario(credenciais=Depends(HTTPBearer())):
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logging.error("Token expirado!")
        raise HTTPException(status_code=401, detail="Token expirado!")
    except jwt.InvalidTokenError:
        logging.error("Token inválido!")
        raise HTTPException(status_code=401, detail="Token inválido!")

def buscar_usuario_por_email(email: str):
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    todos_usuarios = cursor.fetchall()
    usuario = None
    for linha in todos_usuarios:
        if descriptografar_email(linha["email"]) == email:
            usuario = linha
            break
    return usuario
