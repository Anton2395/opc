import psycopg2


def create_connection():
    conn = psycopg2.connect(dbname='postgres', user='mvlab', password='z1x2c3', host='10.0.0.3', port=5432)
    cursor = conn.cursor()
    return conn, cursor
