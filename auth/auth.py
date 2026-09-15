import logging
from cryptography.fernet import Fernet
from config import FERNET_KEY

fernet = Fernet(FERNET_KEY)


def criptografar_email(email):
    logging.info(f"Criptografando email: {email}")
    return fernet.encrypt(email.encode('utf-8')).decode('utf-8')


def descriptografar_email(email):
    logging.info(f"Descriptografando email: {email}")
    return fernet.decrypt(email.encode('utf-8')).decode('utf-8')