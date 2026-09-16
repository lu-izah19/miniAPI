import mysql.connector
from config import MARIADB_HOST,MARIADB_PORT, MARIADB_USER, MARIADB_PASSWORD, MARIADB_DATABASE

conexao = mysql.connector.connect(
    host=MARIADB_HOST,
    port=MARIADB_PORT,
    user=MARIADB_USER,
    password=MARIADB_PASSWORD,
    database=MARIADB_DATABASE
)
