import mysql.connector
from config import MARIADB_USER, MARIADB_PASSWORD, MARIADB_DATABASE

conexao = mysql.connector.connect(
    host="137.131.133.237",
    user=MARIADB_USER,
    password=MARIADB_PASSWORD,
    database=MARIADB_DATABASE
)