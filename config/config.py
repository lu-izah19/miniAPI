import os
from dotenv import load_dotenv

load_dotenv()

USUARIO_ROOT = os.environ.get("USUARIO_ROOT")
SENHA_ROOT = os.environ.get("SENHA_ROOT")
EMAIL_ROOT = os.environ.get("EMAIL_ROOT")
SECRET_KEY = os.environ.get("SECRET_KEY")
FERNET_KEY = os.environ.get("FERNET_KEY")

MARIADB_USER = os.environ.get("MARIADB_USER")
MARIADB_PASSWORD = os.environ.get("MARIADB_PASSWORD")
MARIADB_DATABASE = os.environ.get("MARIADB_DATABASE")