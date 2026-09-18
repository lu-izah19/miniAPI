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
