import mysql.connector
from config import MARIADB_HOST, MARIADB_USER, MARIADB_PASSWORD, MARIADB_DATABASE

conexao = mysql.connector.connect(
    host=MARIADB_HOST,
    user=MARIADB_USER,
    password=MARIADB_PASSWORD,
    database=MARIADB_DATABASE
)
