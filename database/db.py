import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="abcd@1234",
        database="ai_cctv"
    )