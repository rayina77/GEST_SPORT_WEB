import os
import sqlite3
import psycopg2
import psycopg2.extras

# =====================================================
# CONFIGURATION
# =====================================================

DB_PATH = "database/sport.db"

DATABASE_URL = os.getenv("DATABASE_URL")

# =====================================================
# WRAPPER PostgreSQL
# =====================================================

class PostgresConnection:

    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        """
        Rend les requêtes SQLite compatibles PostgreSQL
        en remplaçant ? par %s.
        """

        cursor = self.conn.cursor()

        query = query.replace("?", "%s")

        cursor.execute(query, params or ())

        return cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


# =====================================================
# CONNEXION
# =====================================================

def get_connection():

    # ---------- PostgreSQL ----------
    if DATABASE_URL:

        conn = psycopg2.connect(DATABASE_URL)

        return PostgresConnection(conn)

    # ---------- SQLite ----------
    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn