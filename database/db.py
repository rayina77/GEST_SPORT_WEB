import os
import sqlite3
import psycopg2

# =====================================================
# CONFIGURATION
# =====================================================

DB_PATH = "database/sport.db"

DATABASE_URL = os.getenv("DATABASE_URL")

# =====================================================
# LIGNE COMPATIBLE SQLITE
# =====================================================

class RowAdapter:
    """
    Compatible avec sqlite3.Row.

    Fonctionne avec :

        row[0]
        row["nom"]

    exactement comme SQLite.
    """

    def __init__(self, columns, values):
        self._columns = list(columns)
        self._values = tuple(values)

    def __getitem__(self, key):

        if isinstance(key, int):
            return self._values[key]

        if isinstance(key, str):
            return self._values[self._columns.index(key)]

        raise KeyError(key)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def keys(self):
        return self._columns

    def values(self):
        return self._values

    def items(self):
        return zip(self._columns, self._values)

    def get(self, key, default=None):
        try:
            return self[key]
        except Exception:
            return default

    def __repr__(self):
        return str(dict(zip(self._columns, self._values)))


# =====================================================
# CURSEUR POSTGRES
# =====================================================

class CursorAdapter:

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):

        query = query.replace("?", "%s")

        self.cursor.execute(query, params or ())

        return self

    def executemany(self, query, seq):

        query = query.replace("?", "%s")

        self.cursor.executemany(query, seq)

        return self

    def fetchone(self):

        row = self.cursor.fetchone()

        if row is None:
            return None

        columns = [c[0] for c in self.cursor.description]

        return RowAdapter(columns, row)

    def fetchall(self):

        rows = self.cursor.fetchall()

        columns = [c[0] for c in self.cursor.description]

        return [
            RowAdapter(columns, r)
            for r in rows
        ]

    def fetchmany(self, size=None):

        rows = self.cursor.fetchmany(size)

        columns = [c[0] for c in self.cursor.description]

        return [
            RowAdapter(columns, r)
            for r in rows
        ]

    def __getattr__(self, name):
        return getattr(self.cursor, name)


# =====================================================
# CONNEXION POSTGRES
# =====================================================

class PostgresConnection:

    def __init__(self, conn):
        self.conn = conn

    def cursor(self):

        return CursorAdapter(
            self.conn.cursor()
        )

    def execute(self, query, params=None):

        cur = self.cursor()

        return cur.execute(query, params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __getattr__(self, name):
        return getattr(self.conn, name)


# =====================================================
# CONNEXION
# =====================================================

def get_connection():

    # ---------------- PostgreSQL ----------------

    if DATABASE_URL:

        conn = psycopg2.connect(DATABASE_URL)

        return PostgresConnection(conn)

    # ---------------- SQLite ----------------

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn